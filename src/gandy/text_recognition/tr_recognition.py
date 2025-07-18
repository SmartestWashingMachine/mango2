import albumentations as A
import numpy as np
from PIL import Image
from gandy.text_recognition.base_text_recognition import BaseTextRecognition
import albumentations as A
import numpy as np
from transformers import ViTFeatureExtractor, AutoTokenizer
from optimum.onnxruntime import ORTModelForVision2Seq
from onnxruntime import SessionOptions, GraphOptimizationLevel, ExecutionMode
from gandy.state.config_state import config_state
from gandy.state.debug_state import debug_state
from gandy.utils.fancy_logger import logger
from uuid import uuid4
import os
import cv2
import regex as re

try:
    import torch
except:
    pass


class TrOCRTextRecognitionApp(BaseTextRecognition):
    def __init__(
        self,
        model_sub_path="/",
        gen_kwargs={},
        feature_extractor_cls=ViTFeatureExtractor,
        do_resize=True,
        do_stretch=False,
        extra_postprocess=None,
        join_lines_with="",
        transform=None,
    ):
        super().__init__()

        self.do_resize = do_resize

        if self.do_resize:
            self.transform = transform or A.Compose(
                [
                    A.ToGray(always_apply=True),
                ]
            )

            assert not do_stretch, 'Stretch is only for non resizing non-Magnus models.'
        else:
            if do_stretch:
                self.transform = transform or A.Compose(
                    [
                        A.Resize(448, 448, interpolation=cv2.INTER_CUBIC),
                        A.ToGray(always_apply=True),
                    ]
                )
            else:
                self.transform = transform or A.Compose(
                    [
                        # In theory Massive OCR should be able to extrapolate rather well. Perhaps LongestMaxSize is unnecessary?
                        A.LongestMaxSize(512, always_apply=True),
                        A.PadIfNeeded(
                            None,
                            None,
                            pad_width_divisor=16,
                            pad_height_divisor=16,
                            border_mode=cv2.BORDER_CONSTANT,
                            value=0,
                        ),
                        A.ToGray(always_apply=True),
                    ]
                )

        self.model_sub_path = model_sub_path

        self.gen_kwargs = gen_kwargs

        self.feature_extractor_cls = feature_extractor_cls

        self.extra_postprocess = extra_postprocess
        
        self.join_lines_with = join_lines_with

    def load_dataloader(self, tokenizer_path, feature_extractor_path):
        self.feature_extractor = self.feature_extractor_cls.from_pretrained(
            feature_extractor_path
        )
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)

    def can_load(self):
        s = self.model_sub_path
        return super().can_load(f"models/minocr{s}/model")

    def load_model(self):
        logger.info("Loading object recognition model...")

        can_cuda = config_state.use_cuda and not config_state.force_ocr_cpu

        self.load_generation_model(can_cuda=can_cuda)

        s = self.model_sub_path
        self.load_dataloader(
            f"models/minocr{s}/tokenizer", f"models/minocr{s}/feature_extractor"
        )

        logger.info("Done loading object recognition model!")

        return super().load_model()
    
    def load_generation_model(self, can_cuda: bool):
        s = self.model_sub_path

        provider = "CUDAExecutionProvider" if can_cuda else "CPUExecutionProvider"

        options = SessionOptions()
        options.intra_op_num_threads = 4
        options.inter_op_num_threads = 4
        options.execution_mode = ExecutionMode.ORT_SEQUENTIAL

        options.graph_optimization_level = GraphOptimizationLevel.ORT_ENABLE_ALL

        options.enable_mem_pattern = False
        options.enable_profiling = False
        options.enable_cpu_mem_arena = False
        options.enable_mem_reuse = False

        self.model = ORTModelForVision2Seq.from_pretrained(
            f"models/minocr{s}/model", provider=provider, use_io_binding=can_cuda, session_options=options, use_cache=True,
        )

    def unload_model(self):
        try:
            del self.model
            logger.info("Unloading object recognition model...")
        except:
            pass
        self.model = None

        return super().unload_model()

    def preprocess(self, inp):
        pixel_values = self.feature_extractor(
            inp, return_tensors="pt", do_resize=self.do_resize
        ).pixel_values
        
        if not self.do_resize:
            # bchw
            logger.log_message(f'Using variable TrOCR variant', h=pixel_values.shape[2], w=pixel_values.shape[3])

        if config_state.use_cuda and not config_state.force_ocr_cpu:
            pixel_values = pixel_values.to("cuda:0")

        return pixel_values

    def cut_punct(self, s: str):
        new_s = re.sub(r"[.?!。、”\"'」·．,！？\)\]]$", '', s)

        logger.log_message('Cut punctuation', old=s, new=new_s)
        return new_s

    def postprocess(self, outp, batched = False):
        if batched:
            decoded = self.tokenizer.batch_decode(outp, skip_special_tokens=True)

            final_decoded = []
            for d in decoded:
                if self.extra_postprocess is not None:
                    d = self.extra_postprocess(d)
                d = d.strip()

                if config_state.cut_ocr_punct:
                    d = self.cut_punct(d)

                final_decoded.append(d)

            return final_decoded
        else:
            decoded = self.tokenizer.decode(outp[0, ...], skip_special_tokens=True)

            if self.extra_postprocess is not None:
                decoded = self.extra_postprocess(decoded)

            decoded = decoded.strip()

            if config_state.cut_ocr_punct:
                decoded = self.cut_punct(decoded)

            return decoded

    def do_generate(self, image, batched = False):
        with logger.begin_event('Generating OCR results', batched=batched):
            with logger.begin_event('Preprocessing for OCR'):
                x = self.preprocess(image)
            with logger.begin_event('Generating'):
                generated = self.model.generate(x, num_beams=3, no_repeat_ngram_size=99)
            with logger.begin_event('Postprocessing'):
                postprocessed = self.postprocess(generated, batched=batched)

            return postprocessed
    
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

                            # Make all images same size.
                            for idx in range(len(crop_batch)):
                                # Slight stretching.
                                cropped_image: Image.Image = crop_batch[idx]
                                cropped_image = cropped_image.resize((greatest_width, greatest_height), resample=Image.BICUBIC)
                                crop_batch[idx] = np.array(cropped_image)

                                if debug_state.debug:
                                    self.save_debug(crop_batch[idx], msg='Saving partial line image from batch', text='N/A (Batched)')

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

                if self.join_lines_with is not None and len(line_texts) > 1:
                    for lt_idx in range(len(line_texts[:-1])):
                        line_texts[lt_idx] = str(line_texts[lt_idx]) + self.join_lines_with

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

class MagnusTextRecognitionApp(TrOCRTextRecognitionApp):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # do_resize is ignored as an __init__ parameter. Magnus OCR models have their own predefined transforms.
        self.transform = None

        self.prior_transform = A.Compose([
            A.LongestMaxSize(max_size=512, always_apply=True),
        ])

    def transform_image(self, image):
        image = self.prior_transform(image=image)["image"]

        im_height = image.shape[0]
        im_width = image.shape[1]
        tfm_magnus = A.Compose([
            # INTER_CUBIC is a bit better than INTER_LINEAR for enlarging images.
            # In here we always expand the image (or keep-as-is), distorting the aspect ratio slightly.
            A.Resize(height=max(96, im_height), width=max(96, im_width), interpolation=cv2.INTER_CUBIC),
            A.PadIfNeeded(min_height=None, min_width=None, pad_height_divisor=16, pad_width_divisor=16, border_mode=cv2.BORDER_CONSTANT, value=0),
            A.ToGray(always_apply=True),
        ])

        image = tfm_magnus(image=image)["image"]

        return image
