from typing import List
from gandy.image_redrawing.smart.magic_box import MagicBox


def box_overlaps(box, other_boxes: List[MagicBox], return_indices=False):
    """
    Returns True if box overlaps with any of the other boxes, and False otherwise.

    Assume other_boxes is a list of list of coords, and box is a list of coords.
    """
    a_x1, a_y1, a_x2, a_y2, _ = box

    indices = []

    def _is_overlapping_1d(a_1, b_1, a_2, b_2):
        # a_2 must be greater than a_1. b_2 must be greater than b_1. a_1 and a_2 must be for the same box. b_1 and b_2 must be for another same box.
        return a_2 >= b_1 and b_2 >= a_1

    for idx, other in enumerate(other_boxes):
        # (x1, y1, x2, y2, text)
        b_x1, b_y1, b_x2, b_y2, _ = other

        # From: https://stackoverflow.com/questions/20925818/algorithm-to-check-if-two-boxes-overlap
        is_overlapping = _is_overlapping_1d(
            a_x1, b_x1, a_x2, b_x2
        ) and _is_overlapping_1d(a_y1, b_y1, a_y2, b_y2)
        if is_overlapping:
            if return_indices:
                indices.append(idx)
            else:
                return True

    if return_indices:
        return indices

    return False
