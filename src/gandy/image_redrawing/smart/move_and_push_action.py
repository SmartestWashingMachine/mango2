from gandy.image_redrawing.smart.base_action import BaseAction, hash_text
from gandy.image_redrawing.smart.utils.text_overflows_image import text_overflows_image
from gandy.image_redrawing.smart.utils.text_overlaps import text_overlaps
from gandy.image_redrawing.smart.utils.box_is_lr import box_b_is_left_or_right
from gandy.image_redrawing.smart.utils.move_box import move_box


class MoveAndPushAction(BaseAction):
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
        FAIL_STATE = (
            text_overflows_image(
                min_font_size,
                text,
                candidate,
                img,
                draw,
                text_align_direction,
                direction=overflow_fail_direction,
            )
            or len(other_offending_boxes) > 0
        )

        if len(other_offending_boxes) > 0:
            for other_idx in other_offending_boxes:
                other = other_boxes[other_idx]
                other_text = other[-1]
                # Other boxes exluding this other and the current box.
                excluding_other = (
                    other_boxes[:other_idx] + other_boxes[(other_idx + 1) :]
                )

                # We use the ORIGINAL box rather than the candidate as box_a here.
                other_is_to_the = box_b_is_left_or_right(box_a=box, box_b=other)

                # push_factor = shift_factor * 2

                print(
                    f'{self.action_name}: Box "{hash_text(text)}" is overlapping another box "{hash_text(other_text)}". The other box is to the {other_is_to_the}.'
                )

                # NOTE: This will have to be adjusted if we push up and down in the future.
                shift_amount = (
                    abs(candidate[0] - box[0]) + abs(candidate[2] - box[2])
                ) * 2.5  # Must be > than 1.

                if other_is_to_the == "left":
                    # Push other box to the left.
                    result, other_can_move = move_box(
                        other,
                        excluding_other,
                        other_text,
                        img,
                        min_font_size,
                        draw=draw,
                        text_align_direction="center",
                        shift_amount=-1 * shift_amount,
                    )
                elif other_is_to_the == "right":
                    # Push other box to the right.
                    result, other_can_move = move_box(
                        other,
                        excluding_other,
                        other_text,
                        img,
                        min_font_size,
                        draw=draw,
                        text_align_direction="center",
                        shift_amount=shift_amount,
                    )
                else:
                    other_can_move = False

                if other_can_move:
                    print(
                        f'{self.action_name} Box "{hash_text(text)}" MOVED "{hash_text(other_text)}"'
                    )
                else:
                    print(
                        f'{self.action_name} Box "{hash_text(text)}" FAILED TO MOVE "{hash_text(other_text)}"'
                    )

                if other_can_move:
                    other_boxes[other_idx] = result

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
        )
