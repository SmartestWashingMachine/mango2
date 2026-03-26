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

"""
The config file here only has these fields:

- text_prompt (string): What text to feed to the LLM alongside the image.
- n_context (integer): Max amount of tokens that the model can parse - not to be confused with context inputs in Mango.
- mmproj_name (string): The name of the mmproj GGUF file, located in the same folder. If the file was 'mmproj-BF16.gguf' then this should be 'mmproj-BF16'
"""

# Vibe coded this function because I hate emojis.
def remove_emojis(s: str):
    result = []
    for char in s:
        cat = unicodedata.category(char)

        if cat[0] in ('L', 'N', 'P', 'Z'):
            result.append(char)

        elif cat[0] == 'S':
            try:
                name = unicodedata.name(char).upper()
                if "HEART" in name:
                    result.append(char)
            except ValueError:
                continue
                
    return "".join(result)

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

                overrides = mango_config.get("overrides", {})
                if "transform" in overrides:
                    if overrides["transform"] == "pseudo_smart_resize":
                        self.transform = create_pseudo_smart_resize(overrides["min_pixels"], overrides["max_pixels"], overrides["patch_size"], overrides["merge_size"])
                    else:
                        found = override_transforms.get(overrides["transform"], self.transform)
                        self.transform = found

        return mango_config

    def get_can_cuda(self):
        can_cuda = config_state.use_cuda and not config_state.force_ocr_cpu and config_state.num_gpu_layers_ocr > 0
        return can_cuda
    
    def get_n_context(self):
        return int(self.mango_config["n_context"])
    
    def get_server_port(self):
        return find_tcp_port()
    
    def get_model_path_for_llmcpp(self):
        if self.model_sub_path == "config":
            return self.locate_in_folder(f"{self.mango_config['model_name']}.gguf")

        # TODO - below should never be called anyways.
        return os.path.join("models", "custom_translators", f"{self.model_sub_path}.gguf")
    
    def get_mmproj_path_for_llmcpp(self):
        return self.locate_in_folder(f"{self.mango_config['mmproj_name']}.gguf")
    
    def get_mango_config_path(self):
        return f"{self.config_sub_path}.json"
    
    def locate_in_folder(self, file_name: str):
        return os.path.join(os.path.dirname(self.config_sub_path), file_name)
    
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

        extra_commands = self.mango_config.get("extra_commands", [])
        if "warmup" in self.mango_config:
            extra_commands.append("--no-warmup")

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
            extra_commands=extra_commands,
            extra_body={
                # The Nano model does not support prompt caching. Others might, but let's not risk it.
                "cache_prompt": False,
            },
        )

        self.llm.start_server()

        logger.info("Done loading custom OCR model!")

        self.loaded = True

        # Call whatever is the ancestor of TrOCRTextRecognitionApp (the base app).
        retn = super(TrOCRTextRecognitionApp, self).load_model()

        # The default warmup image used is pretty heavy for my default lightweight OCR models - using more memory than it should.
        # Thanks to ngxson we can manually warm it up with our expected max image size (https://github.com/ggml-org/llama.cpp/pull/17652)
        if "warmup" in self.mango_config:
            self.warmup_image(self.mango_config["warmup"]["width"], self.mango_config["warmup"]["height"])

        return retn

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

        prediction = [p.replace("\n", " ").replace("  ", " ").replace("❤", "♥").replace("♡", "♥").strip() for p in prediction]

        if self.mango_config.get("remove_emojis", False):
            prediction = [remove_emojis(p) for p in prediction]

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

    def warmup_image(self, width: int, height: int):
        with logger.begin_event("Warming up OCR model with image size", width=width, height=height):
            dummy_image = np.array(Image.new("RGB", (width, height)))
            batch_inputs = [self.image_to_llm_messages(dummy_image)]

            self.llm.call_llm(batch_inputs, max_completion_tokens=1)