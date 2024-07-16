from gandy.image_redrawing.base_image_redraw import BaseImageRedraw
from gandy.utils.speech_bubble import SpeechBubble
from typing import List


def to_amg(image, bboxes: List[SpeechBubble], target_texts: List[str]):
    amg_data = {
        "image": image,  # Converted to base64 in task1_route.
        "annotations": [],
    }

    for i, s_bb in enumerate(bboxes):
        text = target_texts[i]

        x1 = s_bb[0]
        y1 = s_bb[1]
        x2 = s_bb[2]
        y2 = s_bb[3]

        amg_data["annotations"].append(
            {
                "text": text,
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
            }
        )

    return amg_data


class AMGConvertApp(BaseImageRedraw):
    def __init__(self):
        super().__init__()

    def process(self, image, bboxes, target_texts, *args, **kwargs):
        return to_amg(image, bboxes, target_texts)
