from flask import request
from gandy.app import app, translate_pipeline, socketio
from gandy.utils.socket_stream import SocketStreamer
from gandy.utils.fancy_logger import logger

# Task2 - refine translation from a user query (from the OCR box). Only used with the "Escalator" model variant.


def translate_task6_background_job(
    source_text,
    target_text,
    box_id=None,
    use_stream=None,
):
    with logger.begin_event("Task6") as ctx:
        output = {
            "text": "",
            "boxId": box_id,
        }

        try:
            new_text = translate_pipeline.correct_translation(
                source_text,
                target_text,
                use_stream=use_stream,
            )

            output["text"] = new_text

            socketio.patched_emit(
                "done_translating_task2",
                output,
            )  # Keep this at task2 to make it easier for the client WSS
        except Exception:
            logger.event_exception(ctx)

            socketio.patched_emit(
                "done_translating_task2",
                {},
            )


@app.route("/processtask6", methods=["POST"])
def process_task6_route():
    data = request.json
    box_id = data["boxId"] if "boxId" in data else None

    use_stream = data["useStream"] if "useStream" in data else None
    if use_stream:
        use_stream = SocketStreamer(box_id=box_id)
    else:
        use_stream = None

    socketio.start_background_task(
        translate_task6_background_job,
        data["sourceText"],
        data["targetText"],
        box_id,
        use_stream,
    )

    return {"processing": True}, 202
