from gandy.image_redrawing.physics.text_block import TextBlock
from gandy.utils.speech_bubble import SpeechBubble
from typing import List
from gandy.utils.fancy_logger import logger
from gandy.image_redrawing.physics.misc_utils import bbox_area, bbox_center, bboxes_overlap, bbox_width, bbox_height
from PIL import Image

def center_on_point(box, point):
    """
    Centers the given box [x_min, y_min, x_max, y_max] on the given point [x, y].

    Returns a new box [new_x_min, new_y_min, new_x_max, new_y_max].
    """
    x_min, y_min, x_max, y_max = box
    x, y = point

    width = x_max - x_min
    height = y_max - y_min

    new_x_min = x - width / 2
    new_y_min = y - height / 2
    new_x_max = x + width / 2
    new_y_max = y + height / 2

    return [new_x_min, new_y_min, new_x_max, new_y_max]

def compute_mass(block: TextBlock):
    return len(block.wrapped_lines) * bbox_area(block.final_bbox)

def initialize_displacement():
    return [0, 0] # [x, y]

def compute_displacement_size(displacement: List[float]):
    return (displacement[0] ** 2 + displacement[1] ** 2) ** 0.5

def displace_bbox(bb: SpeechBubble, displacement: List[float]):
    x, y = displacement
    return [
        bb[0] + x,
        bb[1] + y,
        bb[2] + x,
        bb[3] + y,
    ]

def compute_repulsion_force(bl_A: TextBlock, bl_B: TextBlock, margin = 0):
    margin_bl_A_final_bbox = bl_A.final_bbox
    if margin != 0:
        margin_bl_A_final_bbox = [
            margin_bl_A_final_bbox[0] - margin,
            margin_bl_A_final_bbox[1] - margin,
            margin_bl_A_final_bbox[2] + margin,
            margin_bl_A_final_bbox[3] + margin,
        ]

    center_A = bbox_center(margin_bl_A_final_bbox)
    center_B = bbox_center(bl_B.final_bbox)

    half_width_A = bbox_width(margin_bl_A_final_bbox) / 2
    half_width_B = bbox_width(bl_B.final_bbox) / 2

    half_height_A = bbox_height(margin_bl_A_final_bbox) / 2
    half_height_B = bbox_height(bl_B.final_bbox) / 2

    overlap_x = (half_width_A + half_width_B) - abs(center_A[0] - center_B[0])
    overlap_y = (half_height_A + half_height_B) - abs(center_A[1] - center_B[1])

    ### ??? TODO
    if overlap_x <= 0 or overlap_y <= 0:
        push_bias = 10 # Perfect overlap so "overlap is 0" (wtf)
        # raise RuntimeError('This should never happen. No collision in compute_repulsion_force ???')
    else:
        push_bias = 0
    
    repulsion_force = initialize_displacement()

    ALPHA = 0.2 * 1.0

    if overlap_x < overlap_y:
        if center_A[0] < center_B[0]:
            # Push box A left.
            repulsion_force[0] = -1 * overlap_x * ALPHA + push_bias
        else:
            # Push right instead.
            repulsion_force[0] = overlap_x * ALPHA + push_bias
    else:
        if center_A[1] < center_B[1]:
            # Push box A up.
            repulsion_force[1] = -1 * overlap_y * ALPHA + push_bias
        else:
            # Push down instead.
            repulsion_force[1] = overlap_y * ALPHA + push_bias

    return repulsion_force

def compute_attraction_to_anchor_point(bl: TextBlock):
    BETA = 0.05 # 0.05 # How strong the force should be. Larger is stronger.

    center = bbox_center(bl.final_bbox)

    attraction_force = initialize_displacement() # [0(x), 0(y)]
    attraction_force[0] = (bl.anchor_point[0] - center[0]) * BETA
    attraction_force[1] = (bl.anchor_point[1] - center[1]) * BETA

    return attraction_force

def compute_boundary_repulsion(bl: TextBlock, image_width: int, image_height: int, margin: int = 0):
    BETA = 1.0

    width_start = margin
    height_start = margin
    width_end = image_width - margin
    height_end = image_height - margin

    boundary_force = initialize_displacement()

    if bl.final_bbox[0] <= width_start:
        # Push right.
        boundary_force[0] = -1 * (bl.final_bbox[0] - width_start)

    if bl.final_bbox[2] >= width_end:
        # Push left.
        boundary_force[0] = width_end - bl.final_bbox[2]

    if bl.final_bbox[1] <= height_start:
        # Push down.
        boundary_force[1] = -1 * (bl.final_bbox[1] - height_start)

    if bl.final_bbox[3] >= height_end:
        # Push right.
        boundary_force[1] = height_end - bl.final_bbox[3]

    boundary_force[0] = boundary_force[0] * BETA
    boundary_force[1] = boundary_force[1] * BETA

    return boundary_force

def modify_displacement(force_A: List[float], force_B: List[float]):
    return [force_A[0] + force_B[0], force_A[1] + force_B[1]]

def compute_stop_threshold(image_width: int, image_height: int):
    ALPHA = 0.01 # 0.1%

    diag = ((image_width ** 2) + (image_height ** 2)) ** 0.5

    return (diag * ALPHA)

def manipulate_layout(blocks: List[TextBlock], image: Image.Image, MAX_ITERATIONS = 300):
    with logger.begin_event("Manipulating layout") as ctx:
        for bl in blocks:
            bl.anchor_point = bbox_center(bl.original_bbox)

            # Initialize placement.
            bl.final_bbox = center_on_point(bl.final_bbox, bl.anchor_point)

            bl.mass = compute_mass(bl)

            bl.displacement = initialize_displacement()

        damping_factor = 0.9

        bbox_margins = max(image.width * 0.02, image.height * 0.02)

        stop_thr = compute_stop_threshold(image.width, image.height)

        for i in range(MAX_ITERATIONS):
            can_end = True # False if a collision is found.
            overlapping_id_map = set()

            for bl_A in blocks:
                for bl_B in blocks:
                    if bl_A.uuid == bl_B.uuid:
                        continue # Same box - the inner loop is to iterate over every OTHER box.

                    a_to_b = f'{bl_A.uuid}><{bl_B.uuid}'
                    b_to_a = f'{bl_B.uuid}><{bl_A.uuid}'
                    if a_to_b in overlapping_id_map or b_to_a in overlapping_id_map:
                        continue
                    else:
                        # No point checking the same pair twice - plus they would cancel each other out if they did collide.
                        overlapping_id_map.add(a_to_b)
                        overlapping_id_map.add(b_to_a)

                    if bboxes_overlap(bl_A.final_bbox, bl_B.final_bbox, margin=bbox_margins):
                        repulsion = compute_repulsion_force(bl_A, bl_B, margin=bbox_margins)

                        total_mass = bl_A.mass + bl_B.mass

                        # The "heavier" boxes move less than the "lighter" boxes.
                        bl_A.displacement[0] += repulsion[0] * (bl_B.mass / total_mass)
                        bl_A.displacement[1] += repulsion[1] * (bl_B.mass / total_mass)

                        bl_B.displacement[0] -= repulsion[0] * (bl_A.mass / total_mass)
                        bl_B.displacement[1] -= repulsion[1] * (bl_A.mass / total_mass)

                        can_end = False # Did collide sadly.

                # After displacing other boxes, "spring" or "lure" block A slightly back to its original position.
                anchor_force = compute_attraction_to_anchor_point(bl_A)
                bl_A.displacement = modify_displacement(bl_A.displacement, anchor_force)
                #print(f'({bl_A.uuid[:4]}) WITH ANCHOR FORCE: {bl_A.displacement}')

                # Try to move the text away from the edge of the image.
                image_margins = max(image.width * 0.015, image.height * 0.015)
                boundary_force = compute_boundary_repulsion(bl_A, image.width, image.height, margin=image_margins)
                bl_A.displacement = modify_displacement(bl_A.displacement, boundary_force)

                if boundary_force[0] != 0.0 or boundary_force[1] != 0.0:
                    can_end = False # Still out of bounds.

                #print(f'({bl_A.uuid[:4]}) WITH BOUNDARY FORCE: {bl_A.displacement}')

            total_movement = 0.0
            for bl in blocks:
                bl.displacement[0] = bl.displacement[0] * damping_factor
                bl.displacement[1] = bl.displacement[1] * damping_factor

                #print(f'({bl.uuid[:4]}) DISPLACING BBOX with FORCE {bl.displacement}')

                for x in bl.final_bbox:
                    if x >= 9000 or x <= -9000:
                        raise RuntimeError('NOOOO')

                total_movement = total_movement + compute_displacement_size(bl.displacement)
                bl.final_bbox = displace_bbox(bl.final_bbox, bl.displacement)

                bl.displacement = initialize_displacement()

            # End conditions:
            if total_movement <= stop_thr and can_end:
                break

            if i >= MAX_ITERATIONS:
                break

    ctx.log(f'Done manipulating layout', iterations_used=(i+1))