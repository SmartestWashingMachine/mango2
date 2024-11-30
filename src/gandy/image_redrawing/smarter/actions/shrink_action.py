from gandy.image_redrawing.smarter.checks import text_intersects, text_intersects_on_direction, text_overflows
from gandy.image_redrawing.smarter.actions.action import Action
from gandy.image_redrawing.smarter.text_box import TextBox
from typing import List

class ShrinkAction(Action):
    def __init__(self, shrink_factor: float, min_font_val: int, stackable=False, max_iterations = 30, only_on_failure = True) -> None:
        super().__init__(stackable, action_name="Shrink", max_iterations=max_iterations, only_on_failure=only_on_failure)

        self.shrink_factor = shrink_factor
        self.min_font_val = min_font_val

    def fatal_error(self, candidate, others, img, *args, **kwargs):
        # Very little fatal errors. This is a "final measure" approach.
        if candidate.font_size < self.min_font_val:
            return True

        return False

    def non_fatal_error(self, candidate, others, img):
        if text_overflows(candidate, img, "lrud"):
            return True
        return False
    
    def action_process(self, time_left: int, candidate, others, img, original, iterations_done: int, **kwargs):
        new_candidate = TextBox.clone(candidate)

        new_fz = max(1, int(new_candidate.font_size * self.shrink_factor))
        new_candidate.set_font_size(new_fz)


        # Shrink other boxes that touch this one.
        # Can't mutate in-place; affects originals.
        others_cloned = [TextBox.clone(b) for b in others]
        for idx in range(len(others_cloned)):
            if text_intersects(new_candidate, [others_cloned[idx]]):
                others_cloned[idx].set_font_size(new_fz)

        return new_candidate, others_cloned
