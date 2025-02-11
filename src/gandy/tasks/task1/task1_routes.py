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
from gandy.tasks.task1.smart_vertical_merging import smart_vertical_merging

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
    on_image_done = None,
):
    with logger.begin_event("Task1") as ctx:
        try:
            image_streams = []
            image_names = []

            # Auto tiling "deprecated". It's not ideal in most cases.
            is_auto_tiling = config_state.tile_width == 0 and config_state.tile_height == 0

            old_tile_width = None
            old_tile_height = None

            is_vert_splitting = config_state.tile_height == 0
            is_doing_vertical_merging = config_state.tile_height == -1 or is_vert_splitting
            if is_vert_splitting:
                ctx.log('Vertical splitting enabled.')

            # Only used for auto tiling, which cannot be activated by the user anymore.
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

            if is_vert_splitting:
                new_images_data = []
                vert_split_idx = 0

                for img_idx, (img, img_name) in enumerate(images_data):
                    chunk_hei = img.width * 3

                    for img_ycoord in range(0, img.height, chunk_hei):
                        img_split = img.crop((0, img_ycoord, img.width, min(img_ycoord + chunk_hei, img.height)))
                        if img_split.height <= 40:
                            continue

                        new_images_data.append([img_split, f"{vert_split_idx}"])

                        ctx.log(f'Vertical splitting image', original_image_name=img_name, new_image_name=vert_split_idx)

                        vert_split_idx += 1

                images_data = new_images_data

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

            if is_doing_vertical_merging and len(images_data) > 1:
                ctx.log('Auto vertical merging enabled.')
                socketio.patched_emit("progress_task1", 2)
                socketio.sleep()

                old_tile_width = config_state.tile_width
                old_tile_height = config_state.tile_height

                config_state.tile_width = 100
                config_state.tile_height = 100

                new_images = smart_vertical_merging([i[0] for i in images_data], detect_in_chunk=translate_pipeline._detect_in_chunk)
                ctx.log('Auto vertical merging done with new images.', old_image_count=len(images_data), new_image_count=len(new_images))
                images_data = images_data[:len(new_images)]
                for idx in range(len(images_data)):
                    # images_data[idx][0] = new_images[idx]
                    images_data[idx] = [new_images[idx], images_data[idx][1]]

            for img_idx, (img, img_name) in enumerate(images_data):
                if debug_state.debug or debug_state.debug_redraw:
                    debug_state.metadata['cur_img_name'] = img_name

                # The client really only uses progress for task1 anyways. The other progress_tasks aren't used... yet.
                socketio.patched_emit("progress_task1", 5)
                socketio.sleep()

                ctx.log(f"Task1 processing image", img_name=img_name)
                progress_cb = lambda progress: on_progress(progress, socketio)

                with logger.begin_event('Process image'):
                    new_image, is_amg = translate_pipeline.image_to_image(
                        img, progress_cb=progress_cb
                    )

                img_name_no_ext = os.path.splitext(img_name)[0]

                if on_image_done is None:
                    with logger.begin_event('Base64 encode image'):
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
                            "remainingImages": len(images_data) - (1 + img_idx)
                        },
                    )
                    socketio.sleep()
                else:
                    if not is_amg: # AMG not supported for on_image_done.
                        on_image_done(new_image, img_idx, img_name_no_ext)

            socketio.patched_emit("done_translating_task1", { "taskId": task_id, })
            socketio.sleep()
        except Exception:
            logger.event_exception(ctx)

            socketio.patched_emit("done_translating_task1", { "taskId": task_id, })
            socketio.sleep()

        if (is_auto_tiling or is_doing_vertical_merging) and (old_tile_width is not None and old_tile_height is not None):
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
