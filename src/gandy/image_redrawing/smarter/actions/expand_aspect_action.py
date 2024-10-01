from gandy.image_redrawing.smarter.checks import text_intersects, text_intersects_on_direction, text_overflows
from gandy.image_redrawing.smarter.actions.action import Action
from gandy.image_redrawing.smarter.text_box import TextBox
from typing import List

class ExpandAspectAction(Action):
    def __init__(self, w_increase_pct = 0.03, img_coverage_thresh = 0.1, ideal_asp = 1.25, stackable=False) -> None:
        super().__init__(stackable, action_name="ExpandAspect")

        self.w_increase_pct = w_increase_pct
        self.img_coverage_thresh = img_coverage_thresh
        self.ideal_asp = ideal_asp

    def fatal_error(self, candidate, others, img):
        if text_overflows(candidate, img):
            return True
        if ((candidate.get_area()) / max((img.width * img.height), 1)) >= self.img_coverage_thresh:
            return True
        if (candidate.get_width() / max(candidate.get_height(), 1)) >= self.ideal_asp:
            return True
        if text_intersects(candidate, others):
            return True

        return False

    def non_fatal_error(self, candidate, others, img):
        if (candidate.get_width() / max(candidate.get_height(), 1)) < self.ideal_asp:
            return True
        return False
    
    def action_process(self, time_left: int, candidate, others, img, original, iterations_done: int):
        new_candidate = TextBox.shift_from(candidate, offset_pct=[self.w_increase_pct, 0, self.w_increase_pct, 0])

        return new_candidate, others