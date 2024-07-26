from flask import request
from gandy.tasks.task2.box_context_state_utils import (
    use_context_state_for_box,
    update_context_state_for_box,
)
from gandy.app import app, translate_pipeline, socketio
from gandy.utils.socket_stream import SocketStreamer
from gandy.utils.fancy_logger import logger

# Task2 - translate text into text (from the OCR box or the text field input or e-books).


def translate_task2_background_job(
    text,
    box_id=None,
    use_stream=None,
):
    with logger.begin_event("Task2") as ctx:
        output = {
            "text": "",
            "sourceText": text,
            "boxId": box_id,
        }

        if box_id is not None:
            # Hacky for now. For OCR boxes. TODO
            # This is only used for clipboard copying on the frontend with the OCR box (normal OCR box method is task3).
            # Context is stored on the server FOR NOW.
            text = use_context_state_for_box(text, box_id, ctx=ctx)

        try:
            (
                new_text,
                processed_source_text,
            ) = translate_pipeline.text_to_text(
                text,
                use_stream=use_stream,
                return_source_text=True,
            )

            output["text"] = new_text

            if box_id is not None:
                update_context_state_for_box(
                    new_text[0], processed_source_text[0], box_id
                )

            socketio.patched_emit("done_translating_task2", output)
        except Exception:
            logger.event_exception(ctx)

            socketio.patched_emit("done_translating_task2", {})


@app.route("/processtask2", methods=["POST"])
def process_task2_route():
    data = request.json
    text = data["text"]
    box_id = data["boxId"] if "boxId" in data else None

    use_stream = data["useStream"] if "useStream" in data else None
    if use_stream:
        use_stream = SocketStreamer(box_id=box_id)
    else:
        use_stream = None

    socketio.start_background_task(
        translate_task2_background_job,
        text,
        box_id,
        use_stream,
    )

    return {"processing": True}, 202
