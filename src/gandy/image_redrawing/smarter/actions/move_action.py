from gandy.image_redrawing.smarter.checks import text_intersects, text_intersects_on_direction, text_overflows
from gandy.image_redrawing.smarter.actions.action import Action
from gandy.image_redrawing.smarter.text_box import TextBox
from typing import List

class MoveAction(Action):
    def __init__(self, offset_pct: List[float], fatal_error_overlapping_direction: str, stackable=False, action_name = "Move") -> None:
        super().__init__(stackable, action_name)

        self.offset_pct = offset_pct
        self.fatal_error_overlapping_direction = fatal_error_overlapping_direction

    def get_non_fatal_error_overlapping_direction(self):
        dirs = "lrud"
        for c in self.fatal_error_overlapping_direction:
            dirs = dirs.replace(c, "")

        return dirs

    def fatal_error(self, candidate, others, img):
        if text_overflows(candidate, img, direction=self.get_non_fatal_error_overlapping_direction()):
            print('Box overflows image.')
            return True
        if text_intersects_on_direction(candidate, others, img, self.fatal_error_overlapping_direction):
            print('Box intersects on direction.')
            return True
        return False

    def non_fatal_error(self, candidate, others, img):
        if text_intersects(candidate, others):
            return True
        if text_overflows(candidate, img, direction=self.fatal_error_overlapping_direction):
            return True

        return False
    
    def action_process(self, time_left: int, candidate, others, img, original, iterations_done: int):
        new_candidate = TextBox.shift_from(candidate, offset_pct=self.offset_pct)

        return new_candidate, others
    