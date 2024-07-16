from math import floor


def get_box_height(box):
    return max(floor(box[3] - box[1]), 0)


def get_box_width(box):
    return max(floor(box[2] - box[0]), 0)
