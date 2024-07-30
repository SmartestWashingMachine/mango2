from typing import List
from gandy.full_pipelines.base_app import BaseApp
from gandy.text_detection.base_image_detection import BaseImageDetection
from gandy.text_recognition.base_text_recognition import BaseTextRecognition
from gandy.translation.base_translation import BaseTranslation
from gandy.spell_correction.base_spell_correction import BaseSpellCorrection
from gandy.image_cleaning.base_image_clean import BaseImageClean
from gandy.image_redrawing.base_image_redraw import BaseImageRedraw
import numpy as np
from PIL.Image import Image
from gandy.utils.replace_terms import replace_terms
from gandy.utils.get_sep_regex import get_last_sentence
from flask_socketio import SocketIO
from gandy.utils.fancy_logger import logger
from gandy.utils.text_processing import merge_texts, pack_context
from gandy.state.config_state import config_state
from gandy.utils.join_nearby_speech_bubbles import (
    join_nearby_speech_bubbles_for_source_texts,
)


def create_entire_bbox(image: Image):
    im_width, im_height = image.size
    speech_bboxes = np.array(
        [[0, 0, im_width, im_height]]
    )  # Scan the entire image with the OCR model.
    return speech_bboxes


def replace_terms_source_side(sentences, terms):
    return replace_terms(sentences, terms, on_side="source")


def replace_terms_target_side(sentences, terms):
    return replace_terms(sentences, terms, on_side="target")


class DefaultFrameDetectionApp(BaseImageDetection):
    def __init__(self):
        super().__init__()

    def process(self, image):
        im_width, im_height = image.size
        frame_bboxes = np.array([[0, 0, im_width, im_height]])

        return frame_bboxes


class DefaultSpellCorrectionApp(BaseSpellCorrection):
    def __init__(self):
        super().__init__()

    def process(self, translation_input, translation_output):
        return translation_output


class BasePipeline:
    def __init__(
        self,
        text_detection_app: BaseImageDetection,
        text_recognition_app: BaseTextRecognition,
        translation_app: BaseTranslation,
        spell_correction_app: BaseSpellCorrection,
        image_cleaning_app: BaseImageClean,
        image_redrawing_app: BaseImageRedraw,
        reranking_app: BaseTranslation,
        text_line_model_app: BaseImageDetection,
    ):
        if text_detection_app is None:
            raise RuntimeError("text_detection_app must be given.")
        else:
            self.text_detection_app = text_detection_app

        if text_recognition_app is None:
            raise RuntimeError("text_recognition_app must be given.")
        else:
            self.text_recognition_app = text_recognition_app

        if translation_app is None:
            raise RuntimeError("translation_app must be given.")
        else:
            self.translation_app = translation_app

        if spell_correction_app is None:
            raise RuntimeError("spell_correction_app must be given.")
        else:
            self.spell_correction_app = spell_correction_app

        if image_cleaning_app is None:
            raise RuntimeError("image_cleaning_app must be given.")
        else:
            self.image_cleaning_app = image_cleaning_app

        if image_redrawing_app is None:
            raise RuntimeError("image_redrawing_app must be given.")
        else:
            self.image_redrawing_app = image_redrawing_app

        if reranking_app is None:
            raise RuntimeError("reranking_app must be given.")
        else:
            self.reranking_app = reranking_app

        if text_line_model_app is None:
            raise RuntimeError("text_line_model_app must be given")
        else:
            self.text_line_app = text_line_model_app

    def log_app_usage(self, ctx):
        ctx.log(
            f"Apps used",
            text_detection=self.text_detection_app.get_sel_app_name(),
            text_line=self.text_line_app.get_sel_app_name(),
            text_recognition=self.text_recognition_app.get_sel_app_name(),
            translation=self.translation_app.get_sel_app_name(),
            reranking=self.reranking_app.get_sel_app_name(),
            post_edit=self.spell_correction_app.get_sel_app_name(),
            clean=self.image_cleaning_app.get_sel_app_name(),
            redraw=self.image_redrawing_app.get_sel_app_name(),
        )

    def correct_translation(self, source_texts: List[str], translation_output: str):
        with logger.begin_event("Spelling correction"):
            # But the spelling correction apps will take care of removing any contextual sentences from the final output.
            translation_output = self.spell_correction_app.begin_process(
                # This ignores current - source_texts[:idx], translation_output
                source_texts,
                translation_output,
            )  # string

        return translation_output

    def get_target_texts_from_str(
        self,
        source_texts: List[str],
        use_stream: bool,
        socketio: SocketIO = None,
        with_global_cache=False,
    ):
        target_texts: List[str] = []

        for idx, text in enumerate(source_texts):
            translation_candidates = self.translation_app.begin_process(
                text=text,
                use_stream=use_stream,
            )  # string[]

            with logger.begin_event("Reranking"):
                translation_output = self.reranking_app.begin_process(
                    source_text=text, candidates=translation_candidates
                )  # string

            translation_output = self.correct_translation(
                source_texts[: idx + 1], translation_output
            )  # string

            target_texts.append(translation_output)

        return replace_terms_target_side(target_texts, config_state.terms)

    def get_source_texts_from_bboxes(
        self,
        rgb_image: Image,
        speech_bboxes,
        forced_image=None,
        return_line_bboxes=False,
    ):
        source_texts: List[str] = []
        line_bboxes = None
        line_texts = None

        with logger.begin_event("Text recognition"):
            source_texts, line_bboxes, line_texts = self.text_recognition_app.process(
                rgb_image,
                speech_bboxes,
                text_line_app=self.text_line_app.get_sel_app(),
                forced_image=forced_image,
            )

        if return_line_bboxes:
            return source_texts, line_bboxes, line_texts
        return source_texts

    def get_bboxes_from_image(self, rgb_image: Image):
        with logger.begin_event("Text detection"):
            speech_bboxes = self.text_detection_app.begin_process(rgb_image)

        return speech_bboxes

    def image_to_image(
        self,
        image: Image,
        clear_spelling_correction_context=True,
        progress_cb=None,
        return_debug_data=False,
    ):
        with logger.begin_event("Image to image") as ctx:
            # Spelling correction apps may have their own internal context cache, which is only cleared on task1 start.
            # (since every page is assumed to be independent)
            if clear_spelling_correction_context:
                self.spell_correction_app.get_sel_app().clear_cache()
            rgb_image = image.convert("RGB")

            if progress_cb is not None:
                progress_cb(progress=10)

            speech_bboxes = self.get_bboxes_from_image(rgb_image)
            if progress_cb is not None:
                progress_cb(progress=20)

            source_texts, line_bboxes, line_texts = self.get_source_texts_from_bboxes(
                rgb_image, speech_bboxes, return_line_bboxes=True
            )
            source_texts = replace_terms_source_side(source_texts, config_state.terms)
            if progress_cb is not None:
                progress_cb(progress=50)

            # This is the only task fn that can merge nearby lines if a certain text line model variant is used (YOLO Ex).
            # Task5 merges all texts into one regardless of the model being used.
            if (
                self.text_line_app.get_sel_app_name() == "yolo_line_e"
                and self.text_detection_app.get_sel_app_name() == "none"
            ):
                n_before = len(speech_bboxes)
                (
                    speech_bboxes,
                    source_texts,
                ) = join_nearby_speech_bubbles_for_source_texts(
                    line_bboxes, line_texts, rgb_image
                )
                ctx.log(
                    "Merging due to YOLO Line EX being used",
                    n_text_regions=n_before,
                    n_after=len(speech_bboxes),
                )

            source_texts = pack_context(source_texts, config_state.n_context)

            target_texts = self.get_target_texts_from_str(
                source_texts=source_texts, use_stream=None
            )
            if progress_cb is not None:
                progress_cb(80)

            cleaning_output = self.image_cleaning_app.begin_process(
                rgb_image, speech_bboxes
            )
            if isinstance(
                cleaning_output, tuple
            ):  # Quick fix for adaptive_image_clean.
                rgb_image = cleaning_output[0]
                text_colors = cleaning_output[1]
            else:
                rgb_image = cleaning_output
                text_colors = None

            if progress_cb is not None:
                progress_cb(progress=90)

            rgb_image = self.image_redrawing_app.begin_process(
                rgb_image, speech_bboxes, target_texts, text_colors
            )

            is_amg = isinstance(
                rgb_image, dict
            )  # AMG convert app returns a dict rather than an image directly.

            if return_debug_data:
                debug_data = {
                    "speech_bboxes": speech_bboxes,
                    "target_texts": target_texts,
                    "source_texts": source_texts,
                }
                return rgb_image, is_amg, debug_data
            return rgb_image, is_amg

    def text_to_text(
        self,
        text: str,
        socketio: SocketIO = None,
        output_attentions=False,
        use_stream=None,
        return_source_text=False,
    ):
        with logger.begin_event("Text to text") as ctx:
            # <SEP> tokens are already added from the client / context state for this task.

            source_texts = replace_terms_source_side([text], config_state.terms)

            target_texts = self.get_target_texts_from_str(
                source_texts, socketio=socketio, use_stream=use_stream
            )

            if return_source_text:
                return target_texts, source_texts
            return target_texts

    def image_to_untranslated_texts(
        self, image: Image, with_text_detect=False, with_ocr=True
    ):
        with logger.begin_event("Image to untranslated texts") as ctx:
            image = image.convert("RGB")

            if with_text_detect:
                speech_bboxes = self.get_bboxes_from_image(image)
            else:
                speech_bboxes = create_entire_bbox(image)

            if with_ocr:
                source_texts = self.get_source_texts_from_bboxes(image, speech_bboxes)
                return source_texts
            else:
                return image, speech_bboxes

    def image_to_single_text(
        self, image: Image, with_text_detect=False, context_input=[], use_stream=None
    ):
        with logger.begin_event("Image to single text") as ctx:
            image = image.convert("RGB")

            source_texts = self.image_to_untranslated_texts(image, with_text_detect)

            if len(source_texts) == 0:
                return []
            # Task3 assumes that there is only one detected text item to translate, but sometimes there are multiple text items to translate. (Such as the case with DETR-VN).
            # How do we handle this? Simple! After text recognition, combine all of the recognized text into one unit and translate it all together.
            source_texts = merge_texts(source_texts, context_input)

            target_texts = self.get_target_texts_from_str(
                [source_texts], use_stream=use_stream
            )

            return target_texts, source_texts
