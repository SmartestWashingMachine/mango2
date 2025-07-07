from gandy.state.context_state import context_state
from gandy.state.config_state import config_state
from gandy.utils.fancy_logger import logger


def push_to_state(last_source: str, new_texts, box_id):
    if last_source == "<LINES>":
        # From text line model. Ignore it.
        return

    context_state.update_source_list(
        last_source,
        config_state.n_context,
    )
    logger.debug(f"Task3 is updating server-side context with item: {last_source}")

    context_state.update_target_list(
        new_texts[-1],
        config_state.n_context,
    )


def get_context(box_id):
    return context_state.prev_source_text_list
