from typing import List


class TranslatedSegment:
    def __init__(self, text: str, at_frame: int) -> None:
        self.text = text
        self.at_frame = at_frame


class SubtitleMaker:
    def __init__(self, video_fps: int, sub_duration: int) -> None:
        self.video_fps = video_fps
        self.sub_duration = sub_duration

    def get_timestamp(self, frame) -> str:
        seconds = frame // self.video_fps

        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        s = int(s)
        m = int(m)
        h = int(h)

        return f"{h:02d}:{m:02d}:{s:02d},000"

    def create_srt_content(self, segments: List[TranslatedSegment]):
        srt_content = ""

        for i in range(len(segments)):
            s = segments[i]
            srt_content += f"{i + 1}\n"  # Iteration
            srt_content += f"{self.get_timestamp(s.at_frame)} --> {self.get_timestamp(s.at_frame + self.sub_duration)}\n"  # Timestamp
            srt_content += f"{s.text}\n\n"  # Translation

        return srt_content.strip()
