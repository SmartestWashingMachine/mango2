import mss
import numpy as np
import cv2
import threading
import time

class BackgroundActivityWatcher:
    def __init__(self, monitor_coords, ocr_callback, sensitivity=0.005):
        self.coords = monitor_coords
        self.ocr_callback = ocr_callback
        self.sensitivity = sensitivity  # % of pixels that must change (0.005 = 0.5%)
        
        self._stop_event = threading.Event()
        self._thread = None
        self._last_baseline = None
        self._last_ocr_text = None

        self.SCAN_RATE = 0.15  # How often to check for ANY change
        self.CHANGE_THRESHOLD = 12  # Pixel brightness diff to count as "changed"
        self.STABILITY_COUNT = 4  # Consecutive stable frames needed
        self.STABILITY_INTERVAL = 0.25  # Time between stability checks
        self.COOLDOWN = 0.2  # Don't trigger OCR for this long after success

    def _get_frame(self, sct):
        monitor = {"top": self.coords[1], "left": self.coords[0], "width": self.coords[2], "height": self.coords[3]}

        img = np.array(sct.grab(monitor))
        gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)

        # TODO: maybe (5, 5) ?
        return cv2.GaussianBlur(gray, (3, 3), 0)

    def _compute_change_pct(self, frame1, frame2):
        diff = cv2.absdiff(frame1, frame2)
        changed_pixels = np.sum(diff > self.CHANGE_THRESHOLD)

        return changed_pixels / diff.size

    def _watch_loop(self):
        with mss.mss() as sct:
            self._last_baseline = self._get_frame(sct)

            while not self._stop_event.is_set():
                current_frame = self._get_frame(sct)
                change_pct = self._compute_change_pct(self._last_baseline, current_frame)

                if change_pct > self.sensitivity:
                    # Potential change detected - enter stability tracking
                    stable_count = 0
                    tracking_frame = current_frame
                    
                    while (stable_count < self.STABILITY_COUNT and not self._stop_event.is_set()):
                        time.sleep(self.STABILITY_INTERVAL)
                        
                        check_frame = self._get_frame(sct)
                        stability_change = self._compute_change_pct(tracking_frame, check_frame)

                        # print(stability_change)
                        
                        if stability_change < 0.0025: #0.005:  # < 0.5% = stable
                            stable_count += 1
                        else:
                            stable_count = 0  # Reset - still changing
                        
                        tracking_frame = check_frame
                    
                    # Stability achieved
                    if stable_count == self.STABILITY_COUNT:
                        print(f">>>>>> New subtitle...")
                        # self.ocr_callback()
                        
                        # Update baseline, cooldown
                        self._last_baseline = tracking_frame
                        time.sleep(self.COOLDOWN)
                
                time.sleep(self.SCAN_RATE)

    def start(self):
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join()
