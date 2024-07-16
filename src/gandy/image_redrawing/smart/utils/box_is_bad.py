from gandy.image_redrawing.smart.utils.text_overflows_image import text_overflows_image
from gandy.image_redrawing.smart.utils.box_overlaps import box_overlaps
from gandy.image_redrawing.smart.magic_box import MagicBox
from gandy.image_redrawing.smart.constants import CLOSE_FACTOR
from typing import List


def box_is_bad(
    min_font_size,
    text,
    box: MagicBox,
    text_align_direction,
    draw,
    img,
    other_boxes: List[MagicBox],
    with_margin=True,
):
    """
    Returns True if the text overflows the image in ANY direction or overlaps any other text boxes.
    """
    text_box = box.get_text_box(min_font_size, text_align_direction, draw, text=text)

    if with_margin:
        # image is only used here for margin calculation.
        mx = img.width * CLOSE_FACTOR
        my = img.height * CLOSE_FACTOR
        text_box = [
            text_box[0] - mx,
            text_box[1] - my,
            text_box[2] + mx,
            text_box[3] + my,
            text,
        ]

    other_text_boxes = [
        b.get_text_box(min_font_size, text_align_direction, draw) for b in other_boxes
    ]

    if text_overflows_image(
        min_font_size,
        text,
        box=None,
        img=img,
        draw=draw,
        direction="lrud",
        text_direction=text_align_direction,
        text_box=text_box,
    ) or box_overlaps(text_box, other_text_boxes):
        return True  # Failure condition.

    return False
