from gandy.translation.base_translation import BaseTranslation
from gandy.utils.fancy_logger import logger
from gandy.state.config_state import config_state
from typing import List

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

        self.mt_cache = None

        self.prepend_model_output = prepend_model_output

    def can_load(self):
        return super().can_load(f"models/{self.model_sub_path}" + ".gguf")

    def load_model(
        self,
    ):
        can_cuda = config_state.use_cuda and not config_state.force_translation_cpu
        logger.info(f"Loading translation model ({self.model_sub_path})... CanCuda={can_cuda} NGpuLayers={config_state.num_gpu_layers_mt}")

        if can_cuda:
            from llama_cpp_cuda import Llama as LlamaGpu

            llm_to_use = LlamaGpu
        else:
            from llama_cpp import Llama as LlamaCpu

            llm_to_use = LlamaCpu

        self.llm = llm_to_use(
            model_path=f"models/{self.model_sub_path}" + ".gguf",
            n_ctx=512,
            n_gpu_layers=config_state.num_gpu_layers_mt if can_cuda else 0,
            flash_attn=can_cuda,
            verbose=False,
            #no_perf=True,
            #n_threads_batch=3,
            use_mlock=True,
            logits_all=False,
            use_mmap=True,
            prepend_phrase=self.prepend_model_output,
        )

        logger.info("Done loading translation model!")

        self.loaded = True

    def unload_model(self):
        try:
            del self.llm
            logger.info("Unloading translation model...")
        except:
            pass
        self.llm = None

        return super().unload_model()

    def batch_translate_with_server(self, texts: List[str]):
        with logger.begin_event("Batch Translating with Server (no difference for LLMs currently)") as ctx:
            tars = []

            for t in texts:
                out = self.process(t, use_stream=None)[0] # list[str]
                tars.append(out)

            return tars
        
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

    def call_llm(self, messages, use_stream):
        model_output = self.llm.create_chat_completion(
            messages=messages,
            stream=use_stream is not None,
            dry_multiplier=0.8,
            dry_base=1.75,
            dry_allowed_length=2,
            dry_seq_breakers=["\n", ":", "\"", '*'],
            dry_range=-1,
            temperature=0.02,
        )

        if use_stream is not None:
            prediction = ""

            for out in model_output:
                try:
                    new_word = out['choices'][0]['delta']['content']
                    use_stream.put(new_word, already_detokenized=True)

                    prediction += new_word
                except Exception as e:
                    pass # First entry has nothing, as does last (usually).
        else:
            prediction = model_output['choices'][0]['message']['content']

        return prediction

    def translate_string(self, inp: str, use_stream=None):
        with logger.begin_event("Splitting input & contexts") as ctx:
            inp, contexts = self.remap_input_with_contexts(inp)

            ctx.log('Done splitting', original_input=inp, cur_text=inp, contexts=contexts)

        with logger.begin_event("Creating prompt from splits") as ctx:
            prompt = self.map_prompt(inp, contexts)

            ctx.log('Done creating prompt', prompt=prompt)

        with logger.begin_event("Feeding to LLM") as ctx:
            messages = [{ "role": "user", "content": prompt, }, ]
            prediction = self.call_llm(messages, use_stream)

        return [prediction], [inp]

    def process(
        self,
        text: str = None,
        use_stream=None,
    ):
        with logger.begin_event("Translation", using_stream=use_stream is not None) as ctx:
            if not self.loaded:
                self.load_model()

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

        return output[0]

    def embed_text(self, s: str):
        if self.mt_cache is None:
            self.load_mt_cache()

        return torch.tensor(self.mt_cache.embed_text(s))