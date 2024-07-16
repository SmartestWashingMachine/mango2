def box_b_is_left_or_right(box_a, box_b, img=None):
    """
    Returns "left" if box_b is to the left of box_a. Returns "right" if box_b is to the right of box_a. Returns "none" otherwise.
    """
    # img_width, img_height = img.width, img.height

    def _midp(b):
        return b[0] + ((b[2] - b[0]) / 2)

    x_center_a = _midp(box_a)
    x_center_b = _midp(box_b)

    if x_center_b < x_center_a:
        return "left"
    elif x_center_b > x_center_a:
        return "right"
    else:
        return "none"
