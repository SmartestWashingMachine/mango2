from gandy.image_redrawing.physics.text_block import TextBlock
from gandy.image_redrawing.physics.misc_utils import bbox_width, bbox_height, bbox_area
from typing import List
import numpy as np
import textwrap
import regex as re
from PIL import ImageDraw
from PIL import Image
from gandy.utils.speech_bubble import SpeechBubble
from gandy.image_redrawing.physics.draw_manager import DrawManager
from gandy.image_redrawing.physics.font_manager import FONT_MANAGER
from gandy.utils.fancy_logger import logger

class CustomWrapper(textwrap.TextWrapper):
    def _handle_long_word(self, reversed_chunks, cur_line, cur_len, width):
        # Much like the normal text wrapper, but this one adds a hyphen to broken long words.

        if width < 1:
            space_left = 1
        else:
            space_left = width - cur_len

        if self.break_long_words:
            # This is the actual modification.
            cur_line.append(reversed_chunks[-1][:space_left] + "-")
            reversed_chunks[-1] = reversed_chunks[-1][space_left:]

        elif not cur_line:
            cur_line.append(reversed_chunks.pop())

def wrap_text(text: str, font_size: int, bbox_width: int):
    """
    Given a piece of text, breaks it according to the max_chars_per_line for use in PIL.
    """
    max_chars_per_line = FONT_MANAGER.compute_max_chars_per_line(font_size, bbox_width)

    max_word_len_before_breaking = 22

    words = re.split(r' |\n', text)
    max_word_len = max(len(w) for w in words)
    break_long_words = max_word_len >= max_word_len_before_breaking and len(words) > 1

    w = CustomWrapper(
        width=max_chars_per_line, break_long_words=break_long_words, break_on_hyphens=False
    )
    wrapped_text = w.fill(text)

    return wrapped_text

def compute_max_fitting_font_size(bl: TextBlock, draw_manager: DrawManager, starting_font_size: int, min_font_size: int):
    for cur_font_size in range(starting_font_size, min_font_size, -1):
        extra_width_allowance = 1.3
        fit_in_width = bbox_width(bl.original_bbox) * extra_width_allowance

        wrapped_lines = wrap_text(bl.translated_text, cur_font_size, fit_in_width)
        text_bbox = draw_manager.bbox_from_wrapped_text(wrapped_lines, cur_font_size)

        fit = (bbox_width(text_bbox) <= fit_in_width) and (bbox_height(text_bbox) <= bbox_height(bl.original_bbox))

        if fit:
            return cur_font_size # Largest possible font size since we go in reverse (next ones will be smaller - obviously also fitting).

    return min_font_size

def compute_min_max_font_sizes(img: Image.Image):
    """
    Compute the min and max font size for an image.
    """
    image_length = min(img.width, img.height)

    min_font_size = 4 + round(image_length * 0.008)
    min_font_size = max(min_font_size, 9)

    # max_font_size = round(min_font_size * 1.75)
    max_font_size = round(min_font_size * 4.0)

    return min_font_size, max_font_size

def reduce_font_size_if_too_cluttered(
    blocks: List[TextBlock],
    min_font_size: int,
    starting_font_size: int,
    draw_manager: DrawManager,
):
    if starting_font_size <= min_font_size:
        return min_font_size

    # A bit larger than the detected regions.
    total_detected_area = sum((bbox_area(bl.original_bbox) * 1.25) for bl in blocks)

    for cur_font_size in range(starting_font_size, min_font_size, -1):
        total_written_area = 0.0

        for bl in blocks:
            wrapped_lines = wrap_text(bl.translated_text, cur_font_size, bbox_width(bl.original_bbox))
            text_bbox = draw_manager.bbox_from_wrapped_text(wrapped_lines, cur_font_size)

            total_written_area += bbox_area(text_bbox)

        if total_written_area <= total_detected_area:
            return cur_font_size
        
    return min_font_size

def compute_global_font_size(blocks: List[TextBlock], draw_manager: DrawManager, img: Image.Image):
    with logger.begin_event("Compute global font size") as ctx:
        largest_font_sizes = []

        min_font_size, max_font_size = compute_min_max_font_sizes(img)
        max_font_size = reduce_font_size_if_too_cluttered(blocks, min_font_size, max_font_size, draw_manager)
        if max_font_size <= min_font_size:
            max_font_size = min_font_size + 1 # Just in case...

        ctx.log("Min/Max possible font sizes", min_font_size=min_font_size, max_font_size=max_font_size)

        for bl in blocks:
            largest_font_sizes.append(compute_max_fitting_font_size(bl, draw_manager, starting_font_size=max_font_size, min_font_size=min_font_size))

        best_font_size = np.percentile(np.array(largest_font_sizes), 75) # TODO: Verify

        best_font_size = round(best_font_size) # PIL does NOT support float font sizes. Must be integer.

        ctx.log("Largest font sizes found", largest_font_sizes=largest_font_sizes, best_font_size=best_font_size)

        # Apply font size & initial bboxes (mutates in-place) from the computed global font size.
        for bl in blocks:
            bl.font_size = best_font_size

            additional_width_tolerance = 1.3 # +30%

            bl.wrapped_lines = wrap_text(bl.translated_text, bl.font_size, bbox_width(bl.original_bbox) * additional_width_tolerance)
            bl.final_bbox = draw_manager.bbox_from_wrapped_text(bl.wrapped_lines, bl.font_size)

        return best_font_size
