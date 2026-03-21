from flask import request
from gandy.app import app, translate_pipeline, socketio
from gandy.utils.fancy_logger import logger

# Task9 - Transcribe audio in a vidoe file and burn the translation (similar to Task5).
# Used in VideoView.

def emit_progress(true_progress: float):
    socketio.patched_emit(f"progress_task5", true_progress) # Reuse progress_task5 here.
    socketio.sleep()

def process_task9_background_job(video_file_path: str):
    with logger.begin_event("Task9 transcribing video", video_file_path=video_file_path) as ctx:
        # Transcribe & save as untranslated SRT cache data.

        # Use untranslated SRT cache data to translate and then burn.
        for sub in []:
            target = translate_pipeline.get_target_texts_from_str(
                [sub],
                use_stream=None,
            )

            target = target[0]
        pass

    socketio.sleep()

@app.route("/processtask9", methods=["POST"])
def process_task9_route():
    data = request.form.to_dict(flat=False)
    video_file_path = data["videoFilePath"]

    video_file_path = video_file_path[
        0
    ]  # FormData is a list - we only care for the first item.

    try:
        every_secs = float(data["everySecs"])
        if every_secs is None or not isinstance(every_secs, float):
            raise ValueError(f"every_secs must be a float, but got: {every_secs}")
    except:
        every_secs = 1

    socketio.start_background_task(
        process_task9_background_job,
        video_file_path,
        every_secs,
    )

    return {"processing": True}, 202