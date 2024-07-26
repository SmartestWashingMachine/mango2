from gandy.image_redrawing.smart.utils.load_font import load_font
from gandy.image_redrawing.smart.utils.compute_max_chars_per_line import (
    compute_max_chars_per_line,
)
from gandy.image_redrawing.smart.utils.wrap_text import wrap_text
from gandy.utils.compute_stroke_size import compute_stroke_size
from gandy.image_redrawing.smart.utils.get_vertical_spacing import get_vertical_spacing
from gandy.image_redrawing.smart.utils.get_box_size import get_box_width, get_box_height
from PIL import ImageDraw


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

    # Meh. candidate_size = font.getsize_multiline(wrapped_text)
    # TODO: Optimize. Just found out this function a bit ago... PIL/Pillow can be a pain to navigate...
    bbox = draw.multiline_textbbox(
        (0, 0),
        wrapped_text,
        font,
        align="center",
        stroke_width=compute_stroke_size(font_size),
        spacing=get_vertical_spacing(font_size),
    )

    candidate_size = get_box_width(bbox), get_box_height(bbox)

    return candidate_size
