from flask import request
from PIL import Image
from gandy.utils.fancy_logger import logger
from gandy.app import app, translate_pipeline, socketio
from gandy.state.debug_state import debug_state
from gandy.state.config_state import config_state
from gandy.utils.get_sep_regex import get_last_sentence
from gandy.utils.socket_stream import SocketStreamer
from gandy.tasks.task3.task3_box_context_state_utils import push_to_state, get_context
from gandy.tasks.task3.screenshot_window_only import capture_window_image_from_box
from mss import mss
from uuid import uuid4
import os
import base64
from io import BytesIO

# Task3 - translate images into text (from the OCR box).
# Context here is stored on the SERVER rather than the client.
# Why? Because we may be using textract, and this is the best way to keep a state of previous contexts if it comes to that.
# "Servers shouldn't have state!" Yeah but refactoring it is gonna be a pain. Maybe in the future.


def load_images(images):
    opened_images = []

    for img_file in images:
        opened_img = Image.open(img_file)
        opened_img.load()
        opened_images.append(opened_img)

    return opened_images


def emit_begin(box_id):
    socketio.patched_emit(
        "begin_translating_task3",
        {
            "boxId": box_id,
        },
    )
    socketio.sleep()


def translate_task3_background_job(
    images,
    box_id=None,
    with_text_detect=True,
    use_stream=None,
    already_loaded=False,
    translate_lines_individually=0,
):
    with logger.begin_event("Task3", translate_lines_individually=translate_lines_individually) as ctx:
        try:
            if already_loaded:
                opened_images = images
            else:
                opened_images = load_images(images)

            if debug_state.debug or debug_state.debug_dump_task3_ocr:
                for im in opened_images:
                    debug_id = uuid4().hex
                    bpp = os.path.expanduser("~/Documents/Mango/task3debug")
                    os.makedirs(f'{bpp}/task3', exist_ok=True)
                    im.save(f'{bpp}/task3/{debug_id}.png')

            emit_begin(box_id)  # Images must be loaded BEFORE emitting progress.

            context_input = get_context(box_id)

            for img in opened_images:
                ctx.log(
                    f"With some vars",
                    with_text_detect=with_text_detect,
                    context_input=context_input,
                )

                # NOTE: The source texts returned are those BEFORE translation app preprocessing, but after terms are replaced.
                # In other words: A bit stale.
                if translate_lines_individually is not None and translate_lines_individually != 0:
                    new_texts, source_text = translate_pipeline.image_to_line_texts(
                        img,
                        use_stream=use_stream,
                        bottom_n_lines=translate_lines_individually,
                    )
                else:
                    new_texts, source_text = translate_pipeline.image_to_single_text(
                        img,
                        with_text_detect=with_text_detect,
                        context_input=context_input,
                        use_stream=use_stream,
                    )

                last_source = get_last_sentence(source_text)
                push_to_state(last_source, new_texts, box_id)

                output = {
                    "text": new_texts,
                    "boxId": box_id,
                    "sourceText": [last_source],
                }
                socketio.patched_emit(
                    "item_task3",
                    output,
                )

            socketio.patched_emit("done_translating_task3", {})
        except Exception:
            logger.event_exception(ctx)

            socketio.patched_emit("done_translating_task3", {})


@app.route("/processtask3", methods=["POST"])
def process_task3_route():
    data = request.form.to_dict(flat=False)
    box_id = data["boxId"] if "boxId" in data else None
    text_detect = data["textDetect"] if "textDetect" in data else "off"

    use_stream = data["useStream"] if "useStream" in data else "off"

    use_stream = True if use_stream[0] == "on" else None

    if use_stream:
        use_stream = SocketStreamer(box_id=box_id)

    # It's an array? Huh? TODO
    with_text_detect = text_detect[0] == "on"
    if box_id is not None and len(box_id) > 0:
        box_id = box_id[0]

    translate_lines_individually = int(data['translateLinesIndividually'][0])

    images = request.files.getlist("file")

    socketio.start_background_task(
        translate_task3_background_job,
        images,
        box_id,
        with_text_detect,
        use_stream,
        False,
        translate_lines_individually,
    )

    return {"processing": True}, 202

def process_task3_faster(data):
    if data['use_stream']:
        use_stream = SocketStreamer(box_id=data['box_id'])

    coords = [int(x[0]) for x in [data['x1'], data['y1'], data['width'], data['height']]]

    images = []

    # Capturing the window alone uses low-level Windows API stuff. Prone to breaking.
    if len(config_state.capture_window) > 0:
        xyxy = [coords[0], coords[1], coords[0] + coords[2], coords[1] + coords[3]]

        with logger.begin_event('Capturing specific window image.', capture_window=config_state.capture_window):
            images = [capture_window_image_from_box(config_state.capture_window, xyxy)]
    else:
        # From: https://python-mss.readthedocs.io/examples.html#pil
        with mss() as sct:
            monitor = {"top": coords[1], "left": coords[0], "width": coords[2], "height": coords[3]}
            sct_img = sct.grab(monitor)

            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            images = [img]

    socketio.start_background_task(
        translate_task3_background_job,
        images,
        data['box_id'],
        data['with_text_detect'],
        use_stream,
        True,
        data['translate_lines_individually']
    )

@app.route("/processtask3new", methods=["POST"])
def process_task3new_route():
    data = request.form.to_dict(flat=False)
    box_id = data["boxId"] if "boxId" in data else None
    text_detect = data["textDetect"] if "textDetect" in data else "off"

    use_stream = data["useStream"] if "useStream" in data else "off"

    use_stream = True if use_stream[0] == "on" else None

    translate_lines_individually = int(data['translateLinesIndividually'][0])

    # It's an array? Huh? TODO
    with_text_detect = text_detect[0] == "on"
    if box_id is not None and len(box_id) > 0:
        box_id = box_id[0]

    process_task3_faster({
        'x1': data['x1'],
        'y1': data['y1'],
        'width': data['width'],
        'height': data['height'],
        'box_id': box_id,
        'with_text_detect': with_text_detect,
        'use_stream': use_stream,
        'translate_lines_individually': translate_lines_individually,
    })

    return {"processing": True}, 202

# From task1
def encode_image(new_image):
    buffer = BytesIO()
    # Poor quality: new_image.save(buffer, format="JPEG")
    new_image.save(buffer, format="PNG")
    new_image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return new_image_base64

@app.route("/previewwindowcapture", methods=["POST"])
def preview_window_capture():
    data = request.form.to_dict(flat=False)

    if 'x1' in data:
        coords = [int(x[0]) for x in [data['x1'], data['y1'], data['width'], data['height']]]
        xyxy = [coords[0], coords[1], coords[0] + coords[2], coords[1] + coords[3]]
    else:
        xyxy = None

    # Capturing the window alone uses low-level Windows API stuff. Prone to breaking.
    if len(config_state.capture_window) > 0:

        images = [capture_window_image_from_box(config_state.capture_window, xyxy)]
    else:
        images = []

    return {
        'image_base64': encode_image(images[0]) if len(images) > 0 else "",
    }, 202
