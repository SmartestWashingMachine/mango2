from flask import request

from gandy.app import app, translate_pipeline
from gandy.tricks.translate_web import translate_web


@app.route("/processweb", methods=["POST"])
def process_web_route():
    data = request.json

    web_link = data["weblink"]

    do_preview = data["do_preview"]

    content_filter = data["content_filter"] if len(data["content_filter"]) > 0 else None

    translated_text = translate_web(
        web_link,
        translate_pipeline,
        content_filter=content_filter,
        do_preview=do_preview,
    )

    return {"output": translated_text}, 202
