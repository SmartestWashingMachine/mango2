from math import floor
from PIL import ImageDraw
from gandy.image_redrawing.smart.utils.load_font import load_font
from gandy.image_redrawing.smart.utils.compute_max_chars_per_line import (
    compute_max_chars_per_line,
)
from gandy.image_redrawing.smart.utils.wrap_text import wrap_text
from gandy.image_redrawing.smart.utils.get_stroke_width import get_stroke_width
from gandy.image_redrawing.smart.utils.get_vertical_spacing import get_vertical_spacing
from gandy.image_redrawing.smart.utils.get_box_size import get_box_height, get_box_width


def compute_font_region(font_size, box_width, text, draw: ImageDraw.ImageDraw):
    """
    Calculate the bounding box of the text using the default font.
    """
    font = load_font(font_size)

    candidate_max_char_count = compute_max_chars_per_line(font, box_width)

    wrapped_text = wrap_text(
        text,
        candidate_max_char_count,
    )

    # TODO: Optimize. Just found out this function recently... PIL/Pillow can be a pain to navigate...
    bbox = draw.multiline_textbbox(
        (0, 0),
        wrapped_text,
        font,
        align="center",
        stroke_width=get_stroke_width(font_size),
        spacing=get_vertical_spacing(font_size),
    )

    candidate_size = get_box_width(bbox), get_box_height(bbox)

    return candidate_size


def compute_text_box(font_size, text, box, text_align_direction, draw):
    """
    Compute the bounding box of the actual translated text (rather than the detected text region for the source).
    This is almost always when considering box overlaps.
    """
    text_width, text_height = compute_font_region(
        font_size, box_width=get_box_width(box), text=text, draw=draw
    )

    text_box = [box[0], box[1], box[0] + text_width, box[1] + text_height, text]

    container_height = get_box_height(box)
    container_width = get_box_width(box)

    text_box_height = get_box_height(text_box)
    text_box_width = get_box_width(text_box)

    start_top = max((container_height - text_box_height) // 2, 0)
    if text_align_direction == "center":
        offset_left = max((container_width - text_box_width) // 2, 0)
    elif text_align_direction == "left":
        offset_left = 0
    elif text_align_direction == "right":
        offset_left = max((container_width - text_box_width), 0)
    else:
        raise RuntimeError("Bad text alignment direction.")

    text_box[1] = text_box[1] + start_top
    text_box[3] = text_box[3] + start_top
    text_box[0] = text_box[0] + offset_left
    text_box[2] = text_box[2] + offset_left

    return text_box
