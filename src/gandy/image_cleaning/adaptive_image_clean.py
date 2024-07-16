from PIL import ImageDraw, Image
from gandy.image_cleaning.base_image_clean import BaseImageClean
import numpy as np
from math import floor


# From: https://stackoverflow.com/questions/1855884/determine-font-color-based-on-background-color
def contrasting_text_color(bg_color):
    a = 1.0 - ((0.299 * bg_color[0] + 0.587 * bg_color[1] + 0.114 * bg_color[2]) / 255)

    if a < 0.5:
        return "black"
    else:
        return "white"


def zoom_out(floored_bbox, image: Image.Image, factor=0.05):
    # Factor = X% of the bbox's size is used to zoom out.
    x_out = floor((floored_bbox[2] - floored_bbox[0]) * factor)
    y_out = floor((floored_bbox[3] - floored_bbox[1]) * factor)

    x1 = max(floored_bbox[0] - x_out, 0)
    y1 = max(floored_bbox[1] - y_out, 0)
    x2 = min(floored_bbox[2] + x_out, image.width - 1)
    y2 = min(floored_bbox[3] + y_out, image.height - 1)

    return (x1, y1, x2, y2)


# Fills the bounding box areas with the average color found in the image.
class AdaptiveImageCleanApp(BaseImageClean):
    def __init__(self):
        super().__init__()

    def process(self, image, bboxes):
        input_image = image.copy()
        input_draw = ImageDraw.Draw(input_image)

        np_image = np.array(input_image)  # HWC

        text_colors = []

        for s in bboxes:
            # Coordinates of bounding box
            x1, y1, x2, y2 = floor(s[0]), floor(s[1]), floor(s[2]), floor(s[3])

            # Coordinates of area slightly bigger than bounding box.
            z_x1, z_y1, z_x2, z_y2 = zoom_out([x1, y1, x2, y2], image)

            np_image[
                y1:y2, x1:x2, :
            ] = 127  # Note this may mask legitimate colors too (and affect other text details).
            np_subset = np_image[z_y1:z_y2, z_x1:z_x2, :]

            try:
                # Crop out bounding box area itself.
                mask = np.ma.masked_where(np_subset == 127, np_subset)
                avg_color = mask.mean(axis=(0, 1))
            except:
                avg_color = [255.0, 255.0, 255.0]

            try:
                bg_color = (
                    floor(avg_color[0]),
                    floor(avg_color[1]),
                    floor(avg_color[2]),
                )
            except:
                bg_color = (255, 255, 255)

            input_draw.rounded_rectangle(
                s, outline=bg_color, fill=bg_color, width=1, radius=30
            )

            text_colors.append(contrasting_text_color(bg_color))

        return input_image, text_colors
