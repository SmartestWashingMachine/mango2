from flask import request
import logging
from gandy.tricks.translate_epub import translate_epub
from gandy.app import app, translate_pipeline, socketio
from gandy.utils.fancy_logger import logger


def process_task2_book_background_job(file, output_html = False):
    translate_epub(
        file,
        translate_pipeline,
        checkpoint_every_pages=1,
        socketio=socketio,
        output_html=output_html,
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

        data = request.form.to_dict(flat=False)

        output_html = data["outputHtml"][0] == "on"

    socketio.start_background_task(
        process_task2_book_background_job,
        file,
        output_html
    )

    return {"processing": True}, 202
