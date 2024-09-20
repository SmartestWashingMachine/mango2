import ffmpeg
from gandy.tasks.task5.progress_ffmpeg import ProgressFfmpeg


def burn_subs(
    srt_file_path: str,
    video_path: str,
    out_path: str,
    video_duration_seconds: int,
    progress_callback,
    with_progress=True,
    # every_secs = 2,
):
    video = ffmpeg.input(video_path)
    audio = video.audio

    sub = ffmpeg.filter(video, "subtitles", srt_file_path, force_style="BackColour=&H80000000,BorderStyle=4,Shadow=3")
    concat = ffmpeg.concat(sub, audio, v=1, a=1)
    # concat = ffmpeg.filter(concat, "fps", fps=f"1/{every_secs}") # Makes it choppy.

    if with_progress:
        with ProgressFfmpeg(video_duration_seconds, progress_callback) as progress:
            out = (
                ffmpeg.output(concat, out_path)
                .global_args("-progress", progress.output_file.name)
                .overwrite_output()
            )

            try:
                # ffmpeg.run(out, capture_stderr=True, capture_stdout=True)
                ffmpeg.run(out)
            except ffmpeg.Error as e:
                print("STDOUT:", e.stdout.decode("utf8"))
                print("STDERR:", e.stderr.decode("utf8"))
                raise e
    else:
        out = ffmpeg.output(concat, out_path).overwrite_output()

        try:
            ffmpeg.run(out, capture_stderr=False, capture_stdout=False)
        except ffmpeg.Error as e:
            print("STDOUT:", e.stdout.decode("utf8"))
            print("STDERR:", e.stderr.decode("utf8"))
            raise e
