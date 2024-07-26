from PIL import ImageFont, ImageDraw, Image
import textwrap
from math import floor
from string import ascii_letters
from gandy.image_redrawing.base_image_redraw import BaseImageRedraw
from gandy.image_redrawing.image_redraw_global import compute_min_max_font_sizes
from gandy.utils.compute_stroke_size import compute_stroke_size

# "What happened to V1?" We don't talk about V1.
class ImageRedrawV2App(BaseImageRedraw):
    def __init__(self):
        super().__init__()

    def wrap_text(self, text, max_chars_per_line):
        wrapped_text = textwrap.fill(
            text=text, width=max_chars_per_line, break_long_words=False
        )

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

    def compute_font_metrics(self, s_bb, text, MIN_FONT_SIZE: int, MAX_FONT_SIZE: int):
        width = floor(s_bb[2] - s_bb[0])
        height = floor(s_bb[3] - s_bb[1])

        best_size = None  # tuple of width and height.
        last_one_fits = False
        max_char_count = 99

        base_font_size = MIN_FONT_SIZE
        best_font_size = base_font_size

        while best_size is None or (best_size[0] < width and best_size[1] < height):
            candidate_font_size = best_font_size + 1

            font = ImageFont.truetype(
                "resources/fonts/font.otf", candidate_font_size, encoding="unic"
            )

            avg_char_width = sum(font.getsize(char)[0] for char in ascii_letters) / len(
                ascii_letters
            )
            candidate_max_char_count = max(
                1, int(width / avg_char_width)
            )  # Max true chars before it overflows the width.
            wrapped_text = self.wrap_text(text, candidate_max_char_count)

            candidate_size = font.getsize_multiline(wrapped_text)

            if (
                candidate_size[0] < width
                and candidate_size[1] < height
                and not self.words_did_break(text, candidate_max_char_count)
            ):
                best_font_size = candidate_font_size
                last_one_fits = True
                best_size = candidate_size
                max_char_count = candidate_max_char_count
            elif best_size is None:
                # Could not fit at all :(
                best_font_size = candidate_font_size
                last_one_fits = False
                best_size = candidate_size
                max_char_count = candidate_max_char_count

                break
            else:
                break

            if candidate_font_size >= MAX_FONT_SIZE:
                break

        best_font_size = max(MIN_FONT_SIZE, best_font_size)

        return last_one_fits, best_font_size, max_char_count, best_size

    def process(self, image: Image.Image, bboxes, target_texts, text_colors):
        new_image = image.copy()
        if len(bboxes) == 0:
            return new_image

        draw = ImageDraw.Draw(new_image)

        s_bboxes = bboxes
        texts = target_texts

        MIN_FONT_SIZE, MAX_FONT_SIZE = compute_min_max_font_sizes(
            new_image.width, new_image.height
        )

        for i, s_bbox in enumerate(s_bboxes):
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
            height = floor(s_bb[3] - s_bb[1])

            (
                text_will_fit,
                best_font_size,
                max_chars_per_line,
                (best_width, best_height),
            ) = self.compute_font_metrics(
                s_bb, text, MIN_FONT_SIZE=MIN_FONT_SIZE, MAX_FONT_SIZE=MAX_FONT_SIZE
            )

            font = ImageFont.truetype(
                "resources/fonts/font.otf", best_font_size, encoding="unic"
            )
            wrapped_text = self.wrap_text(text, max_chars_per_line)
            # See: https://github.com/python-pillow/Pillow/issues/5669

            start_top = (height - best_height) // 2
            draw.multiline_text(
                (left, top + start_top),
                wrapped_text,
                self.get_text_color(text_colors, i),
                font,
                align="center",
                stroke_fill=self.get_stroke_color(text_colors, i),
                stroke_width=compute_stroke_size(best_font_size),
            )

        return new_image
