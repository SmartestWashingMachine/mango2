from gandy.utils.fancy_logger import logger
from datetime import timedelta
from typing import List
from gandy.tasks.task5.a_is_close_substring_of_b import a_is_close_substring_of_b

def set_neighboring_similar_texts(frame_source_texts: List[str], every_secs: float, fps: float, total_frames: float, mt_progress_callback):
    """
    Note that this mutates the frame_source_texts input in-place: Nothing is returned in this function.
    """

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