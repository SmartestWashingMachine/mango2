from gandy.text_detection.base_image_detection import BaseImageDetection
from gandy.utils.fancy_logger import logger
from gandy.state.config_state import config_state
import numpy as np

# Code reused from image_redraw_big_global.py
def box_overlaps(box, other_boxes):
    """
    Returns True if box overlaps with any of the other boxes, and False otherwise.

    Assume other_boxes is a list of list of coords, and box is a list of coords.
    """
    a_x1, a_y1, a_x2, a_y2 = box

    def _is_overlapping_1d(a_1, b_1, a_2, b_2):
        # a_2 must be greater than a_1. b_2 must be greater than b_1. a_1 and a_2 must be for the same box. b_1 and b_2 must be for another same box.
        return a_2 >= b_1 and b_2 >= a_1

    for other in other_boxes:
        # (x1, y1, x2, y2)
        b_x1, b_y1, b_x2, b_y2 = other

        # From: https://stackoverflow.com/questions/20925818/algorithm-to-check-if-two-boxes-overlap
        is_overlapping = _is_overlapping_1d(
            a_x1, b_x1, a_x2, b_x2
        ) and _is_overlapping_1d(a_y1, b_y1, a_y2, b_y2)
        if is_overlapping:
            return other

    return None

# Similar to IoU
def box_b_in_box_a_thr(box_a, box_b):
    x_a = max(box_a[0], box_b[0])
    y_a = max(box_a[1], box_b[1])
    x_b = min(box_a[2], box_b[2])
    y_b = min(box_a[3], box_b[3])

    inter = abs(max((x_b - x_a, 0)) * max((y_b - y_a), 0))

    if inter == 0:
        return 0

    box_b_area = abs((box_b[2] - box_b[0]) * (box_b[3] - box_b[1]))

    iou = inter / float(box_b_area)

    return iou

class UnionImageDetectionApp(BaseImageDetection):
    def __init__(self, td_model_app: BaseImageDetection, line_model_app: BaseImageDetection):
        """
        Slower than the RCNNImageDetectionApp, but more precise.
        """
        super().__init__()

        self.td_model_app = td_model_app
        self.line_model_app = line_model_app

    def can_load(self):
        return self.td_model_app.can_load() and self.line_model_app.can_load()

    def load_model(self):
        if not self.loaded:
            logger.info(
                f"Loading Union detection variant."
            )

            self.td_model_app.load_model()
            self.line_model_app.load_model()

            logger.info("Done loading Union detection variant!")

            return super().load_model()

    def process(self, image, do_sort=True, return_list=True):
        td_bboxes = self.td_model_app.begin_process(image) # list of bboxes
        line_bboxes = self.line_model_app.begin_process(image)

        n_lines_before = len(line_bboxes)

        candidate_lines = []
        for box_b in line_bboxes:
            # If the line box is not making contact with any text box, add that line box.
            overlapping_box = box_overlaps(box_b, td_bboxes)
            if overlapping_box:
                # If the line box DOES make contact with a text box, expand that text box in terms of width/height.
                overlapping_box[0] = min(box_b[0], overlapping_box[0])
                overlapping_box[1] = min(box_b[1], overlapping_box[1])
                overlapping_box[2] = max(box_b[2], overlapping_box[2])
                overlapping_box[3] = max(box_b[3], overlapping_box[3])

                continue

            candidate_lines.append(box_b)

            # if not any(box_b_in_box_a(box_a=box_a, box_b=box_b) for box_a in td_bboxes):
                # candidate_lines.append(box_b)

        logger.debug(f"Filtered line bboxes in Union variant from {n_lines_before} to {len(candidate_lines)}")

        n_lines_before = len(candidate_lines)

        # Merge nearby line boxes so that they become full text boxes.
        # Removed since I don't like it.
        # candidate_lines = join_nearby_speech_bubbles_only(bboxes=candidate_lines, rgb_image=image)
        candidate_tds = [d for d in td_bboxes]

        logger.debug(f"Joined nearby line bboxes in Union variant from {n_lines_before} to {len(candidate_lines)}")

        bboxes = candidate_lines + candidate_tds

        # Filter out boxes that overlap too much.
        new_bboxes = []
        for idx in range(len(bboxes)):
            others = bboxes[:idx] + bboxes[(idx + 1):]

            if not any(box_b_in_box_a_thr(box_b=bboxes[idx], box_a=o) >= 0.8 for o in others):
                new_bboxes.append(bboxes[idx])
        bboxes = new_bboxes

        bboxes = np.array(bboxes)

        logger.debug("Sorting union boxes...")
        if do_sort:
            image_width, image_height = image.size
            bboxes = self.sort_bboxes(bboxes, image_width, image_height)

        if return_list:
            return bboxes.tolist()

        return bboxes
