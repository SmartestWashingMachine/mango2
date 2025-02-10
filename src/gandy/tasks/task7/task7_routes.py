from flask import request
from gandy.app import app, translate_pipeline, socketio
from gandy.utils.fancy_logger import logger
from gandy.state.config_state import config_state
from uuid import uuid4
from gandy.utils.socket_stream import SocketStreamer

# Task7 - translate text into text (from a query parameter. Context must be provided by user).
# This can probably be used for Unity.AutoTranslator - need further testing. TODO
# Note that "from" and "to" args are unused here - load the desired language model pipeline before executing this route.


@app.route("/processtask7", methods=["GET"])
@app.route("/translate", methods=["GET"])
def process_task7_route():
    with logger.begin_event("Task7") as ctx:
        try:
            text = request.args.get("text")

            generic_id = uuid4().hex
            metadata = {"genericId": generic_id, }

            use_stream = SocketStreamer(box_id="", metadata=metadata) if config_state.num_beams == 1 else None

            (
                new_text,
                processed_source_text,
            ) = translate_pipeline.text_to_text(
                text,
                use_stream=use_stream,
                return_source_text=True,
            )

            # Send one final update.
            data_to_send = {
                "text": new_text[0],
                "boxId": "",
                "sourceText": processed_source_text[0],
                **metadata,
            }
            socketio.patched_emit(
                "item_stream",
                data_to_send,
            )
            socketio.sleep()

            return new_text[0], 200
        except Exception:
            logger.log("Task7 Error")
            logger.event_exception(ctx)

            return 'ERROR (search logs for "Task7 Error")', 201
