from gandy.utils.fancy_logger import logger
from datetime import timedelta
from typing import List
from gandy.tasks.task5.a_is_close_substring_of_b import a_is_close_substring_of_b
from gandy.utils.cosine_sim import cos_sim
from gandy.full_pipelines.advanced_pipeline import AdvancedPipeline
from gandy.state.config_state import config_state
import regex as re

USE_HEURISTICS = True

USE_MT_EMBEDDINGS = True
EMB_THR = 0.85 # Used to be 0.9.

# NOTE: Maybe adding the dots (.) is a bad idea.
def strip_punct(s: str):
    s = re.sub(r']|\"|\.|!|\?|,|\)|\(|\[', '', s)
    s = re.sub(' +', ' ', s)
    return s

def set_neighboring_similar_texts(app_container: AdvancedPipeline, frame_source_texts: List[str], every_secs: float, fps: float, total_frames: float, mt_progress_callback):
    """
    Note that this mutates the frame_source_texts input in-place: Nothing is returned in this function.
    """

    ### Use simple heuristics - no deep learning magick here.
    if USE_HEURISTICS:
        prog_marker = 0

        for i in reversed(range(len(frame_source_texts))):
            if i == 0:
                break

            seconds_state = i * every_secs
            timestamp = str(timedelta(seconds=seconds_state))

            prog_marker += 1
            at_frame = (prog_marker * every_secs) * fps

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

    prev_embs = [] # list of tuple (str TEXT, tensor EMBED)

    def _get_from_prev_embs(t: str):
        for p in prev_embs:
            if p[0] == t:
                return p[1]
            
        return None

    def _add_to_prev_embs(prev_embs, t: str, emb):
        prev_embs.append((t, emb))

        if len(prev_embs) > 10:
            prev_embs = prev_embs[1:]

        return prev_embs

    if USE_MT_EMBEDDINGS and not config_state.use_translation_server:
        prog_marker = 0

        for i in reversed(range(len(frame_source_texts))):
            if i == 0:
                break

            seconds_state = i * every_secs
            timestamp = str(timedelta(seconds=seconds_state))

            prog_marker += 1
            at_frame = (prog_marker * every_secs) * fps

            prev = frame_source_texts[i - 1]
            cur = frame_source_texts[i]

            if prev == cur or prev is None or cur is None or len(prev) == 0 or len(cur) == 0:
                continue

            prev_emb = _get_from_prev_embs(strip_punct(prev))
            cur_emb = _get_from_prev_embs(strip_punct(cur))
            if prev_emb is None:
                prev_emb = app_container.embed_text(prev)
            if cur_emb is None:
                cur_emb = app_container.embed_text(cur)

            prev_embs = _add_to_prev_embs(prev_embs, prev, prev_emb)
            prev_embs = _add_to_prev_embs(prev_embs, cur, cur_emb)

            cos_score = cos_sim(prev_emb, cur_emb).item()

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
