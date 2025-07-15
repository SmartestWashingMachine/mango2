from gandy.image_redrawing.physics.text_block import TextBlock
from gandy.utils.speech_bubble import SpeechBubble
from typing import List
from gandy.utils.fancy_logger import logger
from gandy.image_redrawing.physics.misc_utils import bbox_area, bbox_center, bboxes_overlap, bbox_width, bbox_height
from gandy.image_redrawing.physics.manipulate_layout import center_on_point, compute_boundary_repulsion, manipulate_layout, modify_displacement, displace_bbox
from gandy.image_redrawing.physics.compute_global_font_size import wrap_text
from PIL import Image

def last_ditch_layout(blocks: List[TextBlock], draw_manager, image: Image.Image, min_font_size: int = 8, MAX_ITERATIONS = 30):
    with logger.begin_event("Manipulating layout by shrinking offending lesser texts if needed.") as ctx:
        bbox_margins = max(image.width * 0.01, image.height * 0.01)

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
                        can_end = False

                        # Shrink the box with less mass ("less important")
                        # We shrink it by decreasing the font size - bbox_from_wrapped_text will see that and produce a smaller final bbox.
                        block_to_shrink = bl_A
                        if bl_A.mass > bl_B.mass:
                            block_to_shrink = bl_B

                        block_to_shrink.font_size = max(min_font_size, block_to_shrink.font_size - 1)

                        additional_width_tolerance = 0.8

                        block_to_shrink.wrapped_lines = wrap_text(block_to_shrink.translated_text, block_to_shrink.font_size, bbox_width(block_to_shrink.original_bbox) * additional_width_tolerance)
                        block_to_shrink.final_bbox = draw_manager.bbox_from_wrapped_text(block_to_shrink.wrapped_lines, block_to_shrink.font_size)
                        block_to_shrink.final_bbox = center_on_point(block_to_shrink.final_bbox, block_to_shrink.anchor_point)

                image_margins = max(image.width * 0.015, image.height * 0.015)
                boundary_force = compute_boundary_repulsion(bl_A, image.width, image.height, margin=image_margins)
                bl_A.displacement = modify_displacement(bl_A.displacement, boundary_force)
                bl_A.final_bbox = displace_bbox(bl_A.final_bbox, bl_A.displacement)

                if boundary_force[0] != 0.0 or boundary_force[1] != 0.0:
                    can_end = False # Still out of bounds.

                if not can_end:
                    manipulate_layout(blocks, image, MAX_ITERATIONS=10)

            if can_end:
                ctx.log("Managed to successfully fit all offending boxes.", iterations_used=i)
                return None

    ctx.log("Failed to fit in all offending boxes.", iterations_used=MAX_ITERATIONS)
    return None