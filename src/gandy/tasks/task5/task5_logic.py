import os
from gandy.full_pipelines.advanced_pipeline import AdvancedPipeline
from gandy.tasks.task5.subtitle_maker import SubtitleMaker, TranslatedSegment
from gandy.tasks.task5.video_burner import burn_subs
from gandy.tasks.task5.generate_images import generate_images
from gandy.tasks.task5.get_fps import get_fps
from PIL import Image
import tempfile
import regex as re

from gandy.state.video_state import make_image_cache, make_translation_cache

from gandy.utils.fancy_logger import logger
from gandy.tasks.task5.a_is_close_substring_of_b import a_is_close_substring_of_b

from gandy.tasks.task5.stages.read_text_in_frames import read_text_in_frames
from gandy.tasks.task5.stages.set_neighboring_similar_texts import set_neighboring_similar_texts
from gandy.tasks.task5.stages.translate_text_in_frames import translate_text_in_frames

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
        frame_source_texts = read_text_in_frames(app_container, frame_image_paths, every_secs, fps, total_frames, mt_progress_callback)

        ## STAGE 2: Reverse loop to find neighboring frames with similar texts.
        # This mutates in-place.
        set_neighboring_similar_texts(frame_source_texts, every_secs, fps, total_frames, mt_progress_callback)

        ## STAGE 3: Translate each frame.
        segments = translate_text_in_frames(app_container, frame_source_texts, every_secs, fps, total_frames, mt_progress_callback)

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
