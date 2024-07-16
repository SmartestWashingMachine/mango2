from flask import request
from PIL import Image
from gandy.utils.fancy_logger import logger
from gandy.app import app, translate_pipeline

# Task4 - scan images and give UNTRANSLATED text (from the OCR box).
# This is really only used for getting speaker names before translating text via task2.
# Didn't bother with a websocket here.


def translate_task4(images, box_id=None, with_text_detect=True):
    with logger.begin_event("Task4") as ctx:
        try:
            opened_images = []

            for img_file in images:
                opened_img = Image.open(img_file)
                opened_img.load()
                opened_images.append(opened_img)

            # Notice it stops after the first image. Guess I should refactor the code at some point...
            for img in opened_images:
                ctx.log(
                    f"With some vars",
                    with_text_detect=with_text_detect,
                )

                new_texts = translate_pipeline.image_to_untranslated_texts(
                    img,
                    with_text_detect=with_text_detect,
                )

                return new_texts
        except Exception:
            logger.event_exception(ctx)
            return ""


@app.route("/processtask4", methods=["POST"])
def process_task4_route():
    data = request.form.to_dict(flat=False)
    text_detect = data["textDetect"] if "textDetect" in data else "off"

    # It's an array? Huh? TODO
    with_text_detect = text_detect[0] == "on"

    images = request.files.getlist("file")

    return {"text": translate_task4(images, with_text_detect)}, 202
