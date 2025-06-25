from typing import List
from gandy.translation.llmcpp_translation import LlmCppTranslationApp
from gandy.utils.fancy_logger import logger

NO_CONTEXT_PROMPT = """
Refine the provided translation. Pay close attention to the following aspects:
1. Subject-Verb Agreement: Ensure subjects and verbs align correctly.
2. Pronoun Resolution: Correct any ambiguous or incorrect pronoun usage.
3. Fluency and Naturalness: Make the translation sound natural and idiomatic in the target language.
4. Accuracy: Ensure the refined translation accurately conveys the meaning of the source.

Source Text: {input_source}
Translation to Refine: {input_target}
""".strip()

DOCUMENT_PROMPT = """
Refine the provided translation, considering the given context as needed. Pay close attention to the following aspects:
1. Subject-Verb Agreement: Ensure subjects and verbs align correctly.
2. Pronoun Resolution: Correct any ambiguous or incorrect pronoun usage.
3. Fluency and Naturalness: Make the translation sound natural and idiomatic in the target language.
4. Accuracy: Ensure the refined translation accurately conveys the meaning of the source.

Context: {input_context}

Source Text: {input_source}
Translation to Refine: {input_target}
""".strip()
    
class LlmCppRefinementApp(LlmCppTranslationApp):
    def map_prompt(self, inp: str, target: str, contexts: List[str]):
        if len(contexts) == 0:
            s = NO_CONTEXT_PROMPT.replace('{input_source}', inp.strip()).replace('{input_target}', target.strip())
        else:
            contexts_joined = " <SENT_SEP> ".join(contexts).strip()
            s = DOCUMENT_PROMPT.replace('{input_source}', inp.strip()).replace('{input_target}', target.strip()).replace('{input_context}', contexts_joined.strip())

        return self.prepend_fn(s)
    
    def translate_string(self, inp: str, target: str, use_stream=None):
        with logger.begin_event("Splitting input & contexts") as ctx:
            inp, contexts = self.remap_input_with_contexts(inp)

            ctx.log('Done splitting', original_input=inp, cur_text=inp, contexts=contexts)

        with logger.begin_event("Creating prompt from splits") as ctx:
            prompt = self.map_prompt(inp, target, contexts)

            ctx.log('Done creating prompt', prompt=prompt)

        with logger.begin_event("Feeding to LLM") as ctx:
            messages = [{ "role": "user", "content": prompt, }, { "role": "assistant", "content": "Here\'s a refined translation:\n\n"}]
            prediction = self.call_llm(messages, use_stream)

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
