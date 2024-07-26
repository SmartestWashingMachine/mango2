from flask import request
import logging
from gandy.tricks.translate_epub import translate_epub
from gandy.app import app, translate_pipeline, socketio
from gandy.utils.fancy_logger import logger


def process_task2_book_background_job(file):
    translate_epub(
        file,
        translate_pipeline,
        checkpoint_every_pages=1,
        socketio=socketio,
    )

    socketio.patched_emit("done_translating_epub", {})


@app.route("/processbookb64", methods=["POST"])
def process_book_route():
    """
    Process an EPUB file.
    """
    with logger.begin_event("Process base64 into book") as ctx:
        if "file" not in request.files or request.files["file"].filename == "":
            ctx.log("No book was sent.")

            return {}, 404

        file = request.files["file"]

    socketio.start_background_task(
        process_task2_book_background_job,
        file,
    )

    return {"processing": True}, 202
