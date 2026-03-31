from flask import request
from gandy.app import app
from gandy.tasks.task3.bg_activity_watcher import BackgroundActivityWatcher
from gandy.tasks.task3.task3_routes import process_task3_faster
from gandy.utils.fancy_logger import logger

# key = box id string
# value = watcher instance
box_states = {}

def forget_box(box_id: str):
    with logger.begin_event("Unregistering box background watcher", box_id=box_id):
        if box_id in box_states and box_states[box_id] is not None:
            box_states[box_id].stop()
            del box_states[box_id]

@app.route("/task3watchboxbg", methods=["POST"])
def begin_watching_box_bg():
    with logger.begin_event("Registering box background watcher") as ctx:
        data = request.get_json()
        box_id = data["boxState"]["this_box_id"]
        ctx.log("For box ID", box_id=box_id)

        forget_box(box_id)

        # Note the coords are fixed on instantiation; thus we need to forget box if its moved in the frontend... we don't want stale data.
        coords = [int(x[0]) for x in [data['boxState']['x1'], data['boxState']['y1'], data['boxState']['width'], data['boxState']['height']]]
        watcher = BackgroundActivityWatcher(monitor_coords=coords, ocr_callback=lambda: process_task3_faster(data["boxState"]))

        box_states[box_id] = watcher
        watcher.start()

        return {"processing": True}, 202

@app.route("/task3forgetboxbg", methods=["POST"])
def stop_watching_box_bg():
    data = request.get_json()

    box_id = data["boxState"]["this_box_id"]
    forget_box(box_id)

    return {"processing": True}, 200