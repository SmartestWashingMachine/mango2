from PIL import ImageFont, ImageDraw, Image
from typing import List
import textwrap
from math import floor
from string import ascii_letters
from gandy.image_redrawing.base_image_redraw import BaseImageRedraw

"""

Uses multiple font sizes for the entire image, and usually does not break characters in words.

Small text regions (e.g: SFX) have their own font sizes.
One font size is determined for normal-sized text regions.

"""


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


def compute_min_max_font_sizes(image_width: int, image_height: int):
    # image_area = image_width * image_height

    # min_font_size = 6 + round(image_width * 0.015) + round(image_height * 0.001)
    # min_font_size = 6 + round(image_width * 0.008)
    # min_font_size = 6 + round(image_width * 0.009)
    min_font_size = 6 + round(image_width * 0.012)
    min_font_size = max(min_font_size, 9)

    max_font_size = round(min_font_size * 2.5)
    return min_font_size, max_font_size


class ImageRedrawGlobalApp(BaseImageRedraw):
    def __init__(self):
        super().__init__()

    def wrap_text(self, text, max_chars_per_line, can_break=False):
        """
        wrapped_text = textwrap.fill(
            text=text,
            width=max_chars_per_line,
            break_long_words=can_break,
        )
        """
        w = CustomWrapper(width=max_chars_per_line, break_long_words=can_break)
        wrapped_text = w.fill(text)

        return wrapped_text

    def words_did_break(self, text, max_chars_per_line):
        # TODO: Optimize

        # If text is just one word, then it's always False.
        try:
            t = " ".split(text)
        except ValueError:
            return False

        a = textwrap.wrap(text, width=max_chars_per_line, break_long_words=False)
        b = textwrap.wrap(text, width=max_chars_per_line, break_long_words=True)
        # ['hello wo', 'rld its me']
        # ['hello world', 'its me']

        if len(a) != len(b):
            return True

        for aa, bb in zip(a, b):
            if aa != bb:
                return True

        return False

    def compute_font_metrics(self, s_bb, text, base_font_size, min_font_size: int):
        width = floor(s_bb[2] - s_bb[0])
        height = floor(s_bb[3] - s_bb[1])

        best_size = None  # tuple of width and height.
        last_one_fits = False
        max_char_count = 99

        best_font_size = base_font_size

        while best_size is None or (best_size[0] > width or best_size[1] > height):
            candidate_font_size = best_font_size

            font = ImageFont.truetype(
                "resources/fonts/font.otf", candidate_font_size, encoding="unic"
            )

            avg_char_width = sum(font.getsize(char)[0] for char in ascii_letters) / len(
                ascii_letters
            )
            candidate_max_char_count = max(
                1, int(width / avg_char_width)
            )  # Max true chars before it overflows the width.
            wrapped_text = self.wrap_text(
                text,
                candidate_max_char_count,
                can_break=candidate_font_size
                <= min_font_size,  # Words can only be broken at the minimum font size.
            )

            candidate_size = font.getsize_multiline(wrapped_text)

            if (
                candidate_size[0] < width
                and candidate_size[1] < height
                and not self.words_did_break(text, candidate_max_char_count)
            ):
                # Stop at the first biggest size that fits.
                best_font_size = candidate_font_size
                last_one_fits = True
                best_size = candidate_size
                max_char_count = candidate_max_char_count

                break

            if candidate_font_size <= min_font_size:
                # Could not fit at all :(
                best_font_size = candidate_font_size
                last_one_fits = False
                best_size = candidate_size
                max_char_count = candidate_max_char_count

                break
            else:
                best_font_size -= 1

        best_font_size = max(min_font_size, best_font_size)

        return last_one_fits, best_font_size, max_char_count, best_size

    def find_best_global_font_sizes(
        self,
        s_bboxes,
        texts: List[str],
        i: int,
        min_font_size: int,
        max_font_size: int,
    ):
        best_font_size = max_font_size
        text_details = []

        _other_i = i

        areas = []
        for s_bb in s_bboxes:
            width = floor(s_bb[2] - s_bb[0])
            height = floor(s_bb[3] - s_bb[1])

            area = width * height
            areas.append(area)

            _other_i += 1

        mean_area = sum(areas) / len(areas)

        for j, s_bbox in enumerate(s_bboxes):
            s_bb = s_bbox

            if i >= len(texts):
                print(
                    "WARNING: repaint_image has more speech bubbles than texts. Some speech bubbles were left untouched."
                )
                break

            text = texts[i]

            if isinstance(text, list):
                print(
                    "WARNING: texts should be a list of strings. Detected list of lists:"
                )
                print(
                    "Taking the first element out of the list and assuming it is a string."
                )
                text = text[0]
                if not text:
                    print("No item found in list. Skipping.")
                    continue

            text = self.uppercase_text(text)

            left = floor(s_bb[0])
            top = floor(s_bb[1])

            width = floor(s_bb[2] - s_bb[0])
            height = floor(s_bb[3] - s_bb[1])
            area = width * height

            # MEAN_FACTOR = 0.7
            # MEAN_FACTOR = 0.55
            MEAN_FACTOR = 0.65
            if area <= (mean_area * MEAN_FACTOR):
                best_font_size_to_use = best_font_size
                (
                    text_will_fit,
                    best_font_size_to_use,
                    max_chars_per_line,
                    (best_width, best_height),
                ) = self.compute_font_metrics(
                    s_bb,
                    text,
                    best_font_size_to_use,
                    min_font_size=min_font_size,
                )
            else:
                (
                    text_will_fit,
                    best_font_size,
                    max_chars_per_line,
                    (best_width, best_height),
                ) = self.compute_font_metrics(
                    s_bb,
                    text,
                    best_font_size,
                    min_font_size=min_font_size,
                )
                best_font_size_to_use = best_font_size

            wrapped_text = self.wrap_text(
                text, max_chars_per_line, can_break=not text_will_fit
            )
            start_top = max((height - best_height) // 2, 0)

            # offset_left = (width - best_width) // 2
            offset_left = max((width - best_width) // 2, 0)

            text_details.append(
                [
                    wrapped_text,
                    left + offset_left,
                    top + start_top,
                    best_font_size_to_use,
                ]
            )

            i += 1

        # For each bucket:
        # Return i (integer) and a list of list of wrapped texts with their left and top positions and best font size.
        return i, text_details

    def process(self, image: Image.Image, bboxes, target_texts, text_colors):
        new_image = image.copy()
        if len(bboxes) == 0:
            return new_image

        draw = ImageDraw.Draw(new_image)

        min_font_size, max_font_size = compute_min_max_font_sizes(
            new_image.width, new_image.height
        )

        i = 0
        i, text_details = self.find_best_global_font_sizes(
            bboxes,
            target_texts,
            i,
            min_font_size=min_font_size,
            max_font_size=max_font_size,
        )

        for idx, td in enumerate(text_details):
            # td = A list containing [wrappedtextstring, leftinteger, topinteger, fontsizeinteger]
            best_font_size = td[3]
            font = ImageFont.truetype(
                "resources/fonts/font.otf", best_font_size, encoding="unic"
            )

            draw.multiline_text(
                (td[1], td[2]),
                td[0],
                self.get_text_color(text_colors, idx),
                font,
                align="center",
                stroke_fill=self.get_stroke_color(text_colors, idx),
                stroke_width=max(2, best_font_size // 7),
            )

        return new_image
