from gandy.translation.base_translation import BaseTranslation
from gandy.translation.llama_server_wrapper import LlamaCppExecutableOpenAIClient
from gandy.utils.fancy_logger import logger
from gandy.state.config_state import config_state
from typing import List
import os

try:
    import torch
except:
    pass

# Some caveats:
# Does not support batch translations. Translations are always done sequentially. (moderate priority)
# Does not support embed_text for video tasks. (very low priority)
# Translation server is ignored (it's only CPU / GPU on the one lib). (no priority)
# Ignores most generation args (including beam search). (low to moderate priority)

class LlmCppTranslationApp(BaseTranslation):
    def __init__(
        self,
        model_sub_path="",
        prepend_fn=None,
        lang="",
        prepend_model_output=None,
    ):
        super().__init__()

        self.model_sub_path = model_sub_path
        self.prepend_fn = prepend_fn
        self.lang = lang

        self.prepend_model_output = prepend_model_output

    def can_load(self):
        return super().can_load(f"models/{self.model_sub_path}" + ".gguf")
    
    def get_n_context(self):
        return 750
    
    def get_server_port(self):
        return 8000
    
    def get_can_cuda(self):
        can_cuda = config_state.use_cuda and not config_state.force_translation_cpu
        return can_cuda
    
    def get_model_path_for_llmcpp(self):
        return os.path.join("models", f"{self.model_sub_path}.gguf")

    def load_model(
        self,
    ):
        can_cuda = self.get_can_cuda()
        logger.info(f"Loading translation model ({self.model_sub_path})... CanCuda={can_cuda} NGpuLayers={config_state.num_gpu_layers_mt}")

        if can_cuda:
            llama_cpp_server_path = os.path.join('models', "llamacpp_gpu", "llama-server.exe")
        else:
            # Else the CUDA binaries are still loaded.
            llama_cpp_server_path = os.path.join('models', "llamacpp_cpu", "llama-server.exe")

        self.llm = LlamaCppExecutableOpenAIClient(
            model_path=self.get_model_path_for_llmcpp(),
            num_gpu_layers=(config_state.num_gpu_layers_mt if can_cuda else 0),
            can_cuda=can_cuda,
            llama_cpp_server_path=llama_cpp_server_path,
            prepend_phrase=self.prepend_model_output,
            # Hmmmmmmmmmmmmm we use a lot of ports in Mango... from web server, to socket server, to Flask server, to this...
            n_context=self.get_n_context(),
            port=self.get_server_port(),
        )

        self.llm.start_server()

        logger.info("Done loading translation model!")

        self.loaded = True

    def unload_model(self):
        try:
            self.llm.stop_server()

            del self.llm # This should automagically call llm.stop_server() - but juuuuuuust in case we also call it above.
            logger.info("Unloading translation model...")
        except:
            pass
        self.llm = None

        return super().unload_model()
        
    def map_prompt(self, inp: str, contexts: List[str]):
        if len(contexts) == 0:
            return self.prepend_fn(f"Translate the {self.lang} text to English.\n{self.lang}: {inp}")

        base_prompt = f'Translate the {self.lang} text to English. Some previous texts are provided as context.\n'

        for i in range(len(contexts)):
            base_prompt += f'Context {i+1}: {contexts[i]}\n'

        base_prompt += f'{self.lang}: {inp}'

        return self.prepend_fn(base_prompt) 
        
    def remap_input_with_contexts(self, inp: str):
        cur_text = inp.split('<TSOS>')
        if len(cur_text) == 1:
            return inp, [] # No context.
        
        contexts = cur_text[0].strip()
        contexts = [c.strip() for c in contexts.split('<SEP>')]

        cur_text = cur_text[1].strip()
        
        if len(contexts) == 0:
            # This should never happen... but juuust in case.
            return inp, []
        
        return cur_text, contexts
    
    def create_messages(self, inp: str):
        with logger.begin_event("Splitting input & contexts") as ctx:
            inp, contexts = self.remap_input_with_contexts(inp)

            ctx.log('Done splitting', original_input=inp, cur_text=inp, contexts=contexts)

        with logger.begin_event("Creating prompt from splits") as ctx:
            prompt = self.map_prompt(inp, contexts)

            ctx.log('Done creating prompt', prompt=prompt)

        messages = [{ "role": "user", "content": prompt, }, ]
        return messages

    def translate_string(self, inp: str, use_stream=None):
        messages = self.create_messages(inp)

        with logger.begin_event("Feeding to LLM") as ctx:
            prediction = self.llm.call_llm_no_batch(messages, use_stream)

        return [prediction], [inp]
    
    def batch_translate_strings(self, inputs: List[str]):
        batch_inputs = [self.create_messages(inp) for inp in inputs]

        with logger.begin_event("Feeding to LLM") as ctx:
            predictions = self.llm.call_llm_with_batch(batch_inputs)

        ctx.log(
            f"Translated batch",
            inputs=inputs,
            outputs=predictions,
        )

        return predictions
    
    def misc_postprocess(self, output: str):
        return output.replace("\\'", "'")

    def process(
        self,
        text: str = None,
        use_stream = None,
        texts: List[str] = None,
    ):
        if texts is not None and text is not None:
            raise ValueError("Either 'text' (single) or 'texts' (batched) should be passed - not both!")

        with logger.begin_event("Translation", using_stream=use_stream is not None, is_batched=texts is not None) as ctx:
            if not self.loaded:
                self.load_model()

            if text is not None:
                if len(text) > 0 and not text.endswith("<TSOS>"):
                    output = self.translate_string(
                        text, use_stream=use_stream
                    )  # [target strings], [source strings]
                    ctx.log(
                        f"Translated",
                        input_text=text,
                        normalized=output[1],
                        output_text=output[0][0] if isinstance(output[0], list) else output[0],
                    )
                else:
                    output = [[""], [""]]  # [target strings], [source strings]
                    ctx.log(f"Poor text found - returning empty string")

                outputs = output[0]
            else:
                outputs = self.batch_translate_strings(texts) # List of strings.

            final_outputs = [self.misc_postprocess(o) for o in outputs]
            ctx.log("Postprocessed translations", before=outputs, after=final_outputs)

            return final_outputs
    
    def process_with_batch(self, texts: List[str]):
        self.translate_string()

class GoliathTranslationApp(LlmCppTranslationApp):
    def make_single_name_entry(self, name_entry):
        baseline = f"{name_entry['source']} = {name_entry['target']}"
        if name_entry['gender'] == "":
            return baseline
        
        return f"{baseline} ({name_entry['gender']})"

    def map_name_entries(self):
        if len(config_state.name_entries) == 0:
            return ""

        joined_entries = '\n'.join([self.make_single_name_entry(ne) for ne in config_state.name_entries]).strip()

        # First space needed.
        return f" Use the provided dictionary for named entity and term translations as needed. Pay close attention to gender information for pronoun reference.\nDictionary:\n{joined_entries}\n" # So two \n Total.

    def map_prompt(self, inp: str, contexts: List[str]):
        dictionary_injection = self.map_name_entries()

        if len(contexts) == 0:
            base_prompt = f"Translate the {self.lang} text to English.{dictionary_injection}\nText to Translate: {inp}"
        else:
            ctx_joined = " <SENT_SEP> ".join(contexts).strip()
            base_prompt = f"Translate the {self.lang} text to English. Some previous texts are provided as context.{dictionary_injection}\nContext: {ctx_joined}\nText to Translate: {inp}"

        return self.prepend_fn(base_prompt)
