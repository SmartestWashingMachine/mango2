from gandy.image_redrawing.smarter.checks import text_intersects, text_intersects_on_direction, text_overflows
from gandy.image_redrawing.smarter.actions.action import Action
from gandy.image_redrawing.smarter.text_box import TextBox
from gandy.image_redrawing.smarter.image_fonts import print_spam
from typing import List

class MoveAction(Action):
    def __init__(self, offset_pct: List[float], fatal_error_overlapping_direction: str, stackable=False, action_name = "Move", max_iterations: int = 30) -> None:
        super().__init__(stackable, action_name, max_iterations=max_iterations)

        self.offset_pct = offset_pct
        self.fatal_error_overlapping_direction = fatal_error_overlapping_direction

    def get_non_fatal_error_overlapping_direction(self):
        dirs = "lrud"
        for c in self.fatal_error_overlapping_direction:
            dirs = dirs.replace(c, "")

        return dirs
    
    def get_opposite_direction(self, direction: str):
        dirs = ""
        if "l" in direction:
            dirs += "r"
        if "r" in direction:
            dirs += "l"
        if "u" in direction:
            dirs += "d"
        if "d" in direction:
            dirs += "u"
        
        return dirs

    def fatal_error(self, candidate, others, img, prev_candidate, *args, **kwargs):
        if text_overflows(candidate, img, direction=self.get_non_fatal_error_overlapping_direction()):
            print_spam('Box overflows image.')
            return True
        if text_intersects_on_direction(candidate, others, img, direction_to_check=self.fatal_error_overlapping_direction) and text_intersects_on_direction(prev_candidate, others, img, direction_to_check=self.get_opposite_direction(self.fatal_error_overlapping_direction)):
            print_spam(f'Box intersects on directions "{self.fatal_error_overlapping_direction}".')
            return True
        return False

    def non_fatal_error(self, candidate, others, img):
        if text_intersects(candidate, others):
            return True
        if text_overflows(candidate, img, direction=self.fatal_error_overlapping_direction):
            return "Overflows Image"

        return False
    
    def action_process(self, time_left: int, candidate, others, img, original, iterations_done: int, **kwargs):
        non_fatal_payload = kwargs.pop('non_fatal_payload', None)

        if non_fatal_payload == "Overflows Image":
            # Only slight adjustments here.
            true_offset_pct = [(x * 0.15) for x in self.offset_pct]
        else:
            true_offset_pct = self.offset_pct

        new_candidate = TextBox.shift_from(candidate, offset_pct=true_offset_pct)

        return new_candidate, others
    