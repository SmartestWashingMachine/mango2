def calculate_vertical_overlap_ratio(box_ymin, box_ymax, row_ymin, row_ymax):
    """
    Calculates the vertical overlap ratio of a box with a given row's vertical span.
    This is effectively the proportion of the box's height that overlaps with the row.

    Args:
        box_ymin (float): The y_min of the box.
        box_ymax (float): The y_max of the box.
        row_ymin (float): The minimum y-coordinate of the current row's vertical span.
        row_ymax (float): The maximum y-coordinate of the current row's vertical span.

    Returns:
        float: The vertical overlap ratio (0.0 to 1.0).
               Returns 0 if box height is 0 or if there's no overlap.
    """
    box_height = box_ymax - box_ymin

    if box_height <= 0:
        return 0.0

    # Calculate intersection
    intersection_ymin = max(box_ymin, row_ymin)
    intersection_ymax = min(box_ymax, row_ymax)
    
    intersection_height = intersection_ymax - intersection_ymin

    if intersection_height <= 0:
        return 0.0

    # The ratio of the intersection height to the box's own height
    return intersection_height / box_height


def get_bottom_rows(boxes, N, overlap_threshold=0.5):
    """
    Groups bounding boxes into rows based on a simple vertical overlap threshold.
    Boxes within each row are sorted by their x_min.

    Args:
        boxes (list): A list of bounding boxes, where each box is a tuple
                      (x_min, y_min, x_max, y_max).
        overlap_threshold (float): The minimum vertical overlap ratio (0.0-1.0)
                                   required for a box to be considered part of an
                                   existing row. A value like 0.6 means 60% of the
                                   box's height must overlap with the row's vertical span.

    Returns:
        list: A list of lists, where each inner list represents a row and
              contains the bounding boxes belonging to that row, sorted
              by their x_min.
    """
    if not boxes:
        return []

    # Sort boxes primarily by their y_min to process them roughly from top to bottom
    boxes.sort(key=lambda b: (b[1], b[0]))

    rows = []

    # To track the vertical extent of the *current* row
    current_row_ymin = -1
    current_row_ymax = -1

    for box in boxes:
        x_min, y_min, x_max, y_max = box

        can_add_to_current_row = False

        if rows:
            # Check if the box has sufficient vertical overlap with the current row's span
            overlap_ratio = calculate_vertical_overlap_ratio(y_min, y_max, current_row_ymin, current_row_ymax)
            
            if overlap_ratio >= overlap_threshold:
                can_add_to_current_row = True

        if can_add_to_current_row:
            rows[-1].append(box)
            # Update the row's overall y_min and y_max to include the new box
            current_row_ymin = min(current_row_ymin, y_min)
            current_row_ymax = max(current_row_ymax, y_max)
        else:
            # Start a new row
            rows.append([box])
            current_row_ymin = y_min
            current_row_ymax = y_max

    # Sort rows by the average y_min (bottom rows last)
    rows.sort(key=lambda row: sum(b[1] for b in row) / len(row))
    # Get the bottom N rows
    rows = rows[-N:]

    # Sort boxes within each row by x_min (leftmost first)
    for row in rows:
        row.sort(key=lambda b: b[0])

    return rows
