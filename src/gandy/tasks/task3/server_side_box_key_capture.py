# DID YOU KNOW ELECTRONJS'S GLOBAL SHORTCUTS DOESN'T ACTUALLY FUDGING WORK ON A LOT OF APPS?
# GOOD JOB ELECTRON. GOOD JOB.
# LIKE REALLY - I REGRET USING ELECTRONJS. ALMOST ALL OF THE FUNCTIONALITY I NEED IS INSTEAD DONE IN PYTHON.
# So in this util we define a way to capture keybinds on the server, then call task3 directly.

from flask import request
from gandy.app import app
from gandy.tasks.task3.task3_routes import process_task3_faster
import keyboard

box_states = {}

def construct_box_id_key(output_box_id, sender_box_id):
    return f'{output_box_id}_{sender_box_id}'

@app.route("/task3rememberbox", methods=["POST"])
def remember_box_route():
    data = request.get_json()

    box_id = construct_box_id_key(data["boxState"]["box_id"], data["boxState"]["this_box_id"])
    if box_id in box_states and box_states[box_id] is not None:
        keyboard.remove_hotkey(box_states[box_id])

    hotkey = keyboard.add_hotkey(data["boxState"]["activation_key"], lambda: process_task3_faster(data["boxState"]))
    box_states[box_id] = hotkey

    return {"processing": True}, 202

@app.route("/task3forgetbox", methods=["POST"])
def forget_box_route():
    data = request.get_json()

    try:
        box_id = construct_box_id_key(data["box_id"], data["this_box_id"])
        hotkey = box_states[box_id]

        if hotkey is not None:
            keyboard.remove_hotkey(hotkey)

        box_states[box_id] = None
    except Exception as e:
        print('ERROR FORGETTING BOX:')
        print(e)

    return {"processing": True}, 200