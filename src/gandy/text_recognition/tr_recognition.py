import albumentations as A
import numpy as np
from PIL import Image
from gandy.text_recognition.base_text_recognition import BaseTextRecognition
import albumentations as A
import numpy as np
from transformers import ViTFeatureExtractor, AutoTokenizer
from optimum.onnxruntime import ORTModelForVision2Seq
from gandy.state.config_state import config_state
from gandy.state.debug_state import debug_state
from gandy.utils.fancy_logger import logger
from uuid import uuid4
import os
import cv2


class TrOCRTextRecognitionApp(BaseTextRecognition):
    def __init__(
        self,
        model_sub_path="/",
        gen_kwargs={},
        feature_extractor_cls=ViTFeatureExtractor,
        do_resize=True,
        do_stretch=False,
        extra_postprocess=None,
    ):
        super().__init__()

        self.do_resize = do_resize

        if self.do_resize:
            self.transform = A.Compose(
                [
                    A.ToGray(always_apply=True),
                ]
            )

            assert not do_stretch, 'Stretch is only for non resizing non-Magnus models.'
        else:
            if do_stretch:
                self.transform = A.Compose(
                    [
                        A.Resize(448, 448, interpolation=cv2.INTER_CUBIC),
                        A.ToGray(always_apply=True),
                    ]
                )
            else:
                self.transform = A.Compose(
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

    def load_dataloader(self, tokenizer_path, feature_extractor_path):
        self.feature_extractor = self.feature_extractor_cls.from_pretrained(
            feature_extractor_path
        )
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)

    def can_load(self):
        s = self.model_sub_path
        return super().can_load(f"models/minocr{s}/model")

    def load_model(self):
        s = self.model_sub_path

        logger.info("Loading object recognition model...")

        can_cuda = config_state.use_cuda
        provider = "CUDAExecutionProvider" if can_cuda else "CPUExecutionProvider"
        self.model = ORTModelForVision2Seq.from_pretrained(
            f"models/minocr{s}/model", provider=provider, use_io_binding=can_cuda
        )

        self.load_dataloader(
            f"models/minocr{s}/tokenizer", f"models/minocr{s}/feature_extractor"
        )

        logger.info("Done loading object recognition model!")

        return super().load_model()

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

        if config_state.use_cuda:
            pixel_values = pixel_values.to("cuda:0")

        return pixel_values

    def postprocess(self, outp, batched = False):
        if batched:
            decoded = self.tokenizer.batch_decode(outp, skip_special_tokens=True)

            if self.extra_postprocess is not None:
                decoded = [self.extra_postprocess(d).strip() for d in decoded]
            else:
                decoded = [d.strip() for d in decoded]
        else:
            decoded = self.tokenizer.decode(outp[0, ...], skip_special_tokens=True)

            if self.extra_postprocess is not None:
                decoded = self.extra_postprocess(decoded)

            decoded = decoded.strip()

        return decoded

    def do_generate(self, image, batched = False):
        x = self.preprocess(image)
        generated = self.model.generate(x, **self.gen_kwargs)
        return self.postprocess(generated, batched=batched)
    
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
    
    def log_text(self, cropped: np.ndarray, msg: str, text: str):
        if debug_state.debug:
            debug_id = uuid4().hex

            if cropped is not None:
                os.makedirs('./debugdumps/textregions', exist_ok=True)
                Image.fromarray(cropped).save(f'./debugdumps/textregions/{debug_id}.png')

            logger.debug_message(msg, text=text, img_id=debug_id, category='text_region_dump')
        else:
            logger.log_message(msg, text=text)

    def process(self, image: Image.Image, bboxes, text_line_app, forced_image=None, text_line_app_scan_image_if_fails = True):
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

        for bbox in bboxes:
            if text_line_app is not None:
                logger.log_message(f"Using text line model for preprocessing.")

                line_texts = []
                text_region_image = (
                    forced_image if forced_image is not None else image.crop(bbox)
                )

                line_bboxes = text_line_app.get_images(text_region_image, return_image_if_fails=text_line_app_scan_image_if_fails)

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

                        outp = self.process_multiple_images(crop_batch)
                        logger.log_message(f'Processed image lines in a batch', n_lines=len(crop_batch), outp=outp)

                        line_texts.extend(outp)
                else:
                    for bb in line_bboxes:
                        cropped_image = text_region_image.crop(
                            bb
                        )  # Further cropped to a text line.
                        cropped_image = np.array(cropped_image)

                        outp = self.process_one_image(cropped_image)
                        self.log_text(cropped_image, f"Found partial text.", text=outp)

                        line_texts.append(outp)

                text = "".join(line_texts)
            else:
                cropped_image = (
                    forced_image if forced_image is not None else image.crop(bbox)
                )
                cropped_image = np.array(cropped_image)

                text = self.process_one_image(cropped_image)

                line_bboxes = None
                line_texts = None

            if config_state.batch_ocr:
                cropped_image = np.array(text_region_image) # For logging.
            self.log_text(cropped_image, f"Found complete text", text=text)
            source_texts.append(text)

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
