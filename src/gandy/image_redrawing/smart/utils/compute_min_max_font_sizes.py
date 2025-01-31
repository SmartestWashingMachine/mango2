from math import floor


def compute_min_max_font_sizes(image_width: int, image_height: int):
    """
    Compute the min and max font size for an image.
    """
    image_length = min(image_width, image_height)

    min_font_size = 16 + round(image_length * 0.012)
    min_font_size = max(min_font_size, 9)

    # max_font_size = round(min_font_size * 1.75)
    max_font_size = round(min_font_size * 1.5)

    return min_font_size, max_font_size
