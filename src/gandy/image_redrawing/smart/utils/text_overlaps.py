from gandy.image_redrawing.smart.magic_box import MagicBox
from gandy.image_redrawing.smart.constants import CLOSE_FACTOR
from gandy.image_redrawing.smart.utils.box_overlaps import box_overlaps
from typing import List


def text_overlaps(
    font_size,
    text,
    box: MagicBox,
    other_boxes: List[MagicBox],
    direction="center",
    draw=None,
    return_indices=False,
    with_margin=False,
    image=None,
):
    """
    Returns True if the text overlaps with any other texts. We usually call this on the other boxes excluding the speech box this text is used on.
    """
    text_box = box.get_text_box(font_size, direction, draw, text=text)

    if with_margin:
        # image is only used here for margin calculation.
        mx = image.width * CLOSE_FACTOR
        my = image.height * CLOSE_FACTOR

        text_box = [
            text_box[0] - mx,
            text_box[1] - my,
            text_box[2] + mx,
            text_box[3] + my,
            text,
        ]

    other_text_boxes = [b.get_text_box(font_size, direction, draw) for b in other_boxes]
    return box_overlaps(text_box, other_text_boxes, return_indices=return_indices)
