from gandy.image_redrawing.smarter.checks import text_intersects, text_intersects_on_direction, text_overflows
from gandy.image_redrawing.smarter.actions.move_action import MoveAction
from gandy.image_redrawing.smarter.text_box import TextBox
from typing import List
from PIL import Image

def get_wrong_direction_from_offset(shift_pct: List[float]):
    if shift_pct[0] < 0:
        return "l"
    if shift_pct[0] > 0:
        return "r"
    if shift_pct[1] < 0:
        return "u"
    if shift_pct[1] > 0:
        return "d"
    return ""

def push_others(boxes: List[TextBox], shift_pct: List[float], img: Image.Image):
    # Can't mutate in-place; affects originals.
    boxes = [TextBox.clone(b) for b in boxes]
 
    for idx in range(len(boxes)):
        others = boxes[:idx] + boxes[idx + 1:]
        if text_intersects(boxes[idx], others):
            pushed = TextBox.shift_from(boxes[idx], offset_pct=shift_pct)
            if not text_overflows(pushed, img, get_wrong_direction_from_offset(shift_pct)):
                boxes[idx] = pushed

    return boxes
        

class MoveAndPushAction(MoveAction):
    def shift_others(self, new_candidate: TextBox, others: List[TextBox], img: Image.Image):
        # Shift the other boxes away if they overlap.
        shift_pct = [(x * 2) for x in self.offset_pct]
        new_others = push_others([new_candidate] + others, shift_pct, img)[1:]

        return new_others

    def action_process(self, time_left: int, candidate, others, img, original, iterations_done: int):
        new_candidate = TextBox.shift_from(candidate, offset_pct=self.offset_pct)
        new_others = self.shift_others(new_candidate, others, img)

        return new_candidate, new_others