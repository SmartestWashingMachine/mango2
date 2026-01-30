from PIL import Image
from gandy.image_cleaning.base_image_clean import BaseImageClean
import numpy as np
from math import floor
import cv2


# From: https://stackoverflow.com/questions/1855884/determine-font-color-based-on-background-color
def contrasting_text_color(bg_color):
    a = 1.0 - ((0.299 * bg_color[0] + 0.587 * bg_color[1] + 0.114 * bg_color[2]) / 255)

    if a < 0.5:
        return "black"
    else:
        return "white"


def zoom_out(bbox, image: Image.Image, px = 3):
    x1 = floor(max(bbox[0] - px, 0))
    y1 = floor(max(bbox[1] - px, 0))
    x2 = floor(min(bbox[2] + px, image.width - 1))
    y2 = floor(min(bbox[3] + px, image.height - 1))

    return (x1, y1, x2, y2)


# Fills the line bounding box areas with the most common color found in the image excluding the line boxes.
class AdaptiveImageCleanLinerApp(BaseImageClean):
    def __init__(self):
        super().__init__()

    def process(self, image, bboxes, line_bboxes):
        # line_bboxes = list of lists. Each parent list corresponds to one text region, and the items correspond to the line regions.

        input_image = image.copy()
        np_image = np.array(input_image) # HWC

        text_colors = []

        for grp_idx in range(len(line_bboxes)):
            bbox = bboxes[grp_idx]

            # First we get the average color excluding line regions.
            line_only_mask = np.zeros_like(np_image) # 1 = line area. 0 = background area.
            line_outline_mask = np.zeros_like(np_image) # Diluted version of the mask.

            for line in line_bboxes[grp_idx]: # [x1, y1, x2, y2]
                # Rescale since "line" only gives coordinates relative to the cropped text region, not the entire image.
                line = [line[0] + bbox[0], line[1] + bbox[1], line[2] + bbox[0], line[3] + bbox[1]]

                box = zoom_out(line, image, px=3)
                line_only_mask[box[1]:box[3], box[0]:box[2], :] = 1 # HW

                box = zoom_out(line, image, px=12)
                line_outline_mask[box[1]:box[3], box[0]:box[2], :] = 1

            # Why median? I think average will lead to an unhappy medium, e.g: slightly darker than the speech bubble background.
            in_region_outside_lines_mask = (line_only_mask == 0) & (line_outline_mask == 1)
            in_region_outside_lines = np.ma.masked_where(in_region_outside_lines_mask == 1, np_image)
            common_color = np.floor(np.median(in_region_outside_lines, axis=(0, 1))) # [3 (channels)]

            # Then we redraw over each line region. No rounded borders.
            across_channels = (line_only_mask == 1)[:, :, 0] # [H, W]

            np_mask = np.full_like(np_image, fill_value=0, dtype=np.uint8)
            np_mask[across_channels] = 255

            # TODO: simplify the code. Previously the code did not inpaint at all, instead using the outline mask with median but the results were disappointing.
            np_image = cv2.inpaint(
                np_image, np_mask[:, :, 0], inpaintRadius=3, flags=cv2.INPAINT_TELEA
            )

            text_colors.append(contrasting_text_color(common_color))

        input_image = Image.fromarray(np_image)
        return input_image, text_colors
