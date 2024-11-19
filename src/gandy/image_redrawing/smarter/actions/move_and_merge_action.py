from gandy.image_redrawing.smarter.checks import text_intersects, text_intersects_on_direction, text_overflows
from gandy.image_redrawing.smarter.actions.action import Action
from gandy.image_redrawing.smarter.text_box import TextBox
from gandy.image_redrawing.smarter.image_fonts import print_spam
from typing import List

class MoveAndMergeTextAction(Action):
    def __init__(self, shrink_factor: float, min_font_val: int, stackable=False, max_iterations = 30, offset_pct = None, expand_box = False, fatal_overflowing_direction = None) -> None:
        super().__init__(stackable, action_name="MoveMergeText", max_iterations=max_iterations)

        self.shrink_factor = shrink_factor
        self.min_font_val = min_font_val
        self.offset_pct = offset_pct
        self.expand_box = expand_box

        self.fatal_overflowing_direction = fatal_overflowing_direction

    def get_non_fatal_error_overlapping_direction(self):
        dirs = "lrud"
        for c in self.fatal_overflowing_direction:
            dirs = dirs.replace(c, "")

        return dirs

    def fatal_error(self, candidate, others, img, prev_candidate, *args, **kwargs):
        if candidate.text == "":
            return False

            #raise RuntimeError('e')
        if text_overflows(candidate, img, direction=self.fatal_overflowing_direction):
            print_spam('Box overflows image.')
            return True
        return False

    def non_fatal_error(self, candidate, others, img):
        if candidate.text == "":
            return False

        if text_intersects(candidate, others):
            return True
        if text_overflows(candidate, img, direction=self.get_non_fatal_error_overlapping_direction()):
            return True

        return False
    
    def action_process(self, time_left: int, candidate: TextBox, others: List[TextBox], img, original, iterations_done: int):
        if iterations_done > 1:
            new_candidate = TextBox.shift_from(candidate, offset_pct=self.offset_pct)
        else:
            new_candidate = TextBox.clone(candidate)

        # Shrink other boxes that touch this one.
        # Can't mutate in-place; affects originals.
        others_cloned = [TextBox.clone(b) for b in others]
        for idx in range(len(others_cloned)):
            if text_intersects(new_candidate, [others_cloned[idx]]):
                other_new = TextBox.clone(others_cloned[idx])

                new_fz = max(self.min_font_val, int(other_new.font_size * (self.shrink_factor ** iterations_done)))
                other_new.set_font_size(new_fz, do_recompute=False)

                if self.expand_box:
                    other_new.x1 = min(other_new.x1, new_candidate.x1)
                    other_new.x2 = max(other_new.x2, new_candidate.x2)
                    other_new.y1 = min(other_new.y1, new_candidate.y1)
                    other_new.y2 = max(other_new.y2, new_candidate.y2)

                other_new.set_text((other_new.text + f" {new_candidate.text}").strip(), do_recompute=True) # Concat the text.

                other_others = others_cloned[:idx] + others_cloned[(idx + 1):]

                # This is the actual "fatal" / "non-fatal" error check here.
                if new_fz >= self.min_font_val and not text_intersects(other_new, other_others) and not text_overflows(other_new, img):
                    others_cloned[idx] = other_new # Hooray!
                    new_candidate.set_text("") # Erase the text here.

                    break # Success!

        return new_candidate, others_cloned
