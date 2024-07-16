from PIL import Image
import numpy as np
from gandy.image_cleaning.tnet_image_clean import TNetImageClean


class TextFillCleanApp(TNetImageClean):
    def __init__(self):
        super().__init__()

    def process(self, image: Image.Image, bboxes):
        easy_mask, added_to_easy_mask = super().process(
            image, bboxes, return_masks_only=True
        )

        easy_mask = Image.fromarray(easy_mask[:, :, 0].astype(np.uint8), mode="L")
        image.paste((255, 255, 255), mask=easy_mask)

        return image
