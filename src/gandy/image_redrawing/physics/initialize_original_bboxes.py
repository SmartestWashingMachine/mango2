from gandy.image_redrawing.physics.misc_utils import bbox_width, bbox_aspect_ratio, bboxes_overlap, bbox_area, bbox_height
from PIL import Image
from gandy.image_redrawing.physics.text_block import TextBlock
from typing import List

def adjust_box_for_aspect_ratio(x_min, y_min, x_max, y_max, target_aspect_ratio):
    """
    Calculates the x% float needed to adjust a bounding box's width
    to achieve a target aspect ratio, while maintaining the original height
    and centering the width expansion.

    Args:
        x_min (float): The minimum x-coordinate of the bounding box.
        y_min (float): The minimum y-coordinate of the bounding box.
        x_max (float): The maximum x-coordinate of the bounding box.
        y_max (float): The maximum y-coordinate of the bounding box.
        target_aspect_ratio (float): The desired width / height aspect ratio.

    Returns:
        float: The x% (as a float, e.g., 0.5 for 50%) by which to expand
               the width. Returns None if a valid expansion is not possible
               (e.g., if target_aspect_ratio is less than or equal to
               the original aspect ratio, or if the height is zero).
    """

    original_width = x_max - x_min
    original_height = y_max - y_min

    if original_height <= 0:
        print("Error: Height of the box must be greater than zero.")
        return 0.0

    # Calculate the required new width based on the target aspect ratio and original height
    required_new_width = target_aspect_ratio * original_height

    # If the required new width is less than or equal to the original width,
    # it means we would need to shrink the box, or it already meets/exceeds
    # the target aspect ratio, which is not what the problem asks for (expansion).
    if required_new_width <= original_width:
        print(f"Warning: The original box already has an aspect ratio of "
              f"{original_width / original_height:.2f}, which is >= "
              f"the target of {target_aspect_ratio:.2f}. "
              f"No expansion needed for width. Returning 0.0 for x%.")
        return 0.0

    # The new width is (1.0 + x%) * original_width.
    # So, (1.0 + x%) = required_new_width / original_width
    # x% = (required_new_width / original_width) - 1.0
    
    x_percentage = (required_new_width / original_width) - 1.0

    return x_percentage

def adjust_box_for_image_coverage(bb, image_width: int, image_height: int, max_allowed_coverage_pct: float):
    image_area = image_width * image_height

    max_allowed_image_area = image_area * max_allowed_coverage_pct

    bb_width = bbox_width(bb)
    bb_height = bbox_height(bb)
    if bb_height == 0:
        return 0.0

    max_bb_width = max_allowed_image_area / bb_height

    width_expansion_amount = max_bb_width - bb_width

    if width_expansion_amount <= 0 or bb_width <= 0:
        return 0.0
    
    return max(1.0 - (width_expansion_amount / bb_width), 0)

def expand_bb_width(bb, left_pct: float, right_pct: float):
    wid = bbox_width(bb)

    return [
        bb[0] - (wid * left_pct),
        bb[1],
        bb[2] + (wid * right_pct),
        bb[3],
    ]

def expand_bboxes(blocks: List[TextBlock], image: Image.Image, scale_until_aspect_ratio=1.3):
    bbox_margins = max(image.width * 0.02, image.height * 0.02)

    for bl_A in blocks:
        # This is usually what is used: Try to increase the width until the aspect ratio (width/height) is 1.3.
        increase_from_balancing_aspect_ratio = adjust_box_for_aspect_ratio(
            x_min=bl_A.original_bbox[0],
            y_min=bl_A.original_bbox[1],
            x_max=bl_A.original_bbox[2],
            y_max=bl_A.original_bbox[3],
            target_aspect_ratio=scale_until_aspect_ratio,
        )
        # This is used as a safety measure in conjunction with "min" to "cap" the above factor:
        # Find the maximum width increase that doesn't go over 20% of the image area.
        increase_from_image_area_coverage = adjust_box_for_image_coverage(
            bl_A.original_bbox,
            image.width,
            image.height,
            max_allowed_coverage_pct=0.2
        )
        pct_increase = min(increase_from_balancing_aspect_ratio, increase_from_image_area_coverage)

        if pct_increase == 0.0:
            continue # Already sufficient in aspect ratio / area covered.

        reduce_each_step = 0.1 # Reduce pct_increase by 10% each failed attempt.
        max_steps = 10 # Max attempts before giving up in expanding the box.

        for step_i in range(max_steps):
            pct_reduct = pct_increase * reduce_each_step * step_i
            scale_pct = 1.0 + (pct_increase - pct_reduct)

            expanded_original_bbox = expand_bb_width(bl_A.original_bbox, scale_pct, scale_pct)

            is_valid = True

            for bl_B in blocks:
                if bl_A.uuid == bl_B.uuid:
                    continue # Same box - the inner loop is to iterate over every OTHER box.

                if bboxes_overlap(expanded_original_bbox, bl_B.original_bbox, margin=bbox_margins):
                    is_valid = False
                    break

            if is_valid:
                bl_A.original_bbox = expanded_original_bbox
                break


Keep scaling aspect ratio until width is a bit more than height
With exceptions:
If box height is massive relative to image height, scale it "less":
    - less as in 

    - As a simple heuristic, scale it such that it cannot take more than twice the image AREA it already is.


so now find the max pct increase before it goes to image AREA - then take min ebtween the two