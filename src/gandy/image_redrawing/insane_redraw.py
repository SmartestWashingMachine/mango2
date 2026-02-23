import numpy as np
from PIL import Image, ImageDraw, ImageFont
from gandy.state.debug_state import debug_state
from gandy.utils.speech_bubble import SpeechBubble
from gandy.image_redrawing.base_image_redraw import BaseImageRedraw
from PIL import Image, ImageDraw
from typing import List, Union

# ============================================================
# CONFIGURATION
# ============================================================

MIN_READABLE_SIZE = 12
MAX_FONT_SIZE = 80
BASE_TOLERANCE = 0.15
DEFAULT_MARGIN = 4
LINE_SPACING = 1.15
SAFE_IMAGE_MARGIN = 2

VOWELS = set("aeiouAEIOU")

# ============================================================
# WORD BREAKING (NO DEPENDENCIES)
# ============================================================

def break_long_word(word, font, max_width):
    """
    Guaranteed to return segments that fit max_width.
    """
    # If entire word fits, return directly
    if font.getlength(word) <= max_width:
        return [word]

    # Try heuristic split near center at vowel boundary
    mid = len(word) // 2
    best_split = None

    for offset in range(len(word) // 2):
        for direction in (-1, 1):
            idx = mid + offset * direction
            if 1 <= idx < len(word) - 1:
                if word[idx] in VOWELS:
                    left = word[:idx] + "-"
                    if font.getlength(left) <= max_width:
                        best_split = idx
                        break
        if best_split:
            break

    if best_split:
        left = word[:best_split] + "-"
        right = word[best_split:]
        return [left] + break_long_word(right, font, max_width)

    # Fallback: character-level guaranteed break
    segments = []
    current = ""

    for char in word:
        trial = current + char
        if font.getlength(trial) <= max_width:
            current = trial
        else:
            if current:
                segments.append(current + "-")
            current = char

    if current:
        segments.append(current)

    return segments

# ============================================================
# TEXT WRAPPING
# ============================================================

def wrap_text(text, font, max_width):
    words = text.split()
    lines = []
    current = ""

    for word in words:
        trial = f"{current} {word}".strip()

        if font.getlength(trial) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
                current = ""

            # Handle long word
            segments = break_long_word(word, font, max_width)
            for seg in segments[:-1]:
                lines.append(seg)
            current = segments[-1]

    if current:
        lines.append(current)

    return lines

# ============================================================
# MEASURE BLOCK
# ============================================================

def measure_block(lines, font, spacing=LINE_SPACING):
    ascent, descent = font.getmetrics()
    line_height = ascent + descent

    widths = []
    total_height = 0

    for line in lines:
        widths.append(font.getlength(line))
        total_height += line_height * spacing

    return (max(widths) if widths else 0), total_height, line_height

# ============================================================
# RECT UTILITIES
# ============================================================

def rect_contains(outer, inner):
    return (
        inner[0] >= outer[0] and
        inner[1] >= outer[1] and
        inner[2] <= outer[2] and
        inner[3] <= outer[3]
    )

def rect_intersects(a, b):
    return not (
        a[2] <= b[0] or
        a[0] >= b[2] or
        a[3] <= b[1] or
        a[1] >= b[3]
    )

# ============================================================
# FIND MAX FONT SIZE (Binary Search)
# ============================================================

def find_max_size(box, text, font_path, image_rect):
    x1, y1, x2, y2 = box
    bubble_width = x2 - x1 - 2 * DEFAULT_MARGIN
    bubble_height = y2 - y1 - 2 * DEFAULT_MARGIN

    low = MIN_READABLE_SIZE
    high = MAX_FONT_SIZE
    best = None

    while low <= high:
        mid = (low + high) // 2
        font = ImageFont.truetype(font_path, mid)
        lines = wrap_text(text, font, bubble_width)
        w, h, _ = measure_block(lines, font)

        text_x = x1 + DEFAULT_MARGIN + (bubble_width - w) / 2
        text_y = y1 + DEFAULT_MARGIN + (bubble_height - h) / 2
        rect = [text_x, text_y, text_x + w, text_y + h]

        if w <= bubble_width and h <= bubble_height and rect_contains(image_rect, rect):
            best = mid
            low = mid + 1
        else:
            high = mid - 1

    return best if best else MIN_READABLE_SIZE

# ============================================================
# MAIN LAYOUT ENGINE
# ============================================================

def draw_background(font, draw, line, lx, cursor_y, size, fill):
    stroke_expand = max(1, size // 5)

    for dx in range(-stroke_expand, stroke_expand + 1):
        for dy in range(-stroke_expand, stroke_expand + 1):
            # Optional: skip diagonals for lighter halo
            if abs(dx) + abs(dy) > stroke_expand:
                continue
            draw.text((lx + dx, cursor_y + dy), line, font=font, fill=fill)

def layout_page(image, bubble_boxes, texts, font_path, draw_text_metadatas):

    draw = ImageDraw.Draw(image)

    image_rect = [
        SAFE_IMAGE_MARGIN,
        SAFE_IMAGE_MARGIN,
        image.width - SAFE_IMAGE_MARGIN,
        image.height - SAFE_IMAGE_MARGIN
    ]

    placed_rects = []

    # PASS 1: Compute max sizes
    max_sizes = []
    for box, text in zip(bubble_boxes, texts):
        size = find_max_size(box, text, font_path, image_rect)
        max_sizes.append(size)

    base_size = int(np.median(max_sizes))

    # PASS 2: Final layout
    for idx, (box, text, max_size) in enumerate(zip(bubble_boxes, texts, max_sizes)):
        background_fill = "black" if draw_text_metadatas[idx]["fill"] == "white" else "white"

        x1, y1, x2, y2 = box
        bubble_width = x2 - x1 - 2 * DEFAULT_MARGIN
        bubble_height = y2 - y1 - 2 * DEFAULT_MARGIN

        allowed_min = max(MIN_READABLE_SIZE, int(base_size * (1 - BASE_TOLERANCE)))
        allowed_max = min(max_size, int(base_size * (1 + BASE_TOLERANCE)))

        success = False

        for size in range(allowed_max, allowed_min - 1, -1):
            font = ImageFont.truetype(font_path, size)
            lines = wrap_text(text, font, bubble_width)
            w, h, line_height = measure_block(lines, font)

            if w > bubble_width or h > bubble_height:
                continue

            text_x = x1 + DEFAULT_MARGIN + (bubble_width - w) / 2
            text_y = y1 + DEFAULT_MARGIN + (bubble_height - h) / 2
            rect = [text_x, text_y, text_x + w, text_y + h]

            if not rect_contains(image_rect, rect):
                continue

            if any(rect_intersects(rect, r) for r in placed_rects):
                continue

            # Render
            cursor_y = text_y
            stroke_width = max(1, size // 15)

            for line in lines:
                lw = font.getlength(line)
                lx = x1 + DEFAULT_MARGIN + (bubble_width - lw) / 2

                draw_background(font, draw, line, lx, cursor_y, size, fill=background_fill)
                draw.text(
                    (lx, cursor_y),
                    line,
                    font=font,
                    stroke_width=stroke_width,
                    **draw_text_metadatas[idx],
                )

                cursor_y += line_height * LINE_SPACING

            placed_rects.append(rect)
            success = True
            break

        # HARD FALLBACK — GUARANTEED RENDER (FIXED CENTERING)
        if not success:
            font = ImageFont.truetype(font_path, MIN_READABLE_SIZE)
            lines = wrap_text(text, font, bubble_width * 0.98)
            w, h, line_height = measure_block(lines, font)

            # Proper centering attempt
            if h <= bubble_height:
                text_y = y1 + DEFAULT_MARGIN + (bubble_height - h) / 2
            else:
                text_y = y1 + DEFAULT_MARGIN  # cannot center if taller than box

            text_x = x1 + DEFAULT_MARGIN + (bubble_width - w) / 2

            rect = [text_x, text_y, text_x + w, text_y + h]

            # Resolve collisions by shifting downward
            shift = 0
            while any(rect_intersects(rect, r) for r in placed_rects):
                shift += 2
                new_y = text_y + shift
                rect = [text_x, new_y, text_x + w, new_y + h]

                # If we exceed image bounds, stop shifting
                if rect[3] > image_rect[3]:
                    break

            cursor_y = rect[1]
            stroke_width = 1

            for line in lines:
                lw = font.getlength(line)
                lx = x1 + DEFAULT_MARGIN + (bubble_width - lw) / 2

                draw_background(font, draw, line, lx, cursor_y, 1, background_fill)
                draw.text(
                    (lx, cursor_y),
                    line,
                    font=font,
                    stroke_width=stroke_width,
                    **draw_text_metadatas[idx],
                )

                cursor_y += line_height * 1.05

            placed_rects.append(rect)

    return image

class InsaneRedraw(BaseImageRedraw):
    def process(
        self,
        image: Image.Image,
        bboxes: List[SpeechBubble],
        target_texts: List[str],
        text_colors: List[str],
    ):
        if debug_state.debug or debug_state.debug_redraw:
            self.save_recording(image, bboxes, target_texts, text_colors)

        draw_text_metadatas = []
        for idx in range(len(text_colors)):
            md = {
                "fill": self.get_text_color(text_colors, idx),
                "stroke_fill": self.get_stroke_color(text_colors, idx),
            }
            draw_text_metadatas.append(md)

        return layout_page(image, bboxes, target_texts, "resources/fonts/font.otf", draw_text_metadatas)

    def run_recording(self, did: str):
        import json
        from glob import glob

        img_path = glob(f'./debugdumps/smartredraw/{did}/*.png')[0]
        image = Image.open(img_path)

        with open(f'./debugdumps/smartredraw/{did}/data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

        return self.process(image, data['bboxes'], data['target_texts'], data['text_colors'])
    
    def save_recording(self, image, bboxes, target_texts, text_colors):
        import uuid
        import os
        import json

        did = uuid.uuid4().hex
        os.makedirs(f'./debugdumps/smartredraw/{did}', exist_ok=True)

        # Save and load with same extension; lest bit depth be different, causing differing font sizing.
        image.save(f'./debugdumps/smartredraw/{did}/{debug_state.metadata["cur_img_name"]}.png')

        data = { 'bboxes': bboxes, 'target_texts': target_texts, 'text_colors': text_colors, }
        with open(f'./debugdumps/smartredraw/{did}/data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f)