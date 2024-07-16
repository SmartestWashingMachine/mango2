from gandy.image_redrawing.smart.utils.get_box_size import get_box_height, get_box_width


def box_aspect_good(box):
    """
    Checks if the aspect ratio (h/w) is fairly balanced.
    """
    width = get_box_width(box)
    height = get_box_height(box)

    thresh = 1.25

    return (width / max(height, 1)) >= thresh
