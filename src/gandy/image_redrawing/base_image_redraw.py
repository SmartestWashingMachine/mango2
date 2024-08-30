from gandy.full_pipelines.base_app import BaseApp
from gandy.utils.speech_bubble import SpeechBubble
from PIL import Image
from typing import List, Union


class BaseImageRedraw(BaseApp):
    def __init__(self):
        super().__init__()

    def uppercase_text(self, text: str):
        return text.upper()

    def get_text_color(
        self, text_colors: Union[List[str], None], idx, default_color="black"
    ):
        return text_colors[idx] if text_colors is not None else default_color

    def get_stroke_color(self, text_colors: Union[List[str], None], idx):
        if text_colors is not None:
            if text_colors[idx] == "white":
                return "black"  # #000
            else:
                return "white"

        return "white"

    def process(
        self,
        image: Image.Image,
        bboxes: List[SpeechBubble],
        target_texts: List[str],
        *args,
        **kwargs
    ):
        return image

    def unload_model(self):
        super().unload_model()
