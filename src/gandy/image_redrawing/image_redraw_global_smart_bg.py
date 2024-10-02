from gandy.image_redrawing.image_redraw_global_smarter import ImageRedrawGlobalSmarter, get_vertical_spacing
from random import choices
from gandy.utils.compute_stroke_size import compute_stroke_size
from gandy.image_redrawing.smarter.text_box import TextBox, FONT_MANAGER
from typing import List
from PIL import Image, ImageDraw

def add_padding(box, img):
    padding_pct = 0.05

    width = box[2] - box[0]
    height = box[3] - box[1]

    xa = int(width * padding_pct)
    ya = int(height * padding_pct)

    return [
        max(box[0] - xa, 0),
        max(box[1] - ya, 0),
        min(box[2] + xa, img.width - 1),
        min(box[3] + ya, img.height - 1),
    ]


def get_center_of_box(box):
    return (
        box[0] + ((box[2] - box[0]) / 2),
        box[1] + ((box[3] - box[1]) / 2),
    )


class ImageRedrawGlobalSmartBackgroundApp(ImageRedrawGlobalSmarter):
    def __init__(self):
        super().__init__()

    def redraw_from_tboxes(self, image: Image.Image, draw: ImageDraw.ImageDraw, text_boxes: List[TextBox], text_colors):
        for idx, tb in enumerate(text_boxes):
            box = [tb.x1, tb.y1, tb.x2, tb.y2]

            fill_col = 'white'
            if text_colors is not None and len(text_colors) > idx:
                fill_col = 'white' if text_colors['idx'] == 'black' else 'black'

            draw.rounded_rectangle(
                add_padding(box, image),
                fill=fill_col,
                radius=int(1 + (image.width * 0.005) + (image.height * 0.005)),
            )

        return super().redraw_from_tboxes(image, draw, text_boxes, text_colors)

