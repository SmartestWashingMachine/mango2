from gandy.image_redrawing.smart.magic_box import MagicBox
from gandy.image_redrawing.smart.base_action import hash_text
from gandy.image_redrawing.smart.utils.text_overlaps import text_overlaps
from gandy.image_redrawing.smart.utils.text_overflows_image import text_overflows_image


def move_box(
    box,
    other_boxes,
    text,
    img,
    min_font_size,
    draw,
    text_align_direction,
    shift_factor=None,
    shift_amount=None,
    axis="x",
):
    """
    Moves the box to the right by shift factor. Set it to a negative to make it to the left instead.
    Use axis 'y' to move the box downward by shift factor. Set it to a negative to move it up instead.

    Returns the initial box with a failure flag if overlapping or overflowing.
    """
    if (
        shift_factor is not None
        and shift_amount is not None
        or shift_factor == shift_amount
    ):
        raise RuntimeError("shift_factor OR shift_amount must be set.")
    if axis != "x" and axis != "y":
        raise RuntimeError("Bad axis value")

    img_width, img_height = img.width, img.height

    if shift_factor is not None:
        move = img_width * shift_factor
    else:
        move = shift_amount

    if axis == "x":
        candidate = MagicBox(
            box[0] + move,
            box[1],
            box[2] + move,
            box[3],
            box[4],
            box.can_change_font_size,
        )
    else:
        candidate = MagicBox(
            box[0],
            box[1] + move,
            box[2],
            box[3] + move,
            box[4],
            box.can_change_font_size,
        )

    # A bit hacky, but we disable margin checking for moved boxes. It doesn't seem to work too well with our algo.
    other_offending_boxes = text_overlaps(
        min_font_size,
        text,
        candidate,
        other_boxes,
        text_align_direction,
        draw=draw,
        image=img,
        with_margin=False,
        return_indices=True,
    )
    if len(other_offending_boxes) > 0:
        bad_texts = [other_boxes[b][-1] for b in other_offending_boxes]
        print(
            f'--- Moving box "{hash_text(text)}" but failed due to overlapping box "{bad_texts}".'
        )

        return box, False
    if text_overflows_image(
        min_font_size,
        text,
        candidate,
        img,
        draw,
        text_direction="center",
        direction="lrud",
    ):
        print(f'--- Moving box "{hash_text(text)}" but failed due to overflowing.')
        return box, False

    return candidate, True
