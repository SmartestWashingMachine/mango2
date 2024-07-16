from PIL import ImageFont, ImageDraw, Image
from typing import List
from gandy.utils.speech_bubble import SpeechBubble
from gandy.image_redrawing.image_redraw_global import (
    ImageRedrawGlobalApp,
    compute_min_max_font_sizes,
)


class ImageRedrawBigGlobalApp(ImageRedrawGlobalApp):
    def box_overlaps(self, box, other_boxes):
        """
        Returns True if box overlaps with any of the other boxes, and False otherwise.

        Assume other_boxes is a list of list of coords, and box is a list of coords.
        """
        a_x1, a_y1, a_x2, a_y2 = box

        def _is_overlapping_1d(a_1, b_1, a_2, b_2):
            # a_2 must be greater than a_1. b_2 must be greater than b_1. a_1 and a_2 must be for the same box. b_1 and b_2 must be for another same box.
            return a_2 >= b_1 and b_2 >= a_1

        for other in other_boxes:
            # (x1, y1, x2, y2)
            b_x1, b_y1, b_x2, b_y2 = other

            # From: https://stackoverflow.com/questions/20925818/algorithm-to-check-if-two-boxes-overlap
            is_overlapping = _is_overlapping_1d(
                a_x1, b_x1, a_x2, b_x2
            ) and _is_overlapping_1d(a_y1, b_y1, a_y2, b_y2)
            if is_overlapping:
                return True

        return False

    def does_overflow(
        self, s_bb: SpeechBubble, other_boxes: List[SpeechBubble], image: Image.Image
    ):
        too_left = s_bb[0] < 0
        too_right = s_bb[2] >= image.width
        too_up = s_bb[1] < 0
        too_down = s_bb[3] >= image.height
        return (
            self.box_overlaps(s_bb, other_boxes)
            or too_left
            or too_right
            or too_up
            or too_down
        )

    def expand_boxes(self, bboxes: List[SpeechBubble], image: Image.Image):
        """
        Expands each box in size. (INPLACE)

        It first tries to simply expand width by up to +300% (until aspect ratio approaches 1.3).

        If aspect ratio could not be reached:
            tries to expand height by up to +40% (starting on the top then bottom).
        """
        # TODO: Super inefficient.

        max_width_increase = 3.0
        max_height_increase = 0.4
        aspect_threshold = 1.3
        step_val = 0.1

        for i, s_bb in enumerate(bboxes):
            old_x1, old_y1, old_x2, old_y2 = s_bb
            old_width = old_x2 - old_x1
            old_height = old_y2 - old_y1

            others = [bboxes[j] for j in range(len(bboxes)) if j != i]

            # First try expanding width.
            width_attempt = step_val
            while True:
                if width_attempt >= max_width_increase:
                    # Max width found.
                    break

                did_expand = False
                expanded_width = round(old_width * width_attempt)

                new_x2 = old_x2 + expanded_width
                new_x1 = old_x1 - expanded_width

                # First try to expand the right side.
                if not self.does_overflow(
                    (s_bb[0], s_bb[1], new_x2, s_bb[3]), others, image
                ):
                    s_bb[2] = new_x2
                    did_expand = True
                # Else try to expand the left side.
                elif not self.does_overflow(
                    (new_x1, s_bb[1], s_bb[2], s_bb[3]), others, image
                ):
                    s_bb[0] = new_x1
                    did_expand = True

                if did_expand:
                    new_aspect_ratio = (s_bb[2] - s_bb[0]) / (s_bb[3] - s_bb[1])
                    if new_aspect_ratio >= aspect_threshold:
                        # Met aspect ratio threshold. No need to expand width any further..
                        break

                    width_attempt += step_val
                    # Aspect ratio not met. Try expanding the size even further.
                    continue

                break  # Failure case. Width could not be extended in either side anymore.

            # Re-update fallback values.
            old_x1, old_y1, old_x2, old_y2 = s_bb
            old_width = old_x2 - old_x1
            old_height = old_y2 - old_y1

            # Then try expanding height if aspect ratio threshold is not met. (box is thin)
            cur_aspect = old_width / old_height
            if cur_aspect < aspect_threshold:
                height_attempt = step_val
                while True:
                    if height_attempt >= max_height_increase:
                        # Max height found.
                        break

                    did_expand = False
                    expanded_height = round(old_height * height_attempt)

                    new_y2 = old_y2 + expanded_height
                    new_y1 = old_y1 - expanded_height

                    # First try to expand the top side.
                    if not self.does_overflow(
                        (s_bb[0], new_y1, s_bb[2], s_bb[3]), others, image
                    ):
                        s_bb[1] = new_y1
                        did_expand = True
                    # Else try to expand the bottom side.
                    elif not self.does_overflow(
                        (s_bb[0], s_bb[1], s_bb[2], new_y2), others, image
                    ):
                        s_bb[3] = new_y2
                        did_expand = True

                    if did_expand:
                        height_attempt += step_val
                        # Try expanding the size even further.
                        continue

                    break  # Failure case. Height could not be extended in either side anymore.

        return bboxes

    def process(self, image: Image.Image, bboxes, target_texts, text_colors):
        new_image = image.copy()
        if len(bboxes) == 0:
            return new_image

        draw = ImageDraw.Draw(new_image)

        # Expand hack, since object detection model tends to fit the text tightly rather than the bubble.
        bboxes = self.expand_boxes(bboxes, image)

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
