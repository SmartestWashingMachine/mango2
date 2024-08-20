# Similar to IoU
def box_b_in_box_a_thr(box_a, box_b):
    x_a = max(box_a[0], box_b[0])
    y_a = max(box_a[1], box_b[1])
    x_b = min(box_a[2], box_b[2])
    y_b = min(box_a[3], box_b[3])

    inter = abs(max((x_b - x_a, 0)) * max((y_b - y_a), 0))

    if inter == 0:
        return 0

    box_b_area = abs((box_b[2] - box_b[0]) * (box_b[3] - box_b[1]))

    iou = inter / float(box_b_area)

    return iou

def filter_out_overlapping_bboxes(bboxes):
    # Filter out boxes that overlap too much.

    new_bboxes = []
    for idx in range(len(bboxes)):
        others = bboxes[:idx] + bboxes[(idx + 1):]

        if not any(box_b_in_box_a_thr(box_b=bboxes[idx], box_a=o) >= 0.8 for o in others):
            new_bboxes.append(bboxes[idx])
    return new_bboxes