from PIL import ImageDraw, Image, ImageFilter
import numpy as np
from math import floor

from gandy.image_cleaning.base_image_clean import BaseImageClean


class BlurImageCleanApp(BaseImageClean):
    def __init__(self):
        super().__init__()

    def process(self, image, bboxes):
        input_image = image.copy()
        blurred_image = input_image.filter(ImageFilter.GaussianBlur(5))

        # Size gives width, height.
        mask = np.zeros(
            (input_image.size[1], input_image.size[0]),
            dtype=np.uint8,
        )  # 255 for text regions. 0 otherwise.

        for s in bboxes:
            x1, y1, x2, y2 = s
            x1 = floor(x1)
            y1 = floor(y1)
            x2 = floor(x2)
            y2 = floor(y2)

            mask[y1:y2, x1:x2] = 255

        mask = Image.fromarray(mask, mode="L")
        mask = mask.filter(ImageFilter.GaussianBlur(6))

        input_image.paste(blurred_image, mask)
        return input_image
