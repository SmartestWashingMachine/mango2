from gandy.image_redrawing.smart.magic_box import MagicBox
from gandy.image_redrawing.smart.utils.box_is_bad import box_is_bad
from typing import List


def recenter_box(
    min_font_size,
    text,
    box: MagicBox,
    text_align_direction,
    draw,
    img,
    other_boxes: List[MagicBox],
):
    """
    Try to shift the x1 for a speech box so that the text inside it would appear to be horizontally centered.
    """
    text_box = box.get_text_box(min_font_size, text_align_direction, draw, text=text)
    x2_shift = max((text_box[2] - box[2]) / 2.0, 0)

    new_box = MagicBox(box[0], box[1], box[2], box[3], box[4], box.can_change_font_size)
    new_box[0] = new_box[0] - x2_shift
    # new_box[2] = new_box[2] + x2_shift # Is this right? Seems to work better

    if box_is_bad(
        min_font_size, text, new_box, text_align_direction, draw, img, other_boxes
    ):
        return box

    return new_box
