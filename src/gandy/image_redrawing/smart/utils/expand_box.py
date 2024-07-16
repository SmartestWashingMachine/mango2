from gandy.image_redrawing.smart.magic_box import MagicBox
from gandy.image_redrawing.smart.constants import EXPAND_RELATIVE


def _inc_factor(val: float, pct: float, image_length=None):
    if image_length is None:
        return val + (val * pct)
    else:
        return val + (image_length * pct)


def expand_box(box: MagicBox, down=None, up=None, left=None, right=None, image=None):
    """
    Expands the detected region box in a specific direction. This has the effect of moving the text in that direction too (since the text is centered in the region box).
    """
    new_box = MagicBox(box[0], box[1], box[2], box[3], box[4], box.can_change_font_size)

    size_factor = 1.0

    if EXPAND_RELATIVE:
        image_width, image_height = None, None
    else:
        image_width, image_height = image.width, image.height

    if down is not None:
        new_box[3] = _inc_factor(new_box[3], down * size_factor, image_height)
    if up is not None:
        new_box[1] = _inc_factor(new_box[1], up * size_factor * -1, image_height)
    if left is not None:
        new_box[0] = _inc_factor(new_box[0], left * size_factor * -1, image_width)
    if right is not None:
        new_box[2] = _inc_factor(new_box[2], right * size_factor, image_width)

    return new_box
