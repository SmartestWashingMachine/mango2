from typing import List
from PIL.Image import Image
from gandy.utils.speech_bubble import SpeechBubble
from dataclasses import dataclass

NEARBY_PCT = 0.033


@dataclass
class Candidate:
    x1: float
    y1: float
    x2: float
    y2: float
    text: str

    is_vertical: bool

    def __init__(self, x1, y1, x2, y2, text):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.text = text

        height = self.y2 - self.y1
        width = self.x2 - self.x1
        asp_ratio = height / width

        self.is_vertical = asp_ratio >= 1.0


def _midp(b: Candidate):
    return b.x1 + ((b.x2 - b.x1) / 2)


def _box_b_is_left_or_right(box_a, box_b):
    """
    Returns "left" if box_b is to the left of box_a. Returns "right" if box_b is to the right of box_a. Returns "none" otherwise.
    """

    x_center_a = _midp(box_a)
    x_center_b = _midp(box_b)

    if x_center_b < x_center_a:
        return "left"
    elif x_center_b > x_center_a:
        return "right"
    else:
        return "none"


# Change image_length depending on if this is an X or Y point.
def _points_nearby(p1: float, p2: float, image_length: float):
    diff = abs(p1 - p2)

    return diff <= ((image_length * NEARBY_PCT))


def _merge_lines(tl_1: Candidate, tl_2: Candidate):
    merged = Candidate(
        x1=min(tl_1.x1, tl_2.x1),
        y1=min(tl_1.y1, tl_2.y1),
        x2=max(tl_1.x2, tl_2.x2),
        y2=max(tl_1.y2, tl_2.y2),
        text="",
    )

    is_rtl = tl_1.is_vertical or tl_2.is_vertical

    if _box_b_is_left_or_right(box_a=tl_1, box_b=tl_2) == "right":
        if is_rtl:
            # tl_2 is right of tl_1. RTL so tl_2 then tl_1.
            merged.text = tl_2.text + tl_1.text
        else:
            # tl_2 is right of tl_1. LTR so tl_1 then tl_2.
            merged.text = tl_1.text + tl_2.text
    else:
        if is_rtl:
            # tl_2 is left of tl_1. RTL so tl_1 then tl_2.
            merged.text = tl_1.text + tl_2.text
        else:
            # tl_2 is left of tl_1. LTR so tl_2 then tl_1.
            merged.text = tl_2.text + tl_1.text

    return merged


def _probably_merge_lines(
    tl_1: Candidate, tl_2: Candidate, img: Image, force_merge=False
):
    """
    Merges two text lines if conditions are met. Returns a list of one text line if the merge is successful, otherwise returns a list of two text lines.

    Conditions:
    1. Both text lines are vertical or horizontal lines (similar aspect ratios).
    2. Both text lines are nearby in the X axis if vertical, or Y axis if horizontal.
    """
    failure_state = [tl_1, tl_2]

    if force_merge:
        return [_merge_lines(tl_1, tl_2)]

    # Condition 2.
    if tl_1.is_vertical != tl_2.is_vertical:
        return failure_state

    img_width = img.width
    img_height = img.height

    if tl_1.is_vertical:
        # Condition 1. Nearby in X axis.
        if _points_nearby(tl_1.x1, tl_2.x2, img_width) or _points_nearby(
            tl_1.x2, tl_2.x1, img_width
        ):
            if _points_nearby(tl_1.y1, tl_2.y1, img_height) or _points_nearby(
                tl_1.y2, tl_2.y2, img_height
            ):
                return [_merge_lines(tl_1, tl_2)]
            else:
                return failure_state
        else:
            return failure_state
    else:
        # Condition 1. Nearby in Y axis.
        if _points_nearby(tl_1.y1, tl_2.y2, img_height) or _points_nearby(
            tl_1.y2, tl_2.y1, img_height
        ):
            if _points_nearby(tl_1.x1, tl_2.x1, img_width) or _points_nearby(
                tl_1.x2, tl_2.x2, img_width
            ):
                return [_merge_lines(tl_1, tl_2)]
            else:
                return failure_state
        else:
            return failure_state


def _filter_not_indices(arr: List, indices: List[int]):
    # Returns the list except for items at the indices specified.
    return [x for (i, x) in enumerate(arr) if i not in indices]


def _process_lines(text_lines: List[Candidate], img: Image, force_merge=False):
    for idx_i in range(len(text_lines)):
        for idx_j in range(len(text_lines)):
            if idx_i == idx_j:  # Ignore self.
                continue

            outp_lines = _probably_merge_lines(
                text_lines[idx_i], text_lines[idx_j], img, force_merge=force_merge
            )
            if len(outp_lines) == 1:
                # A merge was made!
                # This is inefficient, but we make no assumptions on how the text lines are sorted. It could still be better though.
                new_text_lines = _filter_not_indices(text_lines, [idx_i, idx_j])
                new_text_lines = new_text_lines + outp_lines
                return _process_lines(new_text_lines, img, force_merge)

    return text_lines


def join_nearby_speech_bubbles_for_source_texts(
    bboxes: List[SpeechBubble], source_texts: List[str], rgb_image: Image
):
    """
    Merge nearby speech bubbles. Only used for YOLO EX Line variant and when translating image-to-image.
    """
    if len(bboxes) != len(source_texts):
        raise RuntimeError(
            f"Bad bbox to text length: Bboxes N={len(bboxes)} != SourceTexts N={len(source_texts)}"
        )

    candidates = [
        Candidate(x1=b[0], y1=b[1], x2=b[2], y2=b[3], text=s)
        for (b, s) in zip(bboxes, source_texts)
    ]

    merged_candidates = _process_lines(candidates, rgb_image, force_merge=False)

    new_source_texts = [m.text for m in merged_candidates]
    new_bboxes = [[m.x1, m.y1, m.x2, m.y2] for m in merged_candidates]
    return new_bboxes, new_source_texts
