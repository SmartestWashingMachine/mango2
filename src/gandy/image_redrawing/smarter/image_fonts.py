from PIL import Image
from gandy.state.config_state import config_state
import textwrap


def wrap_text(text, max_chars_per_line):
    """
    Given a piece of text, breaks it according to the max_chars_per_line for use in PIL.
    """
    w = textwrap.TextWrapper(
        width=max_chars_per_line, break_long_words=False, break_on_hyphens=False
    )
    wrapped_text = w.fill(text)

    return wrapped_text

def compute_min_max_font_sizes(img: Image):
    """
    Compute the min and max font size for an image.
    """
    image_length = min(img.width, img.height)

    min_font_size = 16 + round(image_length * 0.012)
    min_font_size = max(min_font_size, 9)

    # max_font_size = round(min_font_size * 1.75)
    max_font_size = round(min_font_size * 2.0)

    return min_font_size, max_font_size

def compute_stroke_size(font_size: int):
    min_stroke_size = 1

    comp = round(font_size * (config_state.stroke_size / 8))

    return max(min_stroke_size, comp)

def get_vertical_spacing(font_size: int):
    return 3 - compute_stroke_size(font_size)

def print_spam(s: str):
    #print(s)
    pass