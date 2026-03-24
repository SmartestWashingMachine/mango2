from flask import request
from gandy.app import app, socketio, translate_pipeline
from gandy.tasks.task9.task9_routes import speech_to_text
from gandy.tasks.task9.speech_listener import SystemAudioListener
from gandy.utils.fancy_logger import logger

box_states = {}

def on_speech(audio_data):
    with logger.begin_event("Captured audio from PC", n_boxes=len(list(box_states.keys()))) as ctx:
        # TODO: ASR + Translation always uses local, not remote. This is not the case for task5, which properly calls remote route when needed.
        # TODO: Use streaming here (on translation - not ASR)
        # TODO: Set loading.
        transcription = speech_to_text.process(audio_data)
        ctx.log(f"Transcription found", transcription=transcription)

        target = translate_pipeline.get_target_texts_from_str(
            [transcription],
            use_stream=None,
        )
        target = target[0]
        ctx.log(f"Translation found", translation=target)

        for box_id in box_states.keys():
            socketio.patched_emit(
                'done_translating_task2', # TODO: Refactor to use one event name rather than task2 specific.
                {
                    'boxId': box_id,
                    'sourceText': transcription,
                    # I cannot for the life of me remember WHY target text needs to be a list of strings (one item)?
                    # I HATE UNTYPED LANGUAGES GIVE ME MY INTERFACES BACK WAHHHHHHH
                    'text': [target],

                },
            )

        socketio.sleep()

audio_listener = SystemAudioListener(on_speech=on_speech)

@app.route("/begincaptureaudioforbox", methods=["POST"])
def begin_capture_audio_route():
    with logger.begin_event("Beginning audio capture for box") as ctx:
        data = request.get_json()

        # TODO: Use sender / output box ids. Right now it assumes the sender is always the output box id.
        box_id = data["box_id"]
        box_states[box_id] = ""

        audio_listener.start()

        ctx.log(f"Captured boxes", box_ids=list(box_states.keys()))
        return {"processing": True}, 202

@app.route("/stopcaptureaudioforbox", methods=["POST"])
def stop_capture_audio_route():
    with logger.begin_event("Stopping audio capture for box") as ctx:
        data = request.get_json()

        box_id = data["box_id"]
        if box_id in box_states:
            del box_states[box_id]

        ctx.log(f"Captured boxes", box_ids=list(box_states.keys()))

        if len(box_states) == 0:
            ctx.log("Stopping capture as no more boxes are listening.")
            audio_listener.stop()

        return {"processing": True}, 202