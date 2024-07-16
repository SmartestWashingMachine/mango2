from gandy.image_redrawing.smart.base_action import BaseAction, hash_text
from gandy.image_redrawing.smart.constants import EXPAND_FACTOR
from gandy.image_redrawing.smart.utils.expand_box import expand_box
from gandy.image_redrawing.smart.utils.text_overlaps import text_overlaps
from gandy.image_redrawing.smart.utils.text_overflows_image import text_overflows_image
from gandy.image_redrawing.smart.utils.box_aspect_good import box_aspect_good


class ExpandAspectAction(BaseAction):
    def attempt(
        self,
        box,
        other_boxes,
        text,
        img,
        min_font_size,
        draw,
        text_align_direction="center",
    ):
        print(
            f'{self.action_name} CALLED for Box "{hash_text(text)}" with TimeLeft={self.iterations_left}'
        )

        candidate = expand_box(box, left=EXPAND_FACTOR, right=EXPAND_FACTOR, image=img)

        other_offending_boxes = text_overlaps(
            min_font_size,
            text,
            candidate,
            other_boxes,
            text_align_direction,
            draw=draw,
            image=img,
            with_margin=True,
            return_indices=True,
        )

        reject_action = (
            text_overflows_image(
                min_font_size,
                text,
                candidate,
                img,
                draw,
                text_align_direction,
                direction="lrud",
            )
            or len(other_offending_boxes) > 0
        )

        self.iterations_left -= 1
        if self.iterations_left <= 0 or reject_action:
            print(
                f'{self.action_name} REJECTED for Box "{hash_text(text)}" with TimeLeft={self.iterations_left}'
            )
            return box, False, other_boxes

        FAIL_STATE = not box_aspect_good(candidate)

        if FAIL_STATE:
            print(
                f'{self.action_name}: Box "{hash_text(text)}" RETRYING: Overlaps boxes {[other_boxes[b][-1] for b in other_offending_boxes]} AND AspectGood={FAIL_STATE}'
            )
            return self.attempt(
                candidate,
                other_boxes,
                text,
                img,
                min_font_size,
                draw,
                text_align_direction,
            )
        else:
            print(
                f'{self.action_name} DONE for Box "{hash_text(text)}" with TimeLeft={self.iterations_left}'
            )
            return candidate, True, other_boxes
