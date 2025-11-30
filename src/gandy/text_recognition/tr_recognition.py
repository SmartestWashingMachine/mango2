import albumentations as A
import numpy as np
from PIL import Image
from gandy.text_recognition.base_text_recognition import BaseTextRecognition
import albumentations as A
import numpy as np
from onnxruntime import SessionOptions, GraphOptimizationLevel, ExecutionMode
from gandy.state.config_state import config_state
from gandy.state.debug_state import debug_state
from gandy.utils.fancy_logger import logger
from uuid import uuid4
import os
import cv2
import regex as re
from gandy.utils.is_string_only_name import name_checker

def convert_line_text_to_speaker_line_text(line_text: str):
    return f'[{line_text}]: '

class TrOCRTextRecognitionApp(BaseTextRecognition):
    def __init__(
        self,
        model_sub_path="/",
        join_lines_with="",
        transform=None,
    ):
        super().__init__()

        self.transform = transform
        self.model_sub_path = model_sub_path
        self.join_lines_with = join_lines_with

    def can_load(self):
        return True

    def load_model(self):
        return super().load_model()

    def unload_model(self):
        return super().unload_model()

    def do_generate(self, image, batched = False):
        return [] # List of strings

    # Non abstract methods:

    def cut_punct(self, s: str):
        new_s = re.sub(r"[.?!。、”\"'」·．,！？\)\]]$", '', s)

        logger.log_message('Cut punctuation', old=s, new=new_s)
        return new_s

    def transform_image(self, image):
        augmented = self.transform(image=image)
        cropped_image = augmented["image"]
        return cropped_image

    def process_one_image(self, cropped_image):
        logger.log_message(f"Scanning a text region...", h=cropped_image.shape[0], w=cropped_image.shape[1])

        cropped_image = self.transform_image(cropped_image)

        output = self.do_generate(cropped_image)

        logger.log_message(f"Done scanning a text region!")
        return output
    
    def process_multiple_images(self, cropped_images):
        cropped_images = [self.transform_image(c) for c in cropped_images]
        outputs = self.do_generate(cropped_images, batched=True)
        return outputs # list of strings.
    
    def save_debug(self, cropped: np.ndarray, msg: str, text: str):
        debug_id = uuid4().hex

        if cropped is not None:
            os.makedirs('./debugdumps/textregions_JAv3', exist_ok=True)
            Image.fromarray(cropped).save(f'./debugdumps/textregions_JAv3/{debug_id}.png')

        logger.debug_message(msg, text=text, img_id=debug_id, category='text_region_dump')
    
    def log_text(self, cropped: np.ndarray, msg: str, text: str):
        if debug_state.debug and False:
            self.save_debug(cropped=cropped, msg=msg, text=text)
        else:
            logger.log_message(msg, text=text)

    def process(self, image: Image.Image, bboxes, text_line_app, forced_image=None, text_line_app_scan_image_if_fails = True, on_box_done=None):
        source_texts = []
        if len(bboxes) > 1 and forced_image is not None:
            raise RuntimeError(
                "forced_image should never be called if bboxes > 1 (task5?)"
            )
        if forced_image is not None:
            logger.log_message("Using forced image for OCR")

        line_bboxes = None
        line_texts = None

        cropped_image = None

        for bbox_idx, bbox in enumerate(bboxes):
            if text_line_app is not None:
                logger.log_message(f"Using text line model for preprocessing.")

                line_texts = []
                text_region_image = (
                    forced_image if forced_image is not None else image.crop(bbox)
                )

                with logger.begin_event('Detecting lines'):
                    line_bboxes = text_line_app.get_images(text_region_image, return_image_if_fails=text_line_app_scan_image_if_fails)

                with logger.begin_event('Actually OCR\'ing'):
                    if config_state.batch_ocr:
                        # Batch in up to 4s (per text region).
                        for batch_lines_idx in range(0, len(line_bboxes), 4):
                            end_idx = min(len(line_bboxes), (batch_lines_idx + 4))
                            lines_in_batch = line_bboxes[batch_lines_idx:end_idx]

                            crop_batch = []
                            greatest_width = 1
                            greatest_height = 1
                            for bb in lines_in_batch:
                                cropped_image = text_region_image.crop(
                                    bb
                                )  # Further cropped to a text line.
                                #cropped_image = np.array(cropped_image)
                                crop_batch.append(cropped_image)

                                greatest_width = max(greatest_width, cropped_image.width)
                                greatest_height = max(greatest_height, cropped_image.height)

                            # We don't need to resize each image to have same size anymore, even with batching.
                            crop_batch = [np.array(pil_img) for pil_img in crop_batch]

                            outp = self.process_multiple_images(crop_batch)
                            ### outp = [""]
                            logger.log_message(f'Processed image lines in a batch', n_lines=len(crop_batch), outp=outp)

                            line_texts.extend(outp)
                    else:
                        for bb in line_bboxes:
                            cropped_image = text_region_image.crop(
                                bb
                            )  # Further cropped to a text line.

                            ### print('cropping')
                            ### from random import randint
                            ### cropped_image.save(f'./test_{randint(0, 100000)}.png')
                            cropped_image = np.array(cropped_image)

                            outp = self.process_one_image(cropped_image)
                            ### outp = ""
                            self.log_text(cropped_image, f"Found partial text.", text=outp)

                            line_texts.append(outp)

                with logger.begin_event("Postprocessing lines.", detect_speaker_name=config_state.detect_speaker_name) as ctx:
                    if self.join_lines_with is not None and len(line_texts) > 1:
                        for lt_idx in range(len(line_texts[:-1])):
                            line_texts[lt_idx] = str(line_texts[lt_idx]) + self.join_lines_with

                    if config_state.detect_speaker_name and len(line_texts) > 1:
                        detected_name_data = name_checker.is_string_only_name(line_texts[0])

                        if detected_name_data["is_name"]:
                            line_texts[0] = convert_line_text_to_speaker_line_text(detected_name_data["cleaned"])

                        ctx.log(
                            "Done checking if line was a speaker name.",
                            is_name=detected_name_data["is_name"],
                            cleaned_if_was_name=detected_name_data["cleaned"],
                        )

                text = "".join(line_texts)
            else:
                cropped_image = (
                    forced_image if forced_image is not None else image.crop(bbox)
                )

                cropped_image = np.array(cropped_image)

                # DEBUG STUFF
                if debug_state.debug:#forced_image is None and True:
                    self.save_debug(cropped_image, msg='Saving partial line image from batch', text='N/A (Batched)')

                text = self.process_one_image(cropped_image)

                line_bboxes = None
                line_texts = None

            if config_state.batch_ocr and text_line_app is not None:
                cropped_image = np.array(text_region_image) # For logging.
            self.log_text(cropped_image, f"Found complete text", text=text)
            source_texts.append(text)

            if on_box_done is not None:
                on_box_done(bbox_idx)

        return source_texts, line_bboxes, line_texts
