from gandy.tasks.task5.subtitle_maker import TranslatedSegment
from gandy.state.video_state import make_image_cache, BasicCache
from gandy.utils.fancy_logger import logger
from datetime import timedelta
from typing import List
from gandy.full_pipelines.advanced_pipeline import AdvancedPipeline
from PIL import Image
from gandy.tasks.task5.image_is_similar import image_is_similar
from gandy.tasks.task5.filter_dominant_bbox import filter_dominant_bbox
from gandy.utils.text_processing import merge_texts
from gandy.utils.clean_text_v2 import clean_text_vq

# TODO: Possibly use context
context_input = []

# Only retrieve the one largest box per frame.
# This is just used for certain internal debugging purposes.
ONLY_DOMINANT_BOX = False

def _get_source_text_from_frame(
    app_container: AdvancedPipeline, image: Image.Image, cache: BasicCache, ctx, seconds_state
):
    existing_index, transformed_image = image_is_similar(
        image,
        cache.iterate("images"),
        log_message="Checking if similar frame exists in cache",
        threshold=0,
    )
    transformed_cropped_image = None

    if existing_index is not None:
        # Same entire image as before. Return it.
        t_text = cache.index("source_texts", existing_index)
        ctx.log(
            "Found similar frame image in cache",
            source_text=t_text,
            seconds=cache.index("seconds", existing_index),
        )
        return t_text

    # We only text detect if no similar whole image was found.
    rgb_image, speech_bboxes = app_container.image_to_untranslated_texts(
        image, with_text_detect=True, with_ocr=False
    )

    if ONLY_DOMINANT_BOX:
        speech_bboxes = filter_dominant_bbox(speech_bboxes)

    if len(speech_bboxes) == 1:
        cropped_image = rgb_image.crop(speech_bboxes[0])

        if app_container.text_detection_app.get_sel_app_name() != "none":
            existing_index, transformed_cropped_image = image_is_similar(
                cropped_image,
                cache.iterate("cropped_images"),
                log_message="Checking if similar text region exists in cache",
                mode="text_region",
            )
            if existing_index is not None:
                t_text = cache.index("source_texts", existing_index)
                # Same text region image as before. Return it.
                ctx.log(
                    "Found similar text region image in cache",
                    source_text=t_text,
                    seconds=cache.index("seconds", existing_index),
                )
                return t_text
        else:
            transformed_cropped_image = None

        # We only OCR if no similar text region image was found.
        source_texts = app_container.get_source_texts_from_bboxes(
            rgb_image, speech_bboxes, forced_image=cropped_image
        )
    elif len(speech_bboxes) > 0:
        source_texts = app_container.get_source_texts_from_bboxes(
            rgb_image, speech_bboxes
        )
    else:
        # No texts found in frame.
        source_texts = []

    if len(source_texts) == 0:
        ctx.log("No text found in frame")
        return ""

    source_texts = merge_texts(source_texts, context_input)

    cache.push("images", transformed_image)
    cache.push("source_texts", source_texts)
    cache.push("cropped_images", transformed_cropped_image)
    cache.push("seconds", seconds_state)  # For logging.

    return source_texts  # str

def read_text_in_frames(app_container: AdvancedPipeline, frame_image_paths: List[str], every_secs: float, fps: float, total_frames: float, mt_progress_callback):
    frame_source_texts: List[str] = []

    image_cache = make_image_cache()

    for idx, frame_path in enumerate(frame_image_paths):
        seconds_state = idx * every_secs
        at_frame = (seconds_state) * fps
        timestamp = str(timedelta(seconds=seconds_state))

        with logger.begin_event(
            "Finding source text in frame", seconds=seconds_state, hms=timestamp
        ) as ctx:
            image = Image.open(frame_path).convert("RGB")

            source_text = _get_source_text_from_frame(
                app_container, image, image_cache, ctx, seconds_state
            )

            # All MT models use clean_text_vq. There's no harm in normalizing twice (once here, once in MT).
            # But it is somewhat inefficient to normalize twice...
            # Why do we need this? Because the OCR model sometimes makes mistakes.
            source_text = clean_text_vq(source_text)

            frame_source_texts.append(source_text)

        mt_progress_callback((at_frame / total_frames) / 3)

    return frame_source_texts
