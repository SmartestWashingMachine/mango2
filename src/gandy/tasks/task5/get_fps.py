import ffmpeg
from math import floor


def get_fps(video_file_path: str, return_duration_in_seconds=False):
    # https://github.com/kkroening/ffmpeg-python/issues/165
    try:
        probed = ffmpeg.probe(video_file_path)
    except ffmpeg.Error as e:
        print("STDOUT:", e.stdout.decode("utf8"))
        print("STDERR:", e.stderr.decode("utf8"))
        raise e

    data = probed["streams"]

    # Find first stream with a valid frame rate. Note the assumption here that non main streams have a 0/0 frame rate.
    for stream in data:
        r_f = stream["r_frame_rate"]  # n/n as string
        num, den = r_f.split("/")

        den = float(den)

        try:
            fps = int(float(num) / float(den))

            if return_duration_in_seconds:
                dur = floor(float(probed["format"]["duration"]))
                return fps, dur
            return fps
        except:
            pass

    print(f"Bad data for FFProbe get_fps:")
    print(data)
