from gandy.tasks.task5.subtitle_maker import TranslatedSegment
from gandy.state.video_state import make_translation_cache, BasicCache
from gandy.utils.fancy_logger import logger
from datetime import timedelta
from typing import List
from gandy.full_pipelines.advanced_pipeline import AdvancedPipeline

def _get_n_from_list(l, n=10):
    if len(l) <= n:
        return l
    return l[-n:]

def _translate_text_from_frame(
    app_container: AdvancedPipeline, fst: str, ctx, cache: BasicCache, seconds_state
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
        last_cached=_get_n_from_list(cache.data["source_texts"]),
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

def translate_text_in_frames(app_container: AdvancedPipeline, frame_source_texts: List[str], every_secs: float, fps: float, total_frames: float, mt_progress_callback):
    segments: List[TranslatedSegment] = []

    translation_cache = make_translation_cache()

    for idx, fst in enumerate(frame_source_texts):
        seconds_state = idx * every_secs
        at_frame = (seconds_state) * fps

        timestamp = str(timedelta(seconds=seconds_state))

        with logger.begin_event(
            "Translating source text in frame", seconds=seconds_state, hms=timestamp
        ) as ctx:
            translated_text = _translate_text_from_frame(
                app_container, fst, ctx, translation_cache, seconds_state
            )

            if translated_text is not None and len(translated_text) > 0:
                segments.append(
                    TranslatedSegment(text=translated_text, at_frame=at_frame)
                )

            ctx.log("Final outcome", text=translated_text)

        mt_progress_callback((2 / 3) + ((at_frame / total_frames) / 3))

    return segments