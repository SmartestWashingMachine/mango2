import os
from gandy.full_pipelines.advanced_pipeline import AdvancedPipeline
from gandy.tasks.task5.subtitle_maker import SubtitleMaker, TranslatedSegment
from gandy.tasks.task5.video_burner import burn_subs
from gandy.tasks.task5.generate_images import generate_images
from gandy.tasks.task5.get_fps import get_fps
from PIL import Image
import tempfile
import regex as re
from gandy.utils.text_processing import merge_texts
from gandy.state.video_state import make_image_cache, make_translation_cache
from gandy.tasks.task5.image_is_similar import image_is_similar
from gandy.utils.fancy_logger import logger
from gandy.tasks.task5.a_is_close_substring_of_b import a_is_close_substring_of_b
from gandy.tasks.task5.filter_dominant_bbox import filter_dominant_bbox
from datetime import timedelta
from uuid import uuid4

# Only retrieve the one largest box per frame.
ONLY_DOMINANT_BOX = False

context_input = []  # TODO: Possibly use context

save_videos_path = os.path.expanduser("~/Documents/Mango/videos")
save_subtitles_path = os.path.expanduser("~/Documents/Mango/subtitles")


def working_path(p: str, abs=False):
    ## FFMPeg needs paths in a specific format (at least for parsing subtitles).
    norm = os.path.normpath(p)
    norm = re.sub(r"\\+", r"/", norm)

    return norm


def make_folder(folder_path: str):
    os.makedirs(folder_path, exist_ok=True)


def save_srt(srt_content: str, out_path: str):
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(srt_content)


def get_n_from_list(l, n=10):
    if len(l) <= n:
        return l
    return l[-n:]


def get_source_text_from_frame(
    app_container: AdvancedPipeline, image: Image.Image, cache, ctx, seconds_state
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
    else:
        source_texts = app_container.get_source_texts_from_bboxes(
            rgb_image, speech_bboxes
        )

    if len(source_texts) == 0:
        ctx.log("No text found in frame")
        return ""

    source_texts = merge_texts(source_texts, context_input)

    cache.push("images", transformed_image)
    cache.push("source_texts", source_texts)
    cache.push("cropped_images", transformed_cropped_image)
    cache.push("seconds", seconds_state)  # For logging.

    return source_texts  # str


def translate_text_from_frame(
    app_container: AdvancedPipeline, fst: str, ctx, cache, seconds_state
):
    existing_index = next(
        (idx for (idx, other) in cache.enumerate("source_texts") if fst == other), None
    )
    if existing_index is not None:
        # Same text as in a previous frame (actually, it might be due to the "next" frame - see STAGE 2 with the reverse loop). Return it.
        t_text = cache.index("target_texts", existing_index)
        ctx.log(
            "Found similar source text in cache",
            source_text=fst,
            target_text=t_text,
            similar_source_text=cache.index("source_texts", existing_index),
        )
        return t_text
    ctx.log(
        "Could not find similar source text in cache",
        source_text=fst,
        last_cached=get_n_from_list(cache.data["source_texts"]),
    )

    if len(fst) > 0:
        target_texts = app_container.get_target_texts_from_str(
            [fst],
            use_stream=None,
        )
    else:
        target_texts = [""]

    if len(target_texts) > 0:
        translated_text = target_texts[0]
    else:
        translated_text = None

    cache.push("source_texts", fst)
    cache.push("target_texts", translated_text)
    cache.push("seconds", seconds_state)  # For logging.

    ctx.log("Adding to translation cache", source_text=fst, target_text=translated_text)

    return translated_text


def postprocess_translated_text(t: str):
    # Some characters in certain sequences can not be rendered. Weird SRT logic? FFMPEG parsing error? Who knows!
    # Texts in the form "<abc>: def" are burned as ": def" - a simple naive fix is to replace < with [ and > with ].
    return t.replace("<", "[").replace(">", "]")


def process_task5(
    app_container: AdvancedPipeline,
    video_file_path: str,
    mt_progress_callback,
    burn_progress_callback,
    every_secs=2,
):
    """
    Adds text captions to an image.
    """
    make_folder(save_subtitles_path)
    make_folder(save_videos_path)

    segments = []

    image_cache = make_image_cache()
    translation_cache = make_translation_cache()

    fps, video_duration_seconds = get_fps(
        video_file_path, return_duration_in_seconds=True
    )

    total_frames = fps * video_duration_seconds

    with tempfile.TemporaryDirectory() as tmp_dir:
        frame_image_paths = generate_images(
            video_file_path, tmp_dir, every_secs=every_secs
        )

        frame_source_texts = []

        ## STAGE 1: Detect and OCR regions.
        for idx, frame_path in enumerate(frame_image_paths):
            seconds_state = idx * every_secs
            at_frame = (seconds_state) * fps
            timestamp = str(timedelta(seconds=seconds_state))

            with logger.begin_event(
                "Finding source text in frame", seconds=seconds_state, hms=timestamp
            ) as ctx:
                image = Image.open(frame_path).convert("RGB")

                source_text = get_source_text_from_frame(
                    app_container, image, image_cache, ctx, seconds_state
                )
                frame_source_texts.append(source_text)

            mt_progress_callback((at_frame / total_frames) / 3)

        ## STAGE 2: Reverse loop to find neighboring frames with similar texts.
        for i in reversed(range(len(frame_image_paths))):
            if i == 0:
                break

            seconds_state = i * every_secs
            at_frame = (seconds_state) * fps
            timestamp = str(timedelta(seconds=seconds_state))

            prev = frame_source_texts[i - 1]
            cur = frame_source_texts[i]

            is_close = a_is_close_substring_of_b(a=prev, b=cur)
            with logger.begin_event(
                "Checking if previous frame text is similar to next frame",
                seconds=seconds_state,
                hms=timestamp,
            ) as ctx:
                if is_close:
                    ctx.log("Is similar", prev=prev, cur=cur)
                    frame_source_texts[i - 1] = cur
                else:
                    ctx.log("Is not similar", prev=prev, cur=cur)

            mt_progress_callback((1 / 3) + ((at_frame / total_frames) / 3))

        ## STAGE 3: Translate each frame.
        for idx, fst in enumerate(frame_source_texts):
            seconds_state = idx * every_secs
            at_frame = (seconds_state) * fps
            timestamp = str(timedelta(seconds=seconds_state))

            with logger.begin_event(
                "Translating source text in frame", seconds=seconds_state, hms=timestamp
            ) as ctx:
                translated_text = translate_text_from_frame(
                    app_container, fst, ctx, translation_cache, seconds_state
                )

                if translated_text is not None and len(translated_text) > 0:
                    translated_text = postprocess_translated_text(translated_text)
                    segments.append(
                        TranslatedSegment(text=translated_text, at_frame=at_frame)
                    )

                ctx.log("Final outcome", text=translated_text)

            mt_progress_callback((2 / 3) + ((at_frame / total_frames) / 3))

    if len(segments) == 0:
        raise RuntimeError("No text detected in video.")

    video_stride = every_secs * fps
    maker = SubtitleMaker(video_fps=fps, sub_duration=video_stride)

    file_name = os.path.basename(os.path.splitext(video_file_path)[0])

    srt_path = f"{save_subtitles_path}/{file_name}.srt"
    srt_content = maker.create_srt_content(segments)

    save_srt(srt_content, out_path=srt_path)

    out_video_path = f"{save_videos_path}/{file_name}.mp4"
    burn_subs(
        working_path(srt_path, abs=True),
        working_path(video_file_path),
        out_path=working_path(out_video_path, abs=True),
        video_duration_seconds=video_duration_seconds,
        progress_callback=burn_progress_callback,
    )

    return out_video_path
