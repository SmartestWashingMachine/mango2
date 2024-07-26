from gandy.utils.fancy_logger import logger
from gandy.state.context_state import context_state
from gandy.state.config_state import config_state
from gandy.app import socketio
from gandy.utils.text_processing import add_seps


def use_context_state_for_box(text: str, box_id, ctx):
    ctx.log(f"Using box context", box_id=box_id)
    text = add_seps(context_state.prev_source_text_list + [text])

    socketio.patched_emit(
        "begin_translating_task2",
        {
            "boxId": box_id,
        },
    )
    socketio.sleep()

    return text


def update_context_state_for_box(target_text: str, source_text: str, box_id):
    if len(target_text) > 0:
        context_state.update_source_list(
            source_text,
            config_state.n_context,
        )

        context_state.update_target_list(
            target_text,
            config_state.n_context,
        )
