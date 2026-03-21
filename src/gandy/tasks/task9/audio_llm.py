from gandy.translation.llama_server_wrapper import LlamaCppExecutableOpenAIClient
from gandy.state.config_state import config_state
from gandy.utils.fancy_logger import logger
from gandy.utils.find_free_port import find_tcp_port
import os

# Time-stamping is not supported as llama.cpp doesn't seem to have proper support for outputting intermediate attention data.
# If it could output attention, we could implement some form of dynamic time warping... maybe.
class AudioLLM():
    def __init__(self):
        self.loaded = False

    def get_n_context(self):
        # NOTE: 50000 = This is probably WAY too high.
        aud_tokens_per_second = 84 # 1s of audio = about 84 tokens.
        max_audio_duration_seconds = 40 # Relative pos encoding means it can flex to arbitrary lengths; but I don't expect the model to generalize well for long sequences.
        additional_buffer_tokens = 300 # There's very little "fluff" in the structure expected, but some space is still needed for the output of course.
        return aud_tokens_per_second * max_audio_duration_seconds + additional_buffer_tokens
    
    def get_server_port(self):
        return find_tcp_port()

    def get_model_path_for_llmcpp(self):
        return os.path.join("models", "audio", f"ja_llm.gguf")

    def load(self):
        if self.loaded:
            return

        with logger.begin_event("Loading audio LLM"):
            if config_state.use_cuda:
                llama_cpp_server_path = os.path.join('models', "llamacpp_gpu", "llama-server.exe")
            else:
                # Else the CUDA binaries are still loaded.
                llama_cpp_server_path = os.path.join('models', "llamacpp_cpu", "llama-server.exe")

            self.llm = LlamaCppExecutableOpenAIClient(
                model_path=self.get_model_path_for_llmcpp(),
                num_gpu_layers=(config_state.num_gpu_layers_ocr if config_state.use_cuda else 0),
                can_cuda=config_state.use_cuda,
                llama_cpp_server_path=llama_cpp_server_path,
                prepend_phrase=None,
                n_context=self.get_n_context(),
                port=self.get_server_port(),
                stop=None,
                verbose=False,
                extra_commands=[],
            )

            self.loaded = True

    def to_messages(self, audio_tokens: str, lang: str = "Japanese"):
        # Supported languages (must be lower case):
        # "english" | "chinese" | "japanese" | "korean"

        messages = [
            {
                'role': 'user',
                'content': [
                    { 
                        'type': 'text',
                        'text': f"<|{lang}|>{audio_tokens}",
                    },
                ]
            }
        ]

        return messages

    def do_generate(self, audio_tokens_batched):
        with logger.begin_event("Calling audio LLM"):
            batch_inputs = [self.to_messages(at) for at in audio_tokens_batched]
            return self.llm.call_llm_with_batch(batch_inputs)