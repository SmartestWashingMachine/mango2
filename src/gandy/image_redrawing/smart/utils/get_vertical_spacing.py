from gandy.utils.compute_stroke_size import compute_stroke_size


def get_vertical_spacing(font_size: int):
    return 3 - compute_stroke_size(font_size)
