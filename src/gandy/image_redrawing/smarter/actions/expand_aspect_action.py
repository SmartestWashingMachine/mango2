from gandy.image_redrawing.smarter.checks import text_intersects, text_intersects_on_direction, text_overflows
from gandy.image_redrawing.smarter.actions.action import Action
from gandy.image_redrawing.smarter.text_box import TextBox
from typing import List

def get_aspect_ratio(candidate: TextBox):
    return candidate.get_width() / max(candidate.get_height(), 1)

class ExpandAspectAction(Action):
    def __init__(self, w_increase_pct = 0.01, img_coverage_thresh = 0.1, ideal_asp = 1.0, stackable=False) -> None:
        super().__init__(stackable, action_name="ExpandAspect")

        self.w_increase_pct = w_increase_pct
        self.img_coverage_thresh = img_coverage_thresh
        self.ideal_asp = ideal_asp

    def fatal_error(self, candidate, others, img, prev_candidate):
        if text_overflows(candidate, img, "lr"):
            return True
        if ((candidate.get_area()) / max((img.tile_width * img.tile_height), 1)) >= self.img_coverage_thresh:
            return True
        if get_aspect_ratio(candidate) >= self.ideal_asp and get_aspect_ratio(prev_candidate) >= self.ideal_asp:
            return True
        if text_intersects_on_direction(candidate, others, img, direction_to_check="lr"):
            return True
        if get_aspect_ratio(prev_candidate) >= get_aspect_ratio(candidate):
            # If the box has only one word or few words, expanding the aspect ratio may actually just result in the box shifting to the left.
            return True

        return False

    def non_fatal_error(self, candidate, others, img):
        if (get_aspect_ratio(candidate)) < self.ideal_asp:
            return True
        return False
    
    def action_process(self, time_left: int, candidate, others, img, original, iterations_done: int, **kwargs):
        new_candidate = TextBox.clone(candidate)

        w_offset = self.w_increase_pct * img.tile_width * iterations_done
        new_candidate.x1 = new_candidate.container.x1 - w_offset
        new_candidate.x2 = new_candidate.container.x2 + w_offset
        new_candidate.recompute()

        return new_candidate, others