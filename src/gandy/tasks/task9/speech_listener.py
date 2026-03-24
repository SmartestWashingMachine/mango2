import threading
import numpy as np
import soundcard as sc # "Why not sounddevice?" - it crashes with a very helpful error. ref: https://github.com/invoke-ai/InvokeAI/issues/4416
from ten_vad import TenVad
import ctypes
import queue
import collections

SAMPLING_RATE = 16000
BLOCK_SIZE = 4096  # 2 seconds of audio per read. Hopefully avoids discontinuities

# 1 frame = 16ms (hop_size(256) / sample rate(16000)) or 0.016 seconds
class SystemAudioListener:
    def __init__(self, on_speech, hop_size=256, threshold=0.5, valid_frames=5, patience_frames=18):
        self.on_speech = on_speech
        self.hop_size = hop_size
        self.threshold = threshold
        self.valid_frames = valid_frames
        self.patience_frames = patience_frames
        self.vad = TenVad(hop_size, threshold) # TODO: Share TenVad instance with task9.speech_segmenter
        self._audio_q = queue.Queue(maxsize=100)
        self._speech_q = queue.Queue()
        self._stop = threading.Event()
        self._stop.set()

    def start(self):
        if not self._stop.is_set():
            return

        self._stop.clear()
        threading.Thread(target=self._capture_loop, daemon=True).start()
        threading.Thread(target=self._vad_loop, daemon=True).start()
        threading.Thread(target=self._callback_loop, daemon=True).start()

    def stop(self):
        self._stop.set()

    def _capture_loop(self):
        # "What is this windll magic?" Honestly no clue, but this guy somehow figured it out.
        # ref: https://github.com/bastibe/SoundCard/issues/83
        ole32 = ctypes.windll.ole32
        ole32.CoInitialize(None)

        try:
            mic = sc.get_microphone(
                id=str(sc.default_speaker().name),
                include_loopback=True,
            )

            with mic.recorder(samplerate=SAMPLING_RATE, channels=1) as recorder:
                while not self._stop.is_set():
                    data = recorder.record(numframes=BLOCK_SIZE)
                    chunk = np.clip(data[:, 0] * 32768, -32768, 32767).astype(np.int16)

                    try:
                        self._audio_q.put_nowait(chunk)
                    except queue.Full:
                        pass
        finally:
            # Not sure if we need to uninitialize, but better to be safe...
            ole32.CoUninitialize()

    def _vad_loop(self):
        is_speaking = False
        speech_buf = []
        frame_buffer = []
        frame_index = 0
        recent_frames = collections.deque(maxlen=self.valid_frames + 1)
        sample_buf = np.array([], dtype=np.int16)

        while not self._stop.is_set():
            # A timeout is used so this thread automatically terminates when stop is set (since the function "finishes".)
            try:
                chunk = self._audio_q.get(timeout=0.5)
            except queue.Empty:
                continue

            sample_buf = np.concatenate([sample_buf, chunk])

            while len(sample_buf) >= self.hop_size: # soundcard throws all sorts of scary warnings if BLOCK_size is too small.
                frame = sample_buf[:self.hop_size]
                sample_buf = sample_buf[self.hop_size:]

                _, out_flag = self.vad.process(frame)
                has_speech = out_flag == 1

                if is_speaking:
                    speech_buf.append(frame)

                    if not has_speech:
                        frame_buffer.append(frame_index)
                        if len(frame_buffer) >= self.patience_frames:
                            self._speech_q.put(np.concatenate(speech_buf))
                            is_speaking = False
                            speech_buf = []
                            frame_buffer = []
                    else:
                        frame_buffer = []
                else:
                    recent_frames.append(frame)

                    if has_speech:
                        frame_buffer.append(frame_index)

                        if len(frame_buffer) >= self.valid_frames:
                            is_speaking = True
                            speech_buf = list(recent_frames)
                            frame_buffer = []
                    else:
                        frame_buffer = []

                frame_index += 1

        if is_speaking and speech_buf:
            self._speech_q.put(np.concatenate(speech_buf))

    def _callback_loop(self):
        while not self._stop.is_set():
            try:
                audio = self._speech_q.get(timeout=0.5)
            except queue.Empty:
                continue

            self.on_speech(audio)