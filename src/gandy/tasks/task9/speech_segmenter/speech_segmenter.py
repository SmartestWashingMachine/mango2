import os
from gandy.tasks.task9.speech_segmenter.utils_vad import OnnxWrapper, read_audio, get_speech_timestamps, VADIterator, collect_chunks, drop_chunks
from srt import Subtitle
from gandy.utils.fancy_logger import logger
from datetime import timedelta

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
            threshold=0.5,
            min_speech_duration_ms=250,
            min_silence_duration_ms=100,
            speech_pad_ms=30,
            return_seconds=False,
        )

        items = []
        for i, ts in enumerate(timestamps):
            items.append(Subtitle(index=i, start=timedelta(seconds=ts['start'] / SAMPLING_RATE), end=timedelta(seconds=ts['end'] / SAMPLING_RATE), content="N/A"))
            logger.log_message("VAD found activity", start=items[-1].start.total_seconds(), end=items[-1].end.total_seconds())

        return items