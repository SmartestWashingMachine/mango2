from flask import request
from gandy.app import app, translate_pipeline
from gandy.tasks.task3.bg_activity_watcher import BackgroundActivityWatcher
from gandy.tasks.task3.task3_routes import process_task3_faster
from gandy.utils.fancy_logger import logger
import numpy as np

# key = box id string
# value = watcher instance
box_states = {}

def forget_box(box_id: str):
    with logger.begin_event("Unregistering box background watcher", box_id=box_id):
        if box_id in box_states and box_states[box_id] is not None:
            box_states[box_id].stop()
            del box_states[box_id]

cached_lines = {}

# Vibe-coded this util because bored :3
def calculate_iou(boxA, boxB):
    # Determine the coordinates of the intersection rectangle
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    # Compute the area of intersection
    interWidth = max(0, xB - xA)
    interHeight = max(0, yB - yA)
    interArea = interWidth * interHeight

    # Compute the area of both bounding boxes
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])

    # Compute IoU
    iou = interArea / float(boxAArea + boxBArea - interArea)
    return iou

def are_lines_stale(img, box_id):
    """
    Are the text lines on this image the same as the ones detected on the image before? This is to avoid redundant OCR work.
    """

    prev_box_lines = cached_lines.get(box_id, [])

    text_line_app = translate_pipeline.text_line_app.get_sel_app()
    line_bboxes = text_line_app.get_images(img, return_image_if_fails=False)

    cached_lines[box_id] = line_bboxes

    # Different number of boxes detected - they can not be the same!
    if len(line_bboxes) != len(prev_box_lines):
        # print(f"Differing number of line boxes!")
        return False
    
    if len(line_bboxes) == 0:
        # print(f"No boxes found!")
        return False

    for idx in range(len(line_bboxes)):
        iou = calculate_iou(line_bboxes[idx], prev_box_lines[idx])

        if iou < 0.96:
            # print(f"IOU too low. Boxes are different!")
            # print(iou)
            return False
        
        # print("IOU close. One pair of boxes are equivalent!")
        # print(iou)

    return True

def process_image(thread_id, box_state):
    process_task3_faster(box_state)


@app.route("/task3watchboxbg", methods=["POST"])
def begin_watching_box_bg():
    with logger.begin_event("Registering box background watcher") as ctx:
        data = request.get_json()
        box_id = data["boxState"]["this_box_id"]
        ctx.log("For box ID", box_id=box_id)

        forget_box(box_id)

        # Note the coords are fixed on instantiation; thus we need to forget box if its moved in the frontend... we don't want stale data.
        coords = [int(x[0]) for x in [data['boxState']['x1'], data['boxState']['y1'], data['boxState']['width'], data['boxState']['height']]]
        watcher = BackgroundActivityWatcher(
            monitor_coords=coords,
            ocr_callback=lambda: process_image("stub", data['boxState']),
            text_lines_stale_callback=lambda img: are_lines_stale(img, box_id),
        )

        box_states[box_id] = watcher
        watcher.start()

        return {"processing": True}, 202

@app.route("/task3forgetboxbg", methods=["POST"])
def stop_watching_box_bg():
    data = request.get_json()

    box_id = data["boxState"]["this_box_id"]
    forget_box(box_id)

    return {"processing": True}, 200