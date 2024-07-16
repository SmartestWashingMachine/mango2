import ffmpeg
import os
from glob import glob


def generate_images(video_file_path: str, out_dir: str, every_secs: float):
    # Get frames and return path for every valid frame.
    stream = ffmpeg.input(video_file_path)
    stream = ffmpeg.filter(
        stream, "fps", fps=f"1/{every_secs}"
    )  # 1 frame every N secs. Works on decimal e.g: 0.5

    # Do NOT use JPEG! FFMpeg's JPEG encoder is awful!
    stream = ffmpeg.output(stream, f"{out_dir}/video_%d.png", start_number=0)
    ffmpeg.run(stream)

    sorted_files = sorted(glob(f"{out_dir}/*.png"), key=os.path.getmtime)
    return sorted_files
