from gandy.utils.fancy_logger import logger
from datetime import timedelta
from typing import List
from gandy.tasks.task5.a_is_close_substring_of_b import a_is_close_substring_of_b
from gandy.utils.cosine_sim import cos_sim
from gandy.full_pipelines.advanced_pipeline import AdvancedPipeline

USE_HEURISTICS = True

USE_MT_EMBEDDINGS = True
EMB_THR = 0.9

def set_neighboring_similar_texts(app_container: AdvancedPipeline, frame_source_texts: List[str], every_secs: float, fps: float, total_frames: float, mt_progress_callback):
    """
    Note that this mutates the frame_source_texts input in-place: Nothing is returned in this function.
    """

    ### Use simple heuristics - no deep learning magick here.
    if USE_HEURISTICS:
        for i in reversed(range(len(frame_source_texts))):
            if i == 0:
                break

            seconds_state = i * every_secs
            at_frame = (seconds_state) * fps
            timestamp = str(timedelta(seconds=seconds_state))

            prev = frame_source_texts[i - 1]
            cur = frame_source_texts[i]

            # TODO: Second cond might be wonky on some videos...
            is_close = a_is_close_substring_of_b(a=prev, b=cur) or a_is_close_substring_of_b(a=cur, b=prev, a_after_b=True)

            with logger.begin_event(
                "Checking if previous frame text is similar to next frame with heuristics",
                seconds=seconds_state,
                hms=timestamp,
            ) as ctx:
                if is_close:
                    ctx.log("Is similar", prev=prev, cur=cur)
                    frame_source_texts[i - 1] = cur
                else:
                    ctx.log("Is not similar", prev=prev, cur=cur)

            if not USE_MT_EMBEDDINGS:
                mt_progress_callback((1 / 3) + ((at_frame / total_frames) / 3))

    ### Use MT embeddings for similarity.
    if USE_MT_EMBEDDINGS:
        for i in reversed(range(len(frame_source_texts))):
            if i == 0:
                break

            seconds_state = i * every_secs
            at_frame = (seconds_state) * fps
            timestamp = str(timedelta(seconds=seconds_state))

            prev = frame_source_texts[i - 1]
            cur = frame_source_texts[i]

            if prev == cur or prev is None or cur is None or len(prev) == 0 or len(cur) == 0:
                continue

            a = app_container.embed_text(prev)
            b = app_container.embed_text(cur)
            cos_score = cos_sim(a, b).item()
            is_close = cos_score >= EMB_THR

            with logger.begin_event(
                "Checking if previous frame text is similar to next frame with AI",
                seconds=seconds_state,
                hms=timestamp,
            ) as ctx:
                if is_close:
                    ctx.log("Is similar", prev=prev, cur=cur, cos_score=cos_score)
                    frame_source_texts[i - 1] = cur
                else:
                    ctx.log("Is not similar", prev=prev, cur=cur, cos_score=cos_score)

            mt_progress_callback((1 / 3) + ((at_frame / total_frames) / 3))
