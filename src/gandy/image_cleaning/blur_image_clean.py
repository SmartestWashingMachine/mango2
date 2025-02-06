from PIL import ImageDraw, Image, ImageFilter
import numpy as np
from math import floor

from gandy.image_cleaning.base_image_clean import BaseImageClean


class BlurImageCleanApp(BaseImageClean):
    def __init__(self):
        super().__init__()

    def process(self, image, bboxes):
        input_image = image.copy()

        # Size gives width, height.
        mask = np.zeros(
            (input_image.size[1], input_image.size[0]),
            dtype=np.uint8,
        )  # 255 for text regions. 0 otherwise.
        mask = Image.fromarray(mask, mode="L")

        img_area = max(1, input_image.width * input_image.height)

        for s in bboxes:
            x1, y1, x2, y2 = s
            x1 = floor(x1)
            y1 = floor(y1)
            x2 = floor(x2)
            y2 = floor(y2)

            region = input_image.crop((x1, y1, x2, y2)) # Replaces other blurs since we're not using input_image.

            box_area = (y2 - y1) * (x2 - x1)
            blur_radius = int((box_area / img_area) * 100 * 10)

            blurred_region = region.filter(ImageFilter.GaussianBlur(blur_radius))

            input_image.paste(blurred_region, (x1, y1))

            # Now we want to smoothen the edges of the blurred regions.
            # 1. Create a separate mask for each bounding box.
            temp_mask = np.zeros(
                (input_image.size[1], input_image.size[0]),
                dtype=np.uint8,
            )
            temp_mask[y1:y2, x1:x2] = 255
            temp_mask = Image.fromarray(temp_mask, mode="L")
            temp_mask = temp_mask.filter(ImageFilter.GaussianBlur(10))

            # 2. Combine the temporary mask with the main mask.
            mask = Image.composite(temp_mask, mask, temp_mask)

        mask = mask.filter(ImageFilter.GaussianBlur(10))  # Additional blur for smoother edges

        return Image.composite(input_image, image, mask)
