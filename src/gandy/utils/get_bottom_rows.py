def get_bottom_rows(bounding_boxes, N, image_height, nearby_threshold=0.1):
    """
    Retrieve the N bottom rows of bounding boxes.

    Args:
        bounding_boxes (list of tuples): List of bounding boxes in the form (x_min, y_min, x_max, y_max).
        N (int): Number of bottom rows to retrieve.
        image_height (int): Height of the image.

    Returns:
        list of tuples: List of bounding boxes in the bottom N rows, preserving original order.
    """
    # Sort bounding boxes by y_min
    sorted_boxes = sorted(bounding_boxes, key=lambda box: box[1])

    y_threshold = image_height * nearby_threshold

    N = min(N, len(sorted_boxes))

    # Group boxes into rows based on y_min proximity
    rows = []
    current_row = []
    for box in sorted_boxes:
        if not current_row or abs(box[1] - current_row[-1][1]) <= y_threshold:
            current_row.append(box)
        else:
            rows.append(current_row)
            current_row = [box]
    if current_row:
        rows.append(current_row)

    # Retrieve the bottom N rows
    bottom_rows = rows[-N:]

    # Sort each row by the original order in the input list
    for i in range(len(bottom_rows)):
        bottom_rows[i] = sorted(bottom_rows[i], key=lambda box: bounding_boxes.index(box))

    return bottom_rows
