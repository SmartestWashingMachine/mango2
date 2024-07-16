from gandy.image_redrawing.smart.utils.compute_font_region import compute_font_region


def text_overflows(
    font_size, box_width, box_height, text, candidate_size=None, draw=None
):
    """
    Returns True if the text with the default font would overflow the speech box.

    This is only used to reduce the font size.
    """
    if font_size is None and candidate_size is None:
        raise ValueError("Either font_size or candidate_size must be given.")

    if candidate_size is None:
        candidate_size = compute_font_region(font_size, box_width, text, draw)

    if candidate_size[0] < box_width and candidate_size[1] < box_height:
        return False

    return True
