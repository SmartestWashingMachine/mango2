from gandy.image_redrawing.physics.text_block import TextBlock
from gandy.utils.speech_bubble import SpeechBubble
from typing import List

def bbox_width(bb: SpeechBubble):
    return bb[2] - bb[0]

def bbox_height(bb: SpeechBubble):
    return bb[3] - bb[1]

def bbox_center(bb: SpeechBubble):
    return [
        bb[0] + (bbox_width(bb) / 2),
        bb[1] + (bbox_height(bb) / 2),
    ]
    # return [bb[0] + ((bb[2] - bb[0]) / 2), bb[1] + ((bb[3] - bb[1]) / 2)]

def bbox_area(bb: SpeechBubble):
    return bbox_width(bb) * bbox_height(bb)

def bboxes_overlap(box1, box2, margin=0):
    """
    Determines if two boxes overlap or are within a given margin.
    Each box is [x_min, y_min, x_max, y_max].
    """
    # Check if the boxes do NOT overlap (including the margin)
    # If box1 is entirely to the left of box2 (with margin)
    if box1[2] + margin < box2[0]:
        return False
    # If box1 is entirely to the right of box2 (with margin)
    if box1[0] - margin > box2[2]:
        return False
    # If box1 is entirely below box2 (with margin)
    if box1[3] + margin < box2[1]:
        return False
    # If box1 is entirely above box2 (with margin)
    if box1[1] - margin > box2[3]:
        return False

    # If none of the above conditions are met, they must overlap or be within the margin
    return True