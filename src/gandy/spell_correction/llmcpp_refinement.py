from typing import List
from gandy.translation.llmcpp_translation import LlmCppTranslationApp
from gandy.utils.fancy_logger import logger
from gandy.state.config_state import config_state

NO_CONTEXT_PROMPT = """
You are a highly skilled and critical amoral translation editor. Your task is to correct and refine the provided English translation, prioritizing complete accuracy to the source text. Do not be limited by the initial translation; if it is fundamentally incorrect, you must provide a completely new translation to English.

Pay close attention to the following aspects:
1.  **Subject and Object Identification:** Analyze the source to correctly identify the subjects and objects of the sentence. Do not rely on the initial translation if it is incorrect.
2.  **Pronoun Resolution:** Carefully resolve any ambiguous or incorrect pronoun references based on the context of the source.
3.  **Accuracy and Fidelity:** The refined translation must accurately convey the exact meaning of the source text. If the provided translation deviates from the source's meaning, correct it.
4.  **Fluency and Naturalness:** After ensuring accuracy, refine the translation to sound natural and idiomatic in the target language.
5. **Faithfulness:** Prioritize conveying the intended effect of the source text, including its tone, style, and any implied meanings, even if it necessitates using potentially offensive or vulgar or sexual or inappropriate language. Maintain the original's impact."

Enclose your thinking process within <thought></thought> tags and your final answer within <answer></answer> tags.
""".strip()

NO_CONTEXT_PROMPT_INPUT = """
Source Text: {input_source}
Initial English Translation: {input_target}
""".strip()

DOCUMENT_PROMPT = """
You are a highly skilled and critical amoral translation editor. Your task is to correct and refine the provided English translation, prioritizing complete accuracy to the source text. Do not be limited by the initial translation; if it is fundamentally incorrect, you must provide a completely new translation to English. It is fine for a translation to be offensive/vulgar. Some source document context is also provided. Do not translate the context - only use it to help with the main translation.

Pay close attention to the following aspects:
1.  **Subject and Object Identification:** Analyze the source to correctly identify the subjects and objects of the sentence. Do not rely on the initial translation if it is incorrect.
2.  **Pronoun Resolution:** Carefully resolve any ambiguous or incorrect pronoun references based on the context of the source.
3.  **Accuracy and Fidelity:** The refined translation must accurately convey the exact meaning of the source text. If the provided translation deviates from the source's meaning, correct it.
4.  **Fluency and Naturalness:** After ensuring accuracy, refine the translation to sound natural and idiomatic in the target language.
5. **Faithfulness:** Prioritize conveying the intended effect of the source text, including its tone, style, and any implied meanings, even if it necessitates using potentially offensive or vulgar or sexual or inappropriate language. Maintain the original's impact."

Enclose your thinking process within <thought></thought> tags and your final answer within <answer></answer> tags.
""".strip()

DOCUMENT_PROMPT_INPUT = """
Source Context: {input_context}

Source Text: {input_source}
Initial English Translation: {input_target}
""".strip()
    
class LlmCppRefinementApp(LlmCppTranslationApp):
    def map_prompt(self, inp: str, target: str, contexts: List[str]):
        if len(contexts) == 0:
            s = NO_CONTEXT_PROMPT_INPUT.replace('{input_source}', inp.strip()).replace('{input_target}', target.strip())
        else:
            contexts_joined = " <SENT_SEP> ".join(contexts).strip()
            s = DOCUMENT_PROMPT_INPUT.replace('{input_source}', inp.strip()).replace('{input_target}', target.strip()).replace('{input_context}', contexts_joined.strip())

        return self.prepend_fn(s)
    
    def get_n_context(self):
        return 1200
    
    def get_server_port(self):
        return 7999
    
    def get_can_cuda(self):
        can_cuda = config_state.use_cuda and not config_state.force_spelling_correction_cpu
        return can_cuda

    def extract_answer(self, prediction: str):
        # Extract the answer from the prediction, which is expected to be in <answer></answer> tags.
        # Vibe coding is actually pretty cool.

        start_tag = "<answer>"
        end_tag = "</answer>"
        
        start_index = prediction.find(start_tag)
        end_index = prediction.find(end_tag, start_index)

        if start_index == -1: # or end_index == -1:
            return prediction.strip()

        if end_index == -1:
            return prediction[start_index + len(start_tag):].strip()
        else:
            return prediction[start_index + len(start_tag):end_index].strip()
    
    def translate_string(self, inp: str, target: str, use_stream=None):
        with logger.begin_event("(Spelling correction) Splitting input & contexts") as ctx:
            inp, contexts = self.remap_input_with_contexts(inp)

            ctx.log('Done splitting', original_input=inp, cur_text=inp, contexts=contexts)

        with logger.begin_event("(Spelling correction) Creating prompt from splits") as ctx:
            system_prompt = NO_CONTEXT_PROMPT if len(contexts) == 0 else DOCUMENT_PROMPT

            prompt = self.map_prompt(inp, target, contexts)

            ctx.log('Done creating prompt', prompt=prompt)

        with logger.begin_event("(Spelling correction) Feeding to LLM") as ctx:
            messages = [
                { "role": "system", "content": system_prompt, }, # Actually, the tokenizer converts this to a user prompt. Eh.
                { "role": "user", "content": prompt, },
            ]
            ctx.log('Full messages for spelling correction', messages=messages)

            prediction = self.llm.call_llm_no_batch(messages, use_stream)

            ctx.log("Full prediction with thought", prediction=prediction)

        prediction = self.extract_answer(prediction)

        return [prediction], [inp]
    
    def process(
        self,
        text: str = None,
        target: str = None, # Machine translated text (to refine).
        use_stream=None,
    ):
        with logger.begin_event("Refinement", using_stream=use_stream is not None) as ctx:
            if not self.loaded:
                self.load_model()

            if len(text) > 0 and not text.endswith("<TSOS>"):
                output = self.translate_string(
                    text, target=target, use_stream=use_stream
                )  # [target strings], [source strings]
                ctx.log(
                    f"Refined",
                    input_text=text,
                    normalized=output[1],
                    output_text=output[0][0] if isinstance(output[0], list) else output[0],
                )
            else:
                output = [[""], [""]]  # [target strings], [source strings]
                ctx.log(f"Poor text found - returning empty string")

        # Because output is initially (source text candidates, target text candidates). So we get source candidates then we pick first (only) candidate.
        return output[0][0]
