from gandy.full_pipelines.base_app import BaseApp
from PIL.Image import Image
from typing import List
from gandy.utils.speech_bubble import SpeechBubble


class BaseImageClean(BaseApp):
    def __init__(self):
        super().__init__()

    def process(self, image: Image, bboxes: List[SpeechBubble]):
        return image

    def begin_process(self, *args, **kwargs) -> Image:
        return super().begin_process(*args, **kwargs)

    def unload_model(self):
        super().unload_model()
