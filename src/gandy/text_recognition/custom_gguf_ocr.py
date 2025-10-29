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

"""
The config file here only has these fields:

- text_prompt (string): What text to feed to the LLM alongside the image.
- n_context (integer): Max amount of tokens that the model can parse - not to be confused with context inputs in Mango.
- mmproj_name (string): The name of the mmproj GGUF file, located in the same folder. If the file was 'mmproj-BF16.gguf' then this should be 'mmproj-BF16'
"""

# TODO: Redundant code.
def image_to_base64(new_image, format="PNG"):
    buffer = BytesIO()
    new_image.save(buffer, format="PNG")
    new_image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return f"data:image/{format.lower()};base64,{new_image_base64}"

class CustomGgufOcrApp(TrOCRTextRecognitionApp):
    def __init__(self, model_sub_path="/", config_sub_path="/", join_lines_with="", transform=None):
        super().__init__(model_sub_path, join_lines_with=join_lines_with, transform=transform)

        self.config_sub_path = config_sub_path

    def load_mango_config(self):
        with logger.begin_event("Loading Mango config") as ctx:
            with open(self.get_mango_config_path(), 'r', encoding='utf-8') as f:
                mango_config = json.load(f)
                ctx.log('Loaded Mango config', mango_config=mango_config)

                self.join_lines_with = mango_config.get("join_lines_with", "")

        return mango_config

    def get_can_cuda(self):
        can_cuda = config_state.use_cuda and not config_state.force_ocr_cpu and config_state.num_gpu_layers_ocr > 0
        return can_cuda
    
    def get_n_context(self):
        return int(self.mango_config["n_context"])
    
    def get_server_port(self):
        return 7700
    
    def get_model_path_for_llmcpp(self):
        if self.model_sub_path == "config":
            return os.path.join("models", "custom_ocrs", f"{self.mango_config['model_name']}.gguf")

        return os.path.join("models", "custom_ocrs", f"{self.model_sub_path}.gguf")
    
    def get_mmproj_path_for_llmcpp(self):
        return os.path.join("models", "custom_ocrs", f"{self.mango_config['mmproj_name']}.gguf")
    
    def get_mango_config_path(self):
        return f"models/custom_ocrs/{self.config_sub_path}" + ".mango_config.json"
    
    def can_load(self):
        return os.path.exists(self.get_mango_config_path())

    # load_model() and unload_model() are taken from CustomGgufTranslationApp - TODO: Refactor.
    def load_model(
        self,
    ):
        self.mango_config = self.load_mango_config()

        can_cuda = self.get_can_cuda()
        logger.info(f"Loading custom OCR model ({self.model_sub_path})... CanCuda={can_cuda} NGpuLayers={config_state.num_gpu_layers_ocr}")

        if can_cuda:
            llama_cpp_server_path = os.path.join('models', "llamacpp_gpu", "llama-server.exe")
        else:
            # Else the CUDA binaries are still loaded.
            llama_cpp_server_path = os.path.join('models', "llamacpp_cpu", "llama-server.exe")

        self.llm = LlamaCppExecutableOpenAIClient(
            model_path=self.get_model_path_for_llmcpp(),
            num_gpu_layers=(config_state.num_gpu_layers_ocr if can_cuda else 0),
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

        logger.info("Done loading custom OCR model!")

        self.loaded = True

        # Call whatever is the ancestor of TrOCRTextRecognitionApp (the base app).
        return super(TrOCRTextRecognitionApp, self).load_model()

    def unload_model(self):
        try:
            self.llm.stop_server()

            del self.llm # This should automagically call llm.stop_server() - but juuuuuuust in case we also call it above.
            logger.info("Unloading OCR model...")
        except:
            pass
        self.llm = None

        return super(TrOCRTextRecognitionApp, self).unload_model()
    
    def image_to_llm_messages(self, image):
        image = Image.fromarray(image) # To PIL and then to base64. TODO: Optimize?

        messages = [
            {
                'role': 'user',
                'content': [
                    { 
                        'type': 'text',
                        'text': self.mango_config['text_prompt'],
                    },
                    {
                        'type': 'image_url',
                        'image_url': {
                            'url': image_to_base64(image),
                        }
                    }
                ]
            }
        ]

        return messages

    def ocr_images(self, images):
        with logger.begin_event('Preparing inputs'):
            batch_inputs = [self.image_to_llm_messages(image) for image in images]
        with logger.begin_event('Calling OCR LLM'):
            prediction = self.llm.call_llm_with_batch(batch_inputs)

        # For my Korean OCR variant.
        overrides = self.mango_config.get("overrides", {})

        if "jamo" in overrides and overrides["jamo"]:
            prediction = [JamoOverride.postprocess(p.strip()) for p in prediction]

        prediction = [p.strip() for p in prediction]

        return prediction

    def do_generate(self, image, batched = False):
        # image = single numpy image if batched=False
        # image = list of numpy images if batched=True
        if not batched:
            images = [image]
        else:
            images = image

        with logger.begin_event('Generating OCR results', batched=batched):
            output_texts = self.ocr_images(images)

            if batched:
                return output_texts
            else:
                # Must return single string instead of list here... TODO: Refactor.
                return output_texts[0]
