from gandy.image_redrawing.smart.magic_box import MagicBox
from gandy.image_redrawing.smart.constants import CLOSE_FACTOR
from gandy.image_redrawing.smart.utils.box_overlaps import box_overlaps
from gandy.image_redrawing.smart.utils.box_is_lr import box_b_is_left_or_right
from typing import List


def text_overlaps_on_direction(
    font_size,
    text,
    box: MagicBox,
    other_boxes: List[MagicBox],
    text_align_direction="center",
    direction_to_check="l",
    draw=None,
    with_margin=False,
    image=None,
):
    """
    Returns True if the text overlaps with any other text boxes that are to the (left/right DEPENDING on 'direction_to_check') of the text.

    Used to reject step 1 or step 2.
    """
    text_box = box.get_text_box(font_size, text_align_direction, draw, text=text)

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

    other_text_boxes = [
        b.get_text_box(font_size, text_align_direction, draw) for b in other_boxes
    ]
    overlapping_indices = box_overlaps(text_box, other_text_boxes, return_indices=True)
    for idx in overlapping_indices:
        other = other_boxes[idx]  # TODO: Use other text box maybe instead?

        other_is_to_the = box_b_is_left_or_right(box_a=text_box, box_b=other)
        if other_is_to_the == "left" and direction_to_check == "l":
            return True
        elif other_is_to_the == "right" and direction_to_check == "r":
            return True

    return False
