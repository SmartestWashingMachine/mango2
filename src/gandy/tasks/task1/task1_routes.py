from flask import request
from PIL import Image
from io import BytesIO
import base64
import os
from gandy.utils.natsort import natsort
from gandy.app import app, translate_pipeline, socketio
from gandy.utils.fancy_logger import logger
from gandy.state.debug_state import debug_state

# Task1 - translate images into images.


def encode_image(new_image):
    buffer = BytesIO()
    # Poor quality: new_image.save(buffer, format="JPEG")
    new_image.save(buffer, format="PNG")
    new_image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return new_image_base64


def on_progress(progress: int, socketio):
    socketio.patched_emit(f"progress_task1", progress)
    socketio.sleep()


def translate_task1_background_job(
    images,
):
    with logger.begin_event("Task1") as ctx:
        try:
            image_streams = []
            image_names = []

            # List all files.
            for idx, img_file in enumerate(images):
                img = Image.open(img_file)
                img.load()

                image_streams.append(img)

                try:
                    if img_file.filename == "" or img_file.filename is None:
                        image_names.append(f"{idx}")
                    else:
                        image_names.append(img_file.filename)
                except:
                    image_names.append(f"{idx}")

            images_data = list(zip(image_streams, image_names))
            images_data = sorted(images_data, key=lambda tup: natsort(tup[1]))

            for img, img_name in images_data:
                if debug_state.debug:
                    debug_state.metadata['cur_img_name'] = img_name

                # The client really only uses progress for task1 anyways. The other progress_tasks aren't used... yet.
                socketio.patched_emit("progress_task1", 5)
                socketio.sleep()

                ctx.log(f"Task1 processing image", img_name=img_name)
                progress_cb = lambda progress: on_progress(progress, socketio)
                new_image, is_amg = translate_pipeline.image_to_image(
                    img, progress_cb=progress_cb
                )

                img_name_no_ext = os.path.splitext(img_name)[0]

                if is_amg:
                    new_image_base64 = encode_image(new_image["image"])
                    annotations = new_image["annotations"]

                    new_img_name = f"{img_name_no_ext}.amg"
                else:
                    new_image_base64 = encode_image(new_image)
                    annotations = []

                    new_img_name = f"{img_name_no_ext}.png"

                socketio.patched_emit(
                    "item_task1",
                    {
                        "image": new_image_base64,
                        "imageName": new_img_name,
                        "annotations": annotations,
                    },
                )
                socketio.sleep()

            socketio.patched_emit("done_translating_task1", {})
            socketio.sleep()
        except Exception:
            logger.event_exception(ctx)

            socketio.patched_emit("done_translating_task1", {})
            socketio.sleep()


@app.route("/processtask1", methods=["POST"])
def process_task1_route():
    images = request.files.getlist("file")
    socketio.start_background_task(
        translate_task1_background_job,
        images,
    )

    return {"processing": True}, 202
