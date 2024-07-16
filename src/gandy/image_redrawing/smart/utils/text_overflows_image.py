from gandy.image_redrawing.smart.magic_box import MagicBox


def text_overflows_image(
    min_font_size,
    text,
    box: MagicBox,
    img,
    draw,
    text_direction,
    direction="u",
    text_box=None,
):
    """
    Checks if the text box overflows the image.
    """
    box = text_box or box.get_text_box(
        min_font_size, text_direction, draw, text=text
    )  # text box

    if box[0] <= 0 and "l" in direction:
        return True
    if box[1] <= 0 and "u" in direction:
        return True
    if box[2] >= img.width and "r" in direction:
        return True
    if box[3] >= img.height and "d" in direction:
        return True
    return False
