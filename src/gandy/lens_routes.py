from flask import request
from gandy.app import app, translate_pipeline, remote_router
from gandy.state.config_state import config_state
from gandy.state.context_state import context_state
from gandy.utils.fancy_logger import logger
from mss import mss
from PIL import Image
from io import BytesIO
from win32api import GetMonitorInfo, MonitorFromPoint
from gandy.utils.get_scale_factor import get_windows_scale_factor, SCALE_FACTOR
import regex as re

# This function is vibe-coded.
def has_cjk_characters_property(text):
    pattern = r'[\p{Script=Han}\p{Script=Hiragana}\p{Script=Katakana}\p{Script=Hangul}]'
    return bool(re.search(pattern, text))

# Code from: https://stackoverflow.com/questions/4357258/how-to-get-the-height-of-windows-taskbar-using-python-pyqt-win32
# I HATE WINDOWS I HATE WINDOWS I HATE WINDOWS
def get_taskbar_height():
    primary_monitor = MonitorFromPoint((0,0))
    monitor_info = GetMonitorInfo(primary_monitor)
    monitor_area = monitor_info.get("Monitor")
    work_area = monitor_info.get("Work")
    taskbar_height = monitor_area[3]-work_area[3]

    return taskbar_height

def process_screen_task(img: Image.Image):
    with logger.begin_event("Sending to pipeline"):
        data_to_translate = translate_pipeline.image_to_image(
            img, progress_cb=None, skip_redrawing=True,
        ) # target_texts & speech_bboxes keys are what we care for - returned because we enable 'skip_redrawing'.

    with logger.begin_event("Mapping to output", datas=data_to_translate):
        outputs = []
        for (translation, source, bbox) in zip(data_to_translate["target_texts"], data_to_translate["source_texts"], data_to_translate["speech_bboxes"]):
            outputs.append({
                "text": translation,
                "source": source,
                "x": int(bbox[0]),
                "y": int(bbox[1]),
                "width": int(bbox[2] - bbox[0]),
                "height": int(bbox[3] - bbox[1]),
            })

    return { "items": outputs, }

@app.route("/remote/scanscreen", methods=["POST"])
def scan_screen_task_remotely():
    with logger.begin_event("Processing scan screen request from remote client."):
        with logger.begin_event("Converting image to PIL"):
            # Convert images from to PIL

            image_data = request.files.get('images')
            image_stream = BytesIO(image_data.read())
            im = Image.open(image_stream)
            im.load() # Should only be one image.
            pil_image = im.convert("RGB") if im.mode != "RGB" else im

    return process_screen_task(pil_image)

@app.route("/scanscreen", methods=["GET"])
def scan_screen_task():
    """
    Example output:

    return {
        "items": [
            {
                "x": 100,
                "y": 100,
                "width": 200,
                "height": 400,
                "text": "SAMPLE TEXT HERE!",
            },
        ]
    }
    """

    with logger.begin_event("Lens scan screen") as ctx:
        taskbar_height = get_taskbar_height()

        with mss() as sct:
            monitor = sct.monitors[1]
            sct_img = sct.grab({ "top": monitor["top"], "left": monitor["left"], "width": monitor["width"], "height": monitor["height"] - taskbar_height, })

            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

        if remote_router.is_remote():
            image_stream = BytesIO()

            if remote_router.compress_jpeg:
                img.save(image_stream, format="JPEG", quality=95)
            else:
                img.save(image_stream, format="PNG")

            image_stream.seek(0)
            files_to_send = {
                'images': ('image.png', image_stream.getvalue(), 'image/png'),
            }

            response_data = remote_router.form_post_with_response('/remote/scan_screen', data={}, files=files_to_send)
        else:
            response_data = process_screen_task(img)

        with logger.begin_event("Mapping with screen scale", scale_factor=SCALE_FACTOR, taskbar_height=taskbar_height):
            mapped_outputs = []
            for item in response_data["items"]:
                txt = item["text"].strip()
                if not txt or not item["source"] or not has_cjk_characters_property(item["source"].replace(" ", "")):
                    continue

                mapped = {
                    "text": txt,
                    "source": item["source"],
                    "x": int(item["x"] / SCALE_FACTOR),
                    "y": int(item["y"] / SCALE_FACTOR),
                    "width": int(item["width"] / SCALE_FACTOR),
                    "height": int((item["height"]) / SCALE_FACTOR),
                }
                mapped_outputs.append(mapped)

        return {
            "items": mapped_outputs,
        }