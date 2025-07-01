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
from gandy.state.debug_state import debug_state
from gandy.utils.join_nearby_speech_bubbles import (
    join_nearby_speech_bubbles_for_source_texts,
)
from gandy.utils.get_bottom_rows import get_bottom_rows
from gandy.utils.image_chunking import detect_image_chunks
from math import floor
from uuid import uuid4
import os
import json
from gandy.utils.faiss_mt_cache import MTCache

def dump_task1_debug_data(rgb_image: Image, speech_bboxes):
    debug_id = uuid4().hex
    logger.debug_message('Dumping task1 data', category='task1_dump', debug_id=debug_id)
    os.makedirs(f'./debugdumps/task1boxes/{debug_id}', exist_ok=True)

    rgb_image.save(f'./debugdumps/task1boxes/{debug_id}/image.png')
    with open(f'./debugdumps/task1boxes/{debug_id}/bboxes.json', 'w', encoding='utf-8') as f:
        json.dump({ 'bboxes': speech_bboxes, }, f, indent=4)


def create_entire_bbox(image: Image):
    im_width, im_height = image.size
    speech_bboxes = np.array(
        [[0, 0, im_width, im_height]]
    )  # Scan the entire image with the OCR model.
    return speech_bboxes


def replace_terms_source_side(sentences, terms):
    return replace_terms(sentences, terms, on_side="source", split_context=True)


def replace_terms_target_side(sentences, terms):
    return replace_terms(sentences, terms, on_side="target")

def compute_progress(cur_step: int, max_steps: int, min_value: int, max_value: int):
    return (min_value + floor((max_value - min_value) * ((cur_step + 1) / max(1, max_steps))))


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

    def process(self, text, target, use_stream = None, **kwargs):
        return target


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
        self.mt_cache = MTCache()

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

    def correct_translation(self, translation_input: str, translation_output: str, use_stream=None):
        with logger.begin_event("Spelling correction"):
            # But the spelling correction apps will take care of removing any contextual sentences from the final output.
            translation_output = self.spell_correction_app.begin_process(
                text=translation_input,
                target=translation_output,
                use_stream=use_stream,
            )  # string

        return translation_output
    
    def embed_text(self, s: str):
        return self.translation_app.get_sel_app().embed_text(s)

    def get_target_texts_from_str(
        self,
        source_texts: List[str],
        use_stream: bool,
        socketio: SocketIO = None,
        with_global_cache=False,
        progress_cb=None,
    ):
        target_texts: List[str] = []

        # Currently the MT model supports batching (the spelling correction does not).
        all_translation_outputs: List[str] = ["" for _ in source_texts]
        was_found_in_cache: List[bool] = [False for _ in source_texts]

        source_texts_to_batch: List[str] = [] # Non-cached source texts will be collected into a batch.
        source_indices_to_batch: List[int] = [] # Which indices to place the outputs from batching into 'all_translation_outputs'.

        for idx, text in enumerate(source_texts):
            found_in_cache = False # Don't translate + correct spelling if we already found one (potentially) spelling corrected translation in cache.
            if config_state.cache_mt:
                translation_candidates, cache_embedding = self.mt_cache.look_for_translation(text)

                if translation_candidates is not None:
                    found_in_cache = True

                translation_output = translation_candidates[0] # Only 1 candidate is returned.
                all_translation_outputs[idx] = translation_output

                was_found_in_cache[idx] = found_in_cache # True

            if not found_in_cache:
                source_texts_to_batch.append(text)
                source_indices_to_batch.append(idx)

        # Actually batch translate now.
        if len(source_texts_to_batch) > 1:
            with logger.begin_event('Batching translations', n_batch={len(source_texts_to_batch)}):
                translation_outputs = self.translation_app.begin_process(
                    texts=source_texts_to_batch,
                    use_stream=use_stream,
                )  # string[]
        else:
            translation_candidates = self.translation_app.begin_process(
                text=source_texts_to_batch[0],
                use_stream=use_stream, # use_stream is actually used when text= is used (not with texts=).
            )  # string[]
            translation_outputs = [translation_candidates[0]] # Only 1 candidate is returned.

        assert len(translation_outputs) == len(source_indices_to_batch)
        for output, idx in zip(translation_outputs, source_indices_to_batch):
            all_translation_outputs[idx] = output
            # The cache[idx] is still False, which means after the spelling correction is done the translation will be cached.

        # TODO(?): Batching spelling corrections too.
        for idx, (text, translation_output, found_in_cache) in enumerate(zip(source_texts, all_translation_outputs, was_found_in_cache)):

            if not found_in_cache:
                # Reranking logic used to be here too but is now gone. 
                # We implicitly train the LLMs to be reranking-aware (with certain caveats... nothing in life is free. Except free stuff)

                translation_output = self.correct_translation(
                    translation_input=text, translation_output=translation_output, use_stream=use_stream,
                )  # string

            target_texts.append(translation_output)

            if config_state.cache_mt and not found_in_cache and len(translation_output) > 0:
                self.mt_cache.add_translation(cache_embedding, translation_output)

            if progress_cb is not None:
                # Max progress for this part is 80.
                # Min is 50.
                progress_cb(compute_progress(cur_step=(idx + 1), max_steps=len(source_texts), min_value=50, max_value=80))

        return replace_terms_target_side(target_texts, config_state.target_terms)

    def get_source_texts_from_bboxes(
        self,
        rgb_image: Image,
        speech_bboxes,
        forced_image=None,
        return_line_bboxes=False,
        progress_cb=None,
        use_text_line_app=True,
    ):
        source_texts: List[str] = []
        line_bboxes = None
        line_texts = None

        with logger.begin_event("Text recognition"):
            if progress_cb is not None:
                # Max progress for this part is 50.
                # Min is 20.
                on_box_done = lambda box_idx: progress_cb(compute_progress(cur_step=(box_idx + 1), max_steps=len(speech_bboxes), min_value=20, max_value=50))
            else:
                on_box_done = None

            source_texts, line_bboxes, line_texts = self.text_recognition_app.process(
                rgb_image,
                speech_bboxes,
                text_line_app=self.text_line_app.get_sel_app() if use_text_line_app else None,
                # If no lines are found, fallback to scanning the entire cropped image IF that image was cropped by a text detection app.
                text_line_app_scan_image_if_fails=(not self.text_detection_app.get_sel_app_name() == "none" and use_text_line_app),
                forced_image=forced_image,
                on_box_done=on_box_done,
            )

        if return_line_bboxes:
            return source_texts, line_bboxes, line_texts
        return source_texts

    def _detect_in_chunk(self, im_chunk):
        try:
            return self.text_detection_app.begin_process(im_chunk)
        except Exception:
            logger.log('AN ERROR HAS SPAWNED! Ignoring this image...')
            logger.event_exception(ctx=None)
            return []

    def get_bboxes_from_image(self, rgb_image: Image):
        with logger.begin_event("Text detection") as ctx:
            if config_state.tile_width != 100 or config_state.tile_height != 100:
                ctx.log('Splitting image into tiles', tile_width=config_state.tile_width, tile_height=config_state.tile_height)

                speech_bboxes = detect_image_chunks(rgb_image, config_state.tile_width, config_state.tile_height, detect_in_chunk=self._detect_in_chunk)
            else:
                speech_bboxes = self._detect_in_chunk(rgb_image)

        return speech_bboxes
    
    def _translate_image_to_image_from_data(self, source_texts, rgb_image, speech_bboxes, progress_cb=None, return_debug_data=False):
        target_texts = self.get_target_texts_from_str(
            source_texts=source_texts, use_stream=None, progress_cb=progress_cb,
        )
        if progress_cb is not None:
            progress_cb(80)

        # Since most fonts don't work well with weird characters.
        target_texts = [t.replace("―", "-").encode("ascii", "ignore").decode("utf-8") for t in target_texts]

        if config_state.ignore_detect_single_words:
            targets_and_bboxes = zip(target_texts, speech_bboxes)
            puncts = ['.', '!', '?', '-', ')', '"']
            targets_and_bboxes = [t for t in targets_and_bboxes if len(t[0].split(' ')) > 1 or (any(t[0].endswith(pu) for pu in puncts) and len(t[0]) > 1)]

            old_len = len(target_texts)
            target_texts = []
            speech_bboxes = []
            for t, b in targets_and_bboxes:
                target_texts.append(t)
                speech_bboxes.append(b)

            logger.log_message('Ignoring single words', n_before=old_len, n_after=len(target_texts))

        with logger.begin_event("Image cleaning"):
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

        with logger.begin_event("Redrawing"):
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

    def image_to_image(
        self,
        image: Image,
        progress_cb=None,
        return_debug_data=False,
        return_metadata_to_translate_later=False,
    ):
        with logger.begin_event("Image to image") as ctx:

            rgb_image = image.convert("RGB")

            if progress_cb is not None:
                progress_cb(progress=10)

            speech_bboxes = self.get_bboxes_from_image(rgb_image)
            if progress_cb is not None:
                progress_cb(progress=20)

            if debug_state.debug or debug_state.debug_dump_task1:
                # Dump image and detected BBOX coordinates.
                dump_task1_debug_data(rgb_image, speech_bboxes)

            source_texts, line_bboxes, line_texts = self.get_source_texts_from_bboxes(
                rgb_image, speech_bboxes, return_line_bboxes=True, progress_cb=progress_cb,
            )
            source_texts = replace_terms_source_side(source_texts, config_state.source_terms)
            if progress_cb is not None:
                progress_cb(progress=50)

            # This is the only task fn that can merge nearby lines if certain text line model variants are used (YOLO Ex).
            # Task5 merges all texts into one regardless of the model being used.
            special_apps = ["yolo_line_e", "yolo_line_emassive", "dfine_line_emassive"]
            if (
                self.text_line_app.get_sel_app_name() in special_apps
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

            source_texts = pack_context(source_texts, config_state.n_context, ignore_single_words_in_context=False)

            if return_metadata_to_translate_later:
                return {
                    'source_texts': source_texts,
                    'rgb_image': rgb_image,
                    'speech_bboxes': speech_bboxes,
                }
            else:
                return self._translate_image_to_image_from_data(
                    source_texts=source_texts,
                    progress_cb=progress_cb,
                    rgb_image=rgb_image,
                    speech_bboxes=speech_bboxes,
                    return_debug_data=return_debug_data
                )

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

            source_texts = replace_terms_source_side([text], config_state.source_terms)

            target_texts = self.get_target_texts_from_str(
                source_texts, socketio=socketio, use_stream=use_stream
            )

            if return_source_text:
                return target_texts, source_texts
            return target_texts

    def image_to_untranslated_texts(
        self, image: Image, with_text_detect=False, with_ocr=True,
    ):
        with logger.begin_event("Image to untranslated texts") as ctx:
            image = image.convert("RGB")

            # We never want to tile an image here. Tiling is only for task1 (image to image).
            old_tile_width = config_state.tile_width
            old_tile_height = config_state.tile_height
            config_state.tile_width = 100
            config_state.tile_height = 100

            if with_text_detect:
                speech_bboxes = self.get_bboxes_from_image(image)
            else:
                speech_bboxes = create_entire_bbox(image)

            config_state.tile_width = old_tile_width
            config_state.tile_height = old_tile_height

            if with_ocr:
                source_texts = self.get_source_texts_from_bboxes(image, speech_bboxes)
                return source_texts
            else:
                return image, speech_bboxes

    def image_to_single_text(
        self, image: Image, with_text_detect=False, context_input=[], use_stream=None,
    ):
        with logger.begin_event("Image to single text") as ctx:
            image = image.convert("RGB")

            source_texts = self.image_to_untranslated_texts(image, with_text_detect)

            if len(source_texts) == 0:
                return []
            # Task3 assumes that there is only one detected text item to translate, but sometimes there are multiple text items to translate. (Such as the case with DETR-VN).
            # How do we handle this? Simple! After text recognition, combine all of the recognized text into one unit and translate it all together.
            source_texts = merge_texts(source_texts, context_input)

            source_texts = replace_terms_source_side([source_texts], config_state.source_terms)
            source_texts = source_texts[0]

            target_texts = self.get_target_texts_from_str(
                [source_texts], use_stream=use_stream
            )

            return target_texts, source_texts

    def image_to_line_texts(
        self, image: Image, use_stream=None, bottom_n_lines=0,
    ):
        all_targets = []

        with logger.begin_event("Image to line texts") as ctx:
            image = image.convert("RGB")

            # No text detection app is used - only the line detection app.

            # Line app .get_images() also handles any custom sorting logic.
            line_bboxes = self.text_line_app.get_sel_app().get_images(image, return_image_if_fails=True).tolist()

            line_rows = get_bottom_rows(boxes=line_bboxes, N=bottom_n_lines)

            for row in line_rows:
                # TODO: Add batch for full images (not just lines)?
                line_texts = self.get_source_texts_from_bboxes(image, row, use_text_line_app=False)
                line_texts = "".join(line_texts)

                source_texts = merge_texts(line_texts, [])

                source_texts = replace_terms_source_side([source_texts], config_state.source_terms)
                source_texts = source_texts[0]

                target_texts = self.get_target_texts_from_str(
                    [source_texts], use_stream=use_stream
                )

                if use_stream is not None:
                    # In case we're translating line-by-line.
                    use_stream.put("\n\n", already_detokenized=True)

                # Assuming there's no context needed for this task (since it's used for system UI stuff).
                all_targets.append(target_texts[0])

        return ["\n\n".join(all_targets)], "<LINES>"
