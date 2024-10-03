from gandy.image_redrawing.smarter.checks import text_intersects, text_intersects_on_direction, text_overflows
from gandy.image_redrawing.smarter.actions.action import Action
from gandy.image_redrawing.smarter.text_box import TextBox
from typing import List

class MergeTextAction(Action):
    def __init__(self, shrink_factor: float, min_font_val: int, stackable=False, max_iterations = 30) -> None:
        super().__init__(stackable, action_name="MergeText", max_iterations=max_iterations)

        self.shrink_factor = shrink_factor
        self.min_font_val = min_font_val

    def fatal_error(self, candidate: TextBox, others, img, *args, **kwargs):
        return False

    def non_fatal_error(self, candidate, others, img):
        if candidate.text != "":
            return True

        return False
    
    def action_process(self, time_left: int, candidate: TextBox, others: List[TextBox], img, original, iterations_done: int):
        new_candidate = TextBox.clone(candidate)

        # Shrink other boxes that touch this one.
        # Can't mutate in-place; affects originals.
        others_cloned = [TextBox.clone(b) for b in others]
        for idx in range(len(others_cloned)):
            if text_intersects(new_candidate, [others_cloned[idx]]):
                other_new = TextBox.clone(others_cloned[idx])

                new_fz = max(self.min_font_val, int(other_new.font_size * (self.shrink_factor ** iterations_done)))
                other_new.set_font_size(new_fz, do_recompute=False)

                other_new.set_text((other_new.text + f" {new_candidate.text}").strip(), do_recompute=True) # Concat the text.


                other_others = others_cloned[:idx] + others_cloned[(idx + 1):]

                # This is the actual "fatal" / "non-fatal" error check here.
                if new_fz >= self.min_font_val and not text_intersects(other_new, other_others) and not text_overflows(other_new, img):
                    print('SUCCESS???')
                    others_cloned[idx] = other_new # Hooray!
                    new_candidate.set_text("") # Erase the text here.

                    break # Success!

        return new_candidate, others_cloned
