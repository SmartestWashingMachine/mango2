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
from gandy.utils.clean_text_v2 import clean_text_vq
from datetime import timedelta
from uuid import uuid4

"""

I didn't think I would need to write a pseudo design document for this task, but there are a lot of heuristics involved here, so I want to
briefly explain them to anybody - or myself in the future - who's curious on how this task can semi-successfully translate text characters drawn in videos.

-- The overall process is simple:
1. We split the video into frames. Each frame, or every X frames, is an image.
2. We detect text regions in each frame image.
3. We OCR each text region.
4. We translate each OCR'd text region. (Notice that Steps 2/3/4 are similar to Task1 - translating images into text, minus the image cleaning & redrawing part.)
5. We stitch these translations together into an SRT file.
6. We burn the SRT file onto the video itself.

-- Now, there are some issues with this approach. Can you find them?
1. We're detecting *every X frames*
2. We're OCR'ing *every X frames*
3. We're translating *every X frames*
4. What if our text characters are drawn onto the image over time, character-by-character, rather than all at once?

Think of how slow and clunky this approach is! It's really bad if we just built it as-is.
So there's a few more implementation (read: heuristics) details screwed in to help make this task better.

-- Heuristics
1. (For 1/2/3) We cache some of the previous whole-frame images and their outputs. If the next frame is similar to these ones, reuse the outputs already generated there.
    We use image hashing to find similar images quickly. Image hashing tended to produce false positives frequently, so the hashing block size had to be increased greatly.
    Regrettably, a large hashing block size also increased the false negative rate. A better hashing algorihtm would be appreciated.
2. (For 2/3) We cache some of the previous text-region images and their outputs. If the next text-region image is similar, reuse the outputs there.
3. (For 4/3) After detecting and OCR'ing all applicable frames, we do a reverse loop, starting from the final frame to the first.
    This reverse loop is used to fill in any frames that have sentences that are completed by the later frames from (4).
    We define "completed by the later frames", as being similar to the next frame.

-- Areas of Improvement

IMAGE HASHING:

The ideal hashing algorithm must be sensitive to slight structurally different pixel differences,
as the text pixels are rather small in comparison to the entire image.

The ideal hashing algorithm must also be relatively insensitive to spatial differences, such as a person moving a leg.

SIMILAR TEXT STRINGS:

The ideal similarity checker would use less heuristics and still be extremely fast.

One idea would be to use a multilingual sentence embedding model, but would it be fast enough? And it would add another dependency.
Another idea would be to use the encoder outputs from the MT model, but that would be fairly slow.
Another idea would be to use the outputs from the MT encoder embeddings alone. It would not consider context, and may still be somewhat slow.

"""

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
    elif len(source_texts) > 0:
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


def translate_text_from_frame(
    app_container: AdvancedPipeline, fst: str, ctx, cache, seconds_state
):
    existing_index = next(
        (idx for (idx, other) in cache.enumerate("source_texts") if fst == other), None
    )

    # We only translate if a similar text was not already translated.
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

                # All MT models use clean_text_vq. There's no harm in normalizing twice (once here, once in MT).
                # But it is somewhat inefficient to normalize twice...
                # Why do we need this? Because the OCR model sometimes makes mistakes.
                source_text = clean_text_vq(source_text)

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

            # TODO: Second cond might be wonky on some videos...
            is_close = a_is_close_substring_of_b(a=prev, b=cur) or a_is_close_substring_of_b(a=cur, b=prev)
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
