import os
from gandy.tasks.task9.speech_segmenter.utils_vad import OnnxWrapper, read_audio, get_speech_timestamps, VADIterator, collect_chunks, drop_chunks
from srt import Subtitle
from gandy.utils.fancy_logger import logger
from datetime import timedelta
from typing import List

def merge_subtitles(
    subtitles: List[Subtitle],
    max_gap: timedelta = timedelta(seconds=1.0),
    max_duration: timedelta = timedelta(seconds=10),
) -> List[Subtitle]:
    if not subtitles:
        return []

    merged = []
    current = subtitles[0]
    for sub in subtitles[1:]:
        gap = sub.start - current.end
        combined_duration = sub.end - current.start

        if gap <= max_gap and combined_duration <= max_duration:
            current.end = sub.end
        else:
            merged.append(current)
            current = sub

    merged.append(current)
    return merged

SAMPLING_RATE = 16000

class SpeechSegmenter():
    def __init__(self, model_sub_path: str):
        self.model_sub_path = model_sub_path
        self.model = None

    def get_model_path(self):
        return os.path.join("models", f"{self.model_sub_path}.onnx")

    def load_model(self):
        self.model = OnnxWrapper(self.get_model_path(), force_onnx_cpu=True)

    def process(self, audio: bytes):
        if self.model is None:
            self.load_model()

        self.model.reset_states()
        timestamps = get_speech_timestamps(
            audio, self.model,
            sampling_rate=SAMPLING_RATE,
            threshold=0.3,
            min_speech_duration_ms=250,
            min_silence_duration_ms=300,
            speech_pad_ms=100,
            return_seconds=False,
        )

        items = []
        for i, ts in enumerate(timestamps):
            item = Subtitle(index=i, start=timedelta(seconds=ts['start'] / SAMPLING_RATE), end=timedelta(seconds=ts['end'] / SAMPLING_RATE), content="N/A")
            items.append(item)
            logger.log_message("VAD found activity", start=item.start.total_seconds(), end=item.end.total_seconds())

        items = merge_subtitles(items)

        for item in items:
            logger.log_message("Merged found activity", start=item.start.total_seconds(), end=item.end.total_seconds())

        return items