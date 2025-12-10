from typing import List
from gandy.utils.speech_bubble import SpeechBubble
from gandy.utils.crude_dag import CrudeDAG
from gandy.utils.merge_speeches import distance_segment_to_segment

# A lot of theory from: https://arxiv.org/pdf/2401.10224

def a_strictly_above_b(a: SpeechBubble, b: SpeechBubble):
    return a[3] <= b[1]

def a_strictly_right_of_b(a: SpeechBubble, b: SpeechBubble):
    return a[0] >= b[2]

def a_b_overlap(a: SpeechBubble, b: SpeechBubble):
    # Check if box a and box b overlap.

    if a[0] >= b[2] or b[0] >= a[2]:
        return False # No horizontal overlap.

    if a[1] >= b[3] or b[1] >= a[3]:
        return False # No vertical overlap.

    return True

def erode_box(a: SpeechBubble, factor = 0.03):
    width = a[2] - a[0]
    height = a[3] - a[1]

    return [
        a[0] + width * factor,
        a[1] + height * factor,
        a[2] - width * factor,
        a[3] - height * factor,
    ]

def a_b_split_vertical_cuts(a: SpeechBubble, b: SpeechBubble, boxes: List[SpeechBubble], min_bound = -999999, max_bound = 999999, cut_size = 2):
    candidate_cuts = []
    for x in boxes:
        candidate_cuts.append(
            [x[2] + cut_size, 0, x[2] + cut_size * 2, 999999]
        ) # Make a cut from the right of the box.

        candidate_cuts.append(
            [x[0] - cut_size * 2, 0, x[0] - cut_size, 999999]
        ) # Make a cut from the left of the box.

    for cut in candidate_cuts:
        if cut[0] <= min_bound or cut[2] >= max_bound:
            continue

        if any(a_b_overlap(cut, x) for x in boxes):
            # The cut could not separate all the boxes.
            continue

        # Valid cut - check if it separates a and b.
        if (a_strictly_right_of_b(a, cut) and not a_strictly_right_of_b(b, cut)): # A right of cut. B left of cut.
            return True
        if (a_strictly_right_of_b(b, cut) and not a_strictly_right_of_b(a, cut)): # B right of cut. A left of cut.
            return True

    return False

def a_b_split_horizontal_cuts(a: SpeechBubble, b: SpeechBubble, boxes: List[SpeechBubble], min_bound = -999999, max_bound = 999999, cut_size = 2):
    """
    Determine if there exists a cut that separates box a and box b (top and bottom).
    """
    candidate_cuts = []
    for x in boxes:
        candidate_cuts.append(
            [0, x[1] - cut_size * 2, 999999, x[1] - cut_size]
        ) # Make a cut from the top of the box.

        candidate_cuts.append(
            [0, x[3] + cut_size, 999999, x[3] + cut_size * 2]
        ) # Make a cut from the bottom of the box.

    for cut in candidate_cuts:
        if cut[1] <= min_bound or cut[3] >= max_bound:
            continue

        if any(a_b_overlap(cut, x) for x in boxes):
            # The cut could not separate all the boxes.
            continue

        # Valid cut - check if it separates a and b.
        if (a_strictly_above_b(a, cut) and not a_strictly_above_b(b, cut)): # A above cut. B below cut.
            return True
        if (a_strictly_above_b(b, cut) and not a_strictly_above_b(a, cut)): # B above cut. A below cut.
            return True

    return False

def a_center_x(a: SpeechBubble):
    return (a[0] + a[2]) // 2

def a_center_y(a: SpeechBubble):
    return (a[1] + a[3]) // 2

def sort_frames(boxes: List[SpeechBubble], left_to_right = False):
    G = CrudeDAG() # Directed graph
    for i in range(len(boxes)):
        G.add_node(i)

    for i in range(len(boxes)):
        for j in range(len(boxes)):
            if i == j:
                continue

            # "AI is going to take over programming!" Yeah right try feeding it a fudging graph problem.

            eroded_box_i = [*boxes[i]]
            eroded_box_j = [*boxes[j]]

            while a_b_overlap(eroded_box_i, eroded_box_j):
                eroded_box_i = erode_box(eroded_box_i)
                eroded_box_j = erode_box(eroded_box_j)

            # Ideal "simple" cases: frame[i] and frame[j] do NOT overlap in any direction.
            if (
                (a_strictly_above_b(eroded_box_i, eroded_box_j) and not a_strictly_right_of_b(eroded_box_j, eroded_box_i) and not left_to_right) or
                (a_strictly_above_b(eroded_box_i, eroded_box_j) and not a_strictly_right_of_b(eroded_box_i, eroded_box_j) and left_to_right)
            ):
                # 1. If frame[i] is strictly above frame[j], and frame[j] is not strictly to the right of frame[i].
                # 1b (LTR). If frame[i] is strictly above frame[j], and frame[i] is not strictly to the right of frame[j].
                G.add_edge(i, j)

                # print(f"Added edge {i} -> {j} (case 1)")
            elif (
                (a_strictly_right_of_b(eroded_box_i, eroded_box_j) and not a_strictly_above_b(eroded_box_j, eroded_box_i) and not left_to_right) or
                (a_strictly_right_of_b(eroded_box_j, eroded_box_i) and not a_strictly_above_b(eroded_box_j, eroded_box_i) and left_to_right)
            ):
                # 3. If frame[i] is strictly to the right of frame[j], and frame[j] is not strictly above frame[i].
                # 1b (LTR). If frame[j] is strictly to the right of frame[i], and frame[j] is not strictly above frame[i].
                G.add_edge(i, j)

                # print(f"Added edge {i} -> {j} (case 3)")
            else:
                # (5/6). Complex cases. We need to "cut".

                if (
                    (a_strictly_above_b(eroded_box_i, eroded_box_j) and a_strictly_right_of_b(eroded_box_j, eroded_box_i) and not left_to_right) or
                    (a_strictly_above_b(eroded_box_i, eroded_box_j) and a_strictly_right_of_b(eroded_box_i, eroded_box_j) and left_to_right)
                ):
                    # B.1.1. If frame[i] is strictly above frame[j] AND frame[j] is strictly to the right of frame[i].
                    # B.1.1b (LTR). If frame[i] is strictly above frame[j] AND frame[i] is strictly to the right of frame[j].

                    eroded_boxes = [*boxes]

                    for _ in range(100):
                        if a_b_split_horizontal_cuts(eroded_box_i, eroded_box_j, eroded_boxes):
                            # B.1.3. (1). If there exists a horizontal cut that separates frame[i] and frame[j].
                            G.add_edge(i, j)

                            # print(f"Added edge {i} -> {j} (case 5)")
                            break
                        elif a_b_split_vertical_cuts(eroded_box_i, eroded_box_j, eroded_boxes):
                            # B.1.3. (2). If there exists a vertical cut that separates frame[i] and frame[j].

                            # Yes, this is correct (according to the paper).
                            G.add_edge(j, i)

                            # print(f"Added edge {i} -> {j} (case 6)")
                            break
                        else:
                            # B.1.3. (3). Some overlap, so we erode.
                            eroded_boxes = [erode_box(box) for box in eroded_boxes]
                            continue

    sorted_nodes = G.topological_sort()
    sorted_boxes = [boxes[i] for i in sorted_nodes]

    return sorted_boxes

def merge_nearby_text_boxes(text_boxes: List[SpeechBubble], image_width: int, image_height: int, distance_threshold = 0.02):
    # distance_threshold of 0.02 means 2% of the image side.
    # We merge nearby text boxes that are close to each other.

    merged: List[SpeechBubble] = []

    _width_thr = distance_threshold * image_width
    _height_thr = distance_threshold * image_height
    width_thr = height_thr = _width_thr + _height_thr

    for box in text_boxes:
        did_merge = False
        for i in range(len(merged)): # TODO: We might be able to get away with using a stack instead, considering the reading order...
            mbox = merged[i]

            if distance_segment_to_segment(
                [box[0], box[1]],
                [box[0], box[3]],
                [mbox[2], mbox[1]],
                [mbox[2], mbox[3]],
            ) <= width_thr:
                # Case 1. Left edge of I is near right edge of J.
                do_add = True
            elif distance_segment_to_segment(
                [box[2], box[1]],
                [box[2], box[3]],
                [mbox[0], mbox[1]],
                [mbox[0], mbox[3]],
            ) <= width_thr:
                # Case 2. Right edge of I is near left edge of J.
                do_add = True
            elif distance_segment_to_segment(
                [box[0], box[3]],
                [box[2], box[3]],
                [mbox[0], mbox[1]],
                [mbox[2], mbox[1]],
            ) <= height_thr:
                # NOTE: Currently disabling case 3/4 - does not seem wise.
                # Case 3. Bottom edge of I is near top edge of J.
                do_add = False
            elif distance_segment_to_segment(
                [box[0], box[1]],
                [box[2], box[1]],
                [mbox[0], mbox[3]],
                [mbox[2], mbox[3]],
            ) <= height_thr:
                # Case 4. Top edge of I is near bottom edge of J.
                do_add = False
            else:
                do_add = False

            if do_add:
                merged[i] = [
                    min(box[0], mbox[0]),
                    min(box[1], mbox[1]),
                    max(box[2], mbox[2]),
                    max(box[3], mbox[3]),
                ]
                did_merge = True
                break

        if not did_merge:
            merged.append(box)

    return merged

def add_frames_for_ghost_text_boxes(frame_boxes: List[SpeechBubble], text_boxes: List[SpeechBubble]):
    # Text boxes without any frame (no overlap) have a "ghost frame" with their size and position.

    new_frame_boxes: List[SpeechBubble] = [*frame_boxes]
    for tb in text_boxes:
        if all(not a_b_overlap(tb, fb) for fb in new_frame_boxes):
            new_frame_boxes.append(tb)

    return new_frame_boxes

def sort_text_in_sorted_frames(frame_boxes: List[SpeechBubble], text_boxes: List[SpeechBubble], left_to_right = False, merge_nearby_text_boxes_in_frame = False):
    # For each text box, find which (already sorted) frame it belongs to.
    # We assume that the text box belongs to the frame which it overlaps the most.

    frame_text_map = {i: [] for i in range(len(frame_boxes))}
    for text_box in text_boxes:
        max_overlap_area = 0
        best_frame_index = -1

        for i, frame_box in enumerate(frame_boxes):
            # Calculate overlap area.
            x_left = max(text_box[0], frame_box[0])
            y_top = max(text_box[1], frame_box[1])
            x_right = min(text_box[2], frame_box[2])
            y_bottom = min(text_box[3], frame_box[3])

            if x_right < x_left or y_bottom < y_top:
                overlap_area = 0
            else:
                overlap_area = (x_right - x_left) * (y_bottom - y_top)

            if overlap_area > max_overlap_area:
                max_overlap_area = overlap_area
                best_frame_index = i

        if best_frame_index == -1:
            # Find the closest frame by distance, and just add it there.
            distances = [((a_center_x(fb) - a_center_x(text_box)) ** 2 + (a_center_y(fb) - a_center_y(text_box)) ** 2) ** 0.5 for fb in frame_boxes]
            best_frame_index = distances.index(min(distances))

        frame_text_map[best_frame_index].append(text_box)

    # Then for each frame, sort its text boxes, and concatenate to the final list.
    # We usually assume that text boxes that are closer to the top right come first.
    sorted_text_boxes = []

    # Sort texts in this frame.
    def _text_box_distance(tb):
        if left_to_right:
            # Distance from top-left of frame box [x1, y1]
            x = (tb[0] - frame_box[0]) ** 2
            y = (tb[1] - frame_box[1]) ** 2
        else:
            # Distance from top-right of frame box [x2, y1]
            x = (frame_box[2] - tb[2]) ** 2
            y = (tb[1] - frame_box[1]) ** 2

        return (x + y) ** 0.5

    for i in range(len(frame_boxes)):
        frame_box = frame_boxes[i]

        texts_in_frame = frame_text_map[i]
        if len(texts_in_frame) == 0:
            continue
        texts_in_frame.sort(key=_text_box_distance)

        if merge_nearby_text_boxes_in_frame:
            texts_in_frame = merge_nearby_text_boxes(
                texts_in_frame, 
                image_width=frame_box[2] - frame_box[0], 
                image_height=frame_box[3] - frame_box[1],
                distance_threshold=0.03,
            )

        sorted_text_boxes.extend(texts_in_frame)

    return sorted_text_boxes