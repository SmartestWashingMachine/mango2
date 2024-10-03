from gandy.image_redrawing.smarter.text_box import TextBox
from gandy.image_redrawing.smarter.image_fonts import print_spam
from typing import List
from PIL import Image

def text_intersects(box: TextBox, other_boxes: List[TextBox], return_indices=False):
    """
    Returns True if box overlaps with any of the other boxes, and False otherwise.

    Assume other_boxes is a list of list of coords, and box is a list of coords.
    """

    indices = []

    def _is_overlapping_1d(a_1, b_1, a_2, b_2):
        # a_2 must be greater than a_1. b_2 must be greater than b_1. a_1 and a_2 must be for the same box. b_1 and b_2 must be for another same box.
        return a_2 >= b_1 and b_2 >= a_1

    for idx, other in enumerate(other_boxes):
        # (x1, y1, x2, y2, text)

        # From: https://stackoverflow.com/questions/20925818/algorithm-to-check-if-two-boxes-overlap
        is_overlapping = _is_overlapping_1d(
            box.x1, other.x1, box.x2, other.x2
        ) and _is_overlapping_1d(box.y1, other.y1, box.y2, other.y2)
        if is_overlapping:
            if return_indices:
                indices.append(idx)
            else:
                print_spam(f'OVERLAPPING {box} WITH: {other}')
                return True

    if return_indices:
        return indices

    return False

def text_overflows(cand1: TextBox, img: Image, direction = "lrud", with_margin = "x"):
    """
    Checks if the text box overflows the image.
    """
    margin_pct = 0.025
    x_marg = (img.width * margin_pct)
    y_marg = (img.height * margin_pct)

    with_margin_x = "x" in with_margin
    with_margin_y = "y" in with_margin

    x_min = x_marg if with_margin_x else 0
    y_min = y_marg if with_margin_y else 0
    x_max = (img.width - x_marg) if with_margin_x else img.width
    y_max = (img.height - y_marg) if with_margin_y else img.height

    if cand1.x1 <= x_min and "l" in direction:
        print_spam('BOX OVERFLOWS "LEFT" IMAGE.')
        return True
    if cand1.y1 <= y_min and "u" in direction:
        print_spam('BOX OVERFLOWS "ABOVE" IMAGE.')
        return True
    if cand1.x2 >= x_max and "r" in direction:
        print_spam('BOX OVERFLOWS "RIGHT" IMAGE.')
        return True
    if cand1.y2 >= y_max and "d" in direction:
        print_spam('BOX OVERFLOWS "BELOW" IMAGE.')
        return True

    return False

def _box_b_is_left_or_right(box_a: TextBox, box_b: TextBox):
    """
    Returns "left" if box_b is to the left of box_a. Returns "right" if box_b is to the right of box_a. Returns "none" otherwise.
    """
    # img_width, img_height = img.width, img.height

    def _midp(b):
        return b.x1 + ((b.x2 - b.x1) / 2)

    x_center_a = _midp(box_a)
    x_center_b = _midp(box_b)

    if x_center_b < x_center_a:
        return "left"
    elif x_center_b > x_center_a:
        return "right"
    else:
        return "none"
    
def _box_b_is_up_or_down(box_a: TextBox, box_b: TextBox):
    def _midp(b):
        return b.y1 + ((b.y2 - b.y1) / 2)

    y_center_a = _midp(box_a)
    y_center_b = _midp(box_b)

    if y_center_b < y_center_a:
        return "up"
    elif y_center_b > y_center_a:
        return "down"
    else:
        return "none"

def text_intersects_on_direction(cand1: TextBox, others: List[TextBox], image: Image.Image, direction_to_check: str):
    """
    Returns True if the text overlaps with any other text boxes that are to the (left/right DEPENDING on 'direction_to_check') of the text.
    """
    cand1 = cand1.get_with_margin()

    overlapping_indices = text_intersects(cand1, others, return_indices=True)
    for idx in overlapping_indices:
        other = others[idx]

        other_is_to_the = _box_b_is_left_or_right(box_a=cand1, box_b=other)

        if other_is_to_the == "left" and "l" in direction_to_check:
            return True
        if other_is_to_the == "right" and "r" in direction_to_check:
            return True
        
        other_is_to_the = _box_b_is_up_or_down(box_a=cand1, box_b=other)
        if other_is_to_the == "down" and "u" in direction_to_check:
            return True
        if other_is_to_the == "up" and "d" in direction_to_check:
            return True

    return False
