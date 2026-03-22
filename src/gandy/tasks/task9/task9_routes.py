from flask import request
from gandy.app import app, translate_pipeline, socketio
from gandy.utils.fancy_logger import logger
from gandy.tasks.task9.asr_gguf import AsrGgufApp
from gandy.tasks.task5.video_burner import burn_subs
from gandy.tasks.task5.task5_logic import working_path, save_videos_path, save_subtitles_path
from gandy.tasks.task9.speech_segmenter.speech_segmenter import SpeechSegmenter
from gandy.tasks.task9.speech_segmenter.utils_vad import read_audio
from srt import Subtitle, compose
import os
from uuid import uuid4

# Task9 - Transcribe audio in a vidoe file and burn the translation (similar to Task5).
# Used in VideoView.

os.makedirs(save_videos_path, exist_ok=True)
os.makedirs(save_subtitles_path, exist_ok=True)

# TODO: Place this somewhere cleaner.
speech_segmenter = SpeechSegmenter("asr/silero_vad")
speech_to_text = AsrGgufApp("asr/llm-xy", "asr/mmproj-xy")

def emit_progress(true_progress: float):
    socketio.patched_emit(f"progress_task5", true_progress) # Reuse progress_task5 here.
    socketio.sleep()

def save_subs(subtitles, video_file_path, side):
    with logger.begin_event("Saving SRT file", len_subtitles=len(subtitles), video_file_path=video_file_path, side=side) as ctx:
        # side = source | target

        video_name = os.path.splitext(os.path.basename(video_file_path))[0].strip()
        subtitles_file_path = os.path.join(save_subtitles_path, f"{video_name}_{side}.srt")

        with open(subtitles_file_path, "w", encoding="utf-8") as f:
            f.write(compose(subtitles))

        ctx.log("Saved to", subtitles_file_path=subtitles_file_path)

    return subtitles_file_path

def process_task9_background_job(video_file_path: str):
    with logger.begin_event("Task9 transcribing and translating video audio", video_file_path=video_file_path):
        with logger.begin_event("Loading audio data"):
            # Both Silero VAD and the ASR support 16000 SR.
            SAMPLING_RATE = 16000
            audio_data = read_audio(video_file_path, SAMPLING_RATE) # librosa.load(video_file_path, sr=SAMPLING_RATE, mono=True)

        with logger.begin_event("Detecting voice activity") as ctx:
            # First get all speech segments using a VAD.
            # Each output is a dict with start & end timestamps.
            speech_segments = speech_segmenter.process(audio_data)
            socketio.patched_emit("progress_task5", 1)

            ctx.log("Done with VAD", len_speech_segments=len(speech_segments))

        # For computing progress to show to the user. (* 2) since there's ASR + translation.
        # (+ 10) so there's a little buffer after ASR/Translationns for burning the subtitles.
        total_steps = len(speech_segments) * 2 + 10

        with logger.begin_event("Transcribing speech to text") as ctx:
            # Then transcribe each speech segment.
            # Each item is a dict with start & end timestamps along with the transcribed text.
            transcriptions = []
            for i, segment in enumerate(speech_segments):
                with logger.begin_event("Transcribing text", start=segment.start.total_seconds(), end=segment.end.total_seconds()):
                    segment_audio = audio_data[int(segment.start.total_seconds() * SAMPLING_RATE):int(segment.end.total_seconds() * SAMPLING_RATE)]
                    content = speech_to_text.process(segment_audio)

                    transcriptions.append(Subtitle(index=i, start=segment.start, end=segment.end, content=content))
                    socketio.patched_emit("progress_task5", (i + 1) // total_steps + 1)
                    socketio.sleep()

        # Save untranslated SRT data if the user needs it in the future.
        # TODO: Refactor - Some duplicated SRT logic; this one uses an SRT library, task5 uses internal SRT logic instead...
        save_subs(transcriptions, video_file_path, "source")

        with logger.begin_event("Translating transcriptions") as ctx:
            # Translate.
            target_subs = []
            for i, transcription in enumerate(transcriptions):
                with logger.begin_event("Translating text", start=transcription.start.total_seconds(), end=transcription.end.total_seconds(), content=transcription.content):
                    target = translate_pipeline.get_target_texts_from_str(
                        [transcription.content],
                        use_stream=None,
                    )
                    target = target[0]

                    target_subs.append(Subtitle(index=i, start=transcription.start, end=transcription.end, content=target))
                    socketio.patched_emit("progress_task5", (i + 1) // total_steps + 1)
                    socketio.sleep()

        # Save translated SRT data so we can burn it into the video.
        target_srt_path = save_subs(target_subs, video_file_path, "target")

        with logger.begin_event("Burning subtitles") as ctx:
            out_video_path = os.path.join(save_videos_path, f"{uuid4().hex}.mp4")
            ctx.log("Saving video to", out_video_path=out_video_path)

            burn_subs( # Similar to task5 just to be safe...
                working_path(target_srt_path, abs=True),
                working_path(video_file_path),
                out_path=working_path(out_video_path, abs=True),
                with_progress=False,
                # These args are only needed if using with_progress=True:
                progress_callback=None,
                video_duration_seconds=None,
            )

    # Since client expects task5 done. Same for progress tasks. TODO: Use one done_translating for all video tasks.
    socketio.patched_emit("done_translating_task5", out_video_path.replace("\\", "/"))
    socketio.sleep()

@app.route("/processtask9", methods=["POST"])
def process_task9_route():
    data = request.form.to_dict(flat=False)
    video_file_path = data["videoFilePath"]

    video_file_path = video_file_path[
        0
    ]  # FormData is a list - we only care for the first item.

    socketio.start_background_task(
        process_task9_background_job,
        video_file_path,
    )

    return {"processing": True}, 202