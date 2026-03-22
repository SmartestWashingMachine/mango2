from gandy.text_recognition.tr_recognition import TrOCRTextRecognitionApp
from gandy.translation.llama_server_wrapper import LlamaCppExecutableOpenAIClient
from gandy.utils.fancy_logger import logger
from gandy.state.config_state import config_state
from gandy.text_recognition.jamo_override import JamoOverride
from io import BytesIO
import base64
import os
from PIL import Image
import json
from gandy.utils.robust_text_line_resize import override_transforms
import numpy as np
from gandy.utils.find_free_port import find_tcp_port
from gandy.utils.pseudo_smart_image_resize import create_pseudo_smart_resize
import unicodedata
from io import BytesIO
import wave

class AsrGgufApp():
    def __init__(self, model_sub_path: str, mmproj_sub_path: str):
        self.llm = None
        self.model_sub_path = model_sub_path
        self.mmproj_sub_path = mmproj_sub_path

    def get_model_path_for_llmcpp(self):
        return os.path.join("models", f"{self.model_sub_path}.gguf")
    
    def get_mmproj_path_for_llmcpp(self):
        return os.path.join("models", f"{self.mmproj_sub_path}.gguf")
    
    def get_n_context(self):
        return 6000
    
    def get_server_port(self):
        return find_tcp_port()
    
    def get_can_cuda(self):
        # For now it borrows settings from MT model.
        return config_state.use_cuda and not config_state.force_translation_cpu

    def load_model(self):
        with logger.begin_event("Loading model"):
            can_cuda = self.get_can_cuda()
            llama_cpp_server_path = os.path.join("models", "llamacpp_gpu" if can_cuda else "llamacpp_cpu", "llama-server.exe")

            self.llm = LlamaCppExecutableOpenAIClient(
                model_path=self.get_model_path_for_llmcpp(),
                num_gpu_layers=(99 if can_cuda else 0),
                can_cuda=can_cuda,
                llama_cpp_server_path=llama_cpp_server_path,
                prepend_phrase=None,
                n_context=self.get_n_context(),
                port=self.get_server_port(),
                stop=None,
                mmproj=self.get_mmproj_path_for_llmcpp(),
                verbose=False,
            )

            self.llm.start_server()

    def process(self, audio_data: np.ndarray):
        with logger.begin_event("Transcribing audio clip") as ctx:
            if self.llm is None:
                self.load_model()

            # TODO: This might be slow.
            buffer = BytesIO()
            with wave.open(buffer, 'wb') as wav_file:
                wav_file.setnchannels(1) # Mono 1 channel
                wav_file.setsampwidth(2)  # 2 bytes per sample (16-bit)
                wav_file.setframerate(16000) # Sampling rate is fixed at 16000
                wav_file.writeframes((audio_data * 32767).astype(np.int16).tobytes()) # Denormalize
            buffer.seek(0)

            encoded_audio = base64.b64encode(buffer.getvalue()).decode("utf-8")

            messages = [
                {
                    "role": "user",
                    "content": [
                        # The prompt is because this is based on GLM-ASR.
                        # ... this model arch is very similar to other ASR models. 
                        # It just happened to be highly compatible with llama.cpp + transformers hence I decided to train one on it.
                        {"type": "text", "text": "Please transcribe this audio into text"},
                        {
                            "type": "input_audio", 
                            "input_audio": {
                                "data": encoded_audio, 
                                "format": "wav" # TODO: Right now it requires a WAV...
                            }
                        }
                    ],
                }
            ]

            # No streaming since this is a cascaded system (Transcribe -> Translate)
            prediction = self.llm.call_llm_no_batch(messages)
            ctx.log("Transcription result", prediction=prediction)
            return prediction

# TODO: No unload...