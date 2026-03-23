from ten_vad import TenVad
import os
from gandy.tasks.task9.speech_segmenter.utils_vad import OnnxWrapper, read_audio, get_speech_timestamps, VADIterator, collect_chunks, drop_chunks
from srt import Subtitle
from gandy.utils.fancy_logger import logger
from datetime import timedelta
from typing import List
import numpy as np

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
        self.hop_size = 256 # 16 ms per frame
        self.threshold = 0.35 # Maybe 0.5 is better?

    def get_model_path(self):
        return os.path.join("models", f"{self.model_sub_path}.onnx")

    def load_model(self):
        self.model = OnnxWrapper(self.get_model_path(), force_onnx_cpu=True)
        self.vad = TenVad(self.hop_size, self.threshold)

    def process(self, audio: np.ndarray):
        audio_data = np.clip(audio * 32768, -32768, 32767).astype(np.int16)
        num_frames = audio_data.shape[0] // self.hop_size

        if self.model is None:
            self.load_model()

        is_speaking = False
        start_i = 0
        buffer = []
        valid_frames = 3 # Wait for this many speech frames to start a speech segment.
        patience_frames = 3 # Wait for this many silence frames to consider a speech segment done.

        segments: List[Subtitle] = []

        for i in range(num_frames):
            frame = audio_data[i * self.hop_size:(i + 1) * self.hop_size]
            out_probability, out_flag = self.vad.process(frame)

            has_speech = out_flag == 1

            #from time import sleep
            #sleep(1)
            #print("[%d] %0.6f, %d" % (i, out_probability, out_flag))

            if is_speaking:
                if not has_speech:
                    buffer.append(i)

                    # Waited long enough - there's no more speech. End this segment.
                    if len(buffer) >= patience_frames:
                        segments.append(Subtitle(start=start_i, end=i, content="N/A", index=0))

                        is_speaking = False
                        buffer = []
                else:
                    # Speech was still detected - someone is still speaking. Reset the patience threshold.
                    buffer = []
            else:
                if has_speech:
                    buffer.append(i)

                    if len(buffer) >= valid_frames:
                        # Enough speech frames were detected - starting a new segment and listening for its end...
                        is_speaking = True
                        buffer = []
                        start_i = i
                else:
                    # Not currently in a speech segment and silence was detected - reset the window.
                    buffer = []

        # Detect speech at end of audio OR detect speech that spans the entire audio.
        if is_speaking:
            segments.append(Subtitle(start=start_i, end=i + 1, content="N/A", index=0)) # i + 1 as last frame probably had speech too.

        # From frame indices to seconds.
        items = []
        for i, ts in enumerate(segments):
            item = Subtitle(
                index=i,
                start=timedelta(seconds=ts.start * self.hop_size / SAMPLING_RATE),
                end=timedelta(seconds=ts.end * self.hop_size / SAMPLING_RATE),
                content="N/A"
            )
            items.append(item)
            logger.log_message("VAD found activity", start=item.start.total_seconds(), end=item.end.total_seconds())

        items = merge_subtitles(items)

        for item in items:
            logger.log_message("Merged found activity", start=item.start.total_seconds(), end=item.end.total_seconds())

        return items