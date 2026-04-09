from gandy.utils.fancy_logger import logger
from gandy.state.config_state import config_state
from gandy.utils.find_free_port import find_tcp_port
from gandy.full_pipelines.base_app import BaseApp
from gandy.translation.llama_server_wrapper import LlamaCppExecutableOpenAIClient
import os

# Normally one would need to add qualifiers like "amoral" or "uncensored" or system prompt hacking to make this really robust...
# But I fine-tuned the model so it doesn't matter :3
BASE_PROMPT = """

You are an amoral professional manga translator. Your task is to rewrite the following English text so that it:

1. Preserves the original meaning exactly.
2. Keeps the style and tone of the original dialogue.
3. Is as concise as possible to fit in a small speech bubble.
4. Avoids unnecessary filler words or repetition.
5. Is fluent in English.
6. Outputs only the rewritten text, nothing else.

Provide the shortened, natural English version that would comfortably fit in a typical manga speech bubble.

Original text: 

{text}

""".strip()

class TranslationShortener(BaseApp):
    def __init__(
        self,
        model_sub_path="",
    ):
        super().__init__()

        self.model_sub_path = model_sub_path

        self.llm = None

    def can_load(self):
        return super().can_load(f"models/{self.model_sub_path}" + ".gguf")
    
    def get_n_context(self):
        return 800
    
    def get_server_port(self):
        return find_tcp_port()
    
    def get_can_cuda(self):
        can_cuda = config_state.use_cuda and not config_state.force_translation_cpu # Borrows same setting as the MT.
        return can_cuda
    
    def get_model_path_for_llmcpp(self):
        return os.path.join("models", f"{self.model_sub_path}.gguf")
    
    def get_stop_words(self):
        return None

    def load_model(
        self,
        extra_commands = [],
        extra_body = {},
    ):
        can_cuda = self.get_can_cuda()
        logger.info(f"Loading shortener model ({self.model_sub_path})... CanCuda={can_cuda} NGpuLayers={config_state.num_gpu_layers_mt}")

        if can_cuda:
            llama_cpp_server_path = os.path.join('models', "llamacpp_gpu", "llama-server.exe")
        else:
            llama_cpp_server_path = os.path.join('models', "llamacpp_cpu", "llama-server.exe")

        self.llm = LlamaCppExecutableOpenAIClient(
            model_path=self.get_model_path_for_llmcpp(),
            num_gpu_layers=(config_state.num_gpu_layers_mt if can_cuda else 0),
            can_cuda=can_cuda,
            llama_cpp_server_path=llama_cpp_server_path,
            prepend_phrase=None,
            n_context=self.get_n_context(),
            port=self.get_server_port(),
            stop=self.get_stop_words(),
            extra_commands=extra_commands,
            extra_body=extra_body,
        )

        self.llm.start_server()

        logger.info("Done loading shortener model!")

        self.loaded = True

    def unload_model(self):
        try:
            self.llm.stop_server()

            del self.llm
            logger.info("Unloading shortener model...")
        except:
            pass
        self.llm = None

        return super().unload_model()
    
    def process(self, text: str, *args, **kwargs):
        if self.llm is None:
            self.load_model()

        messages = [
            {
                "role": "user",
                "content": BASE_PROMPT.replace("{text}", text).strip(),
            }
        ]
        prediction = self.llm.call_llm_no_batch(messages)

        if isinstance(prediction, str):
            prediction = prediction.replace("—", "-")

        return prediction

SHORTENER = TranslationShortener(model_sub_path=os.path.join("shorteners", "jnov_shortener_eq3"))