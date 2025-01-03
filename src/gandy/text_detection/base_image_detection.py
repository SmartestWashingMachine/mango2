from gandy.full_pipelines.base_app import BaseApp
from gandy.utils.speech_bubble import SpeechBubble
from typing import List
from PIL import Image
import numpy as np
import copy
from gandy.state.config_state import config_state

class BaseImageDetection(BaseApp):
    def __init__(self):
        super().__init__()

    def process(self, image: Image) -> List[SpeechBubble]:
        return []

    def begin_process(self, *args, **kwargs) -> List[SpeechBubble]:
        return super().begin_process(*args, **kwargs)

    # Sorts a group of bbox tensors such that the tensors with the highest top-right / top-left values are first.
    # Note: This does not modify in place.
    def sort_bboxes(self, bboxes, image_width, image_height):
        # Create copy of bboxes C
        new_bboxes = copy.deepcopy(bboxes)

        if new_bboxes.shape[0] == 0:
            # No boxes to sort.
            return new_bboxes

        if config_state.sort_text_from_top_left:
            # Distance of x1 from (0, 0) point. (Mainly for Korean images)
            x = (bboxes[:, 0]) ** 2
        else:
            # Distance of x2 from (image_width, 0) point.
            x = (image_width - bboxes[:, 2]) ** 2

        # This still isn't perfect, but it gives slightly better ordering results on average.
        y = (
            bboxes[:, 1] ** 4
        ) * 2  # Y distance is penalized more heavily than X distance.
        distances = (x + y) ** 0.5

        sorted_indices = np.argsort(distances)  # Ascending order.

        li = len(sorted_indices)
        for i in range(li):
            sorted_index = sorted_indices[i]

            new_bboxes[i, :] = bboxes[sorted_index, :]

        return new_bboxes

    def unload_model(self):
        super().unload_model()
