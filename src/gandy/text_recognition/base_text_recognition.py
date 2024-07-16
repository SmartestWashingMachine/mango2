import cv2
import numpy as np
from PIL.Image import Image
from gandy.utils.speech_bubble import SpeechBubble
from typing import List
from gandy.full_pipelines.base_app import BaseApp


class BaseTextRecognition(BaseApp):
    def __init__(self, merge_split_lines=True, preload=False):
        self.merge_split_lines = merge_split_lines
        super().__init__(preload)

    def process(
        self, image: Image, bboxes: List[SpeechBubble], text_line_app, *args, **kwargs
    ):
        return ["" for b in bboxes], None, None

    def unload_model(self):
        pass
