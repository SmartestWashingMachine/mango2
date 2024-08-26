from flask import request
from gandy.app import app, translate_pipeline, socketio
from gandy.tasks.task5.task5_logic import process_task5
from gandy.utils.fancy_logger import logger

# Task5 - auto translate written text in video.


def emit_progress(true_progress: float):
    socketio.patched_emit(f"progress_task5", true_progress)
    socketio.sleep()


def mt_progress(progress: float):
    emit_progress(progress / 2)  # [0, 0.5]


def burn_progress(progress: float):
    emit_progress(0.5 + (progress / 2))  # [0.5, 1.0]


def process_task5_background_job(video_file_path: str, every_secs: float):
    out = ""

    try:
        with logger.begin_event("Task5") as ctx:
            ctx.log(
                "Translating video",
                video_file_path=video_file_path,
                every_secs=every_secs,
            )
            out = process_task5(
                translate_pipeline,
                video_file_path,
                mt_progress_callback=mt_progress,
                burn_progress_callback=burn_progress,
                every_secs=every_secs,
            )
            ctx.log(f"Created new video", out=out)
    except Exception as e:
        logger.log(e)

    socketio.patched_emit("done_translating_task5", out.replace("\\", "/"))


@app.route("/processtask5", methods=["POST"])
def process_task5_route():
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
        process_task5_background_job,
        video_file_path,
        every_secs,
    )

    return {"processing": True}, 202
