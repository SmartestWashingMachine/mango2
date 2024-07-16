from gandy.image_redrawing.smart.base_action import BaseAction, hash_text
from gandy.image_redrawing.smart.utils.text_overlaps_on_direction import (
    text_overlaps_on_direction,
)
from gandy.image_redrawing.smart.utils.text_overlaps import text_overlaps
from gandy.image_redrawing.smart.utils.text_overflows_image import text_overflows_image


class MoveAction(BaseAction):
    def attempt(
        self,
        box,
        make_candidate,
        reject_action,
        other_boxes,
        text,
        img,
        min_font_size,
        draw,
        text_align_direction="center",
        overflow_fail_direction="l",
    ):
        print(
            f'{self.action_name} CALLED for Box "{hash_text(text)}" with TimeLeft={self.iterations_left}'
        )

        candidate = make_candidate(box)

        self.iterations_left -= 1
        if self.iterations_left <= 0 or reject_action(
            box=candidate,
            other_boxes=other_boxes,
            text=text,
            img=img,
            min_font_size=min_font_size,
            draw=draw,
            text_align_direction=text_align_direction,
        ):
            print(
                f'{self.action_name} REJECTED for Box "{hash_text(text)}" with TimeLeft={self.iterations_left}'
            )
            return box, False, other_boxes

        other_offending_boxes = text_overlaps(
            min_font_size,
            text,
            candidate,
            other_boxes,
            text_align_direction,
            draw=draw,
            return_indices=True,
            image=img,
            with_margin=True,
        )
        FAIL_STATE = len(other_offending_boxes) > 0 or text_overflows_image(
            min_font_size,
            text,
            candidate,
            img,
            draw,
            text_align_direction,
            direction=overflow_fail_direction,
        )

        if FAIL_STATE:
            print(
                f'{self.action_name}: Box "{hash_text(text)}" RETRYING: Overlaps boxes {[other_boxes[b][-1] for b in other_offending_boxes]}'
            )

            return self.attempt(
                candidate,
                make_candidate,
                reject_action,
                other_boxes,
                text,
                img,
                min_font_size,
                draw,
                text_align_direction,
                overflow_fail_direction,
            )
        else:
            last_check = not text_overflows_image(
                min_font_size,
                text,
                candidate,
                img,
                draw,
                text_align_direction,
                direction="lrud",
            )

            print(
                f'{self.action_name}: Box "{hash_text(text)}" DONE with SanityCheck={last_check} AND TimeLeft={self.iterations_left}'
            )

            return candidate, last_check, other_boxes

    @staticmethod
    def reject(overflow_direction):
        return lambda box, *args, **kwargs: text_overflows_image(
            kwargs["min_font_size"],
            kwargs["text"],
            box,
            kwargs["img"],
            kwargs["draw"],
            "center",
            direction=overflow_direction,
        ) or text_overlaps_on_direction(
            kwargs["min_font_size"],
            kwargs["text"],
            box,
            kwargs["other_boxes"],
            "center",
            direction_to_check=overflow_direction,
            draw=kwargs["draw"],
            image=kwargs["img"],
            with_margin=True,
        )
