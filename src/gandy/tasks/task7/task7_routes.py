from flask import request
from gandy.app import app, translate_pipeline, socketio
from gandy.utils.fancy_logger import logger

# Task7 - translate text into text (from a query parameter. Context must be provided by user).
# This can probably be used for Unity.AutoTranslator - need further testing. TODO
# Note that "from" and "to" args are unused here - load the desired language model pipeline before executing this route.


@app.route("/processtask7", methods=["GET"])
@app.route("/translate", methods=["GET"])
def process_task7_route():
    with logger.begin_event("Task7") as ctx:
        try:
            text = request.args.get("text")

            (
                new_text,
                processed_source_text,
            ) = translate_pipeline.text_to_text(
                text,
                use_stream=None,
                return_source_text=True,
            )

            output = {
                "text": new_text,
                "sourceText": text,
            }
            socketio.patched_emit("done_translating_generic", output)

            return new_text[0], 200
        except Exception:
            logger.log("Task7 Error")
            logger.event_exception(ctx)

            return 'ERROR (search logs for "Task7 Error")', 201
