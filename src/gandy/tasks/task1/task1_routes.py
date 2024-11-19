from flask import request
from PIL import Image
from io import BytesIO
import base64
import os
from gandy.utils.natsort import natsort
from gandy.app import app, translate_pipeline, socketio
from gandy.utils.fancy_logger import logger
from gandy.state.debug_state import debug_state
from gandy.state.config_state import config_state
from gandy.tasks.task1.stitch_images_together import stack_horizontally, stack_vertically

# Task1 - translate images into images.

# From: https://stackoverflow.com/questions/24101524/finding-median-of-list-in-python
def median(lst):
    sortedLst = sorted(lst)
    lstLen = len(lst)
    index = (lstLen - 1) // 2

    if (lstLen % 2):
        return sortedLst[index]
    else:
        return (sortedLst[index] + sortedLst[index + 1]) / 2.0


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
    task_id: str,
):
    with logger.begin_event("Task1") as ctx:
        try:
            image_streams = []
            image_names = []

            is_auto_tiling = config_state.tile_width == 0 or config_state.tile_height == 0

            image_widths = []
            image_heights = []

            # List all files.
            for idx, img_file in enumerate(images):
                img = Image.open(img_file)
                img.load()

                image_widths.append(img.width)
                image_heights.append(img.height)

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

            if is_auto_tiling and len(images_data) > 1:
                old_tile_width = config_state.tile_width
                old_tile_height = config_state.tile_height

                avg_width = sum(image_widths) / len(images_data)
                avg_height = sum(image_heights) / len(images_data)
                if avg_height > avg_width:
                    # Images are likely long in the vertical dimension. Tile them top to bottom.
                    config_state.tile_width = 100
                    config_state.tile_height = (median(image_heights) / sum(image_heights)) * 100

                    images_data = [[stack_vertically([i[0] for i in images_data]), images_data[0][1]]]
                else:
                    # Images are likely long in the horizontal dimension. This should never happen though...
                    config_state.tile_width = (median(image_widths) / sum(image_widths)) * 100
                    config_state.tile_height = 100

                    images_data = [[stack_horizontally(images_data), images_data[0][1]]]

                ctx.log('Auto tile mode enabled.', computed_tile_width=config_state.tile_width, computed_tile_height=config_state.tile_height)

            for img, img_name in images_data:
                if debug_state.debug or debug_state.debug_redraw:
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
                        "taskId": task_id,
                    },
                )
                socketio.sleep()

            socketio.patched_emit("done_translating_task1", { "taskId": task_id, })
            socketio.sleep()
        except Exception:
            logger.event_exception(ctx)

            socketio.patched_emit("done_translating_task1", { "taskId": task_id, })
            socketio.sleep()

        if is_auto_tiling:
            config_state.tile_width = old_tile_width
            config_state.tile_height = old_tile_height


@app.route("/processtask1", methods=["POST"])
def process_task1_route():
    images = request.files.getlist("file")
    task_id = request.form.get('task_id', type=str)

    socketio.start_background_task(
        translate_task1_background_job,
        images,
        task_id,
    )

    return {"processing": True}, 202
