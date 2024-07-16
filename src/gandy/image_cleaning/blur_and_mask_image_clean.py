from PIL import Image, ImageFilter
import numpy as np
from math import floor
import cv2
from typing import List
from gandy.utils.speech_bubble import SpeechBubble
from gandy.image_cleaning.tnet_image_clean import TNetImageClean


class BlurMaskImageCleanApp(TNetImageClean):
    def __init__(self):
        super().__init__()

    def process(self, image: Image.Image, bboxes: List[SpeechBubble]):
        easy_mask, added_to_easy_mask = super().process(
            image, bboxes, return_masks_only=True
        )

        inpainted_image = cv2.inpaint(
            np.array(image), easy_mask, inpaintRadius=1, flags=cv2.INPAINT_TELEA
        )
        inpainted_image = Image.fromarray(inpainted_image)

        hard_mask = np.zeros(
            (inpainted_image.size[1], inpainted_image.size[0]), dtype=np.uint8
        )

        any_added_to_hard_mask = False

        for idx, bbox in bboxes:
            if added_to_easy_mask[idx]:
                continue

            x1, y1, x2, y2 = bbox
            x1 = floor(x1)
            y1 = floor(y1)
            x2 = floor(x2)
            y2 = floor(y2)

            hard_mask[y1:y2, x1:x2] = 255

            any_added_to_hard_mask = True

        if any_added_to_hard_mask:
            blurred_image = inpainted_image.filter(ImageFilter.GaussianBlur(5))
            hard_mask = Image.fromarray(hard_mask, mode="L")
            inpainted_image.paste(blurred_image, hard_mask)

        return inpainted_image
