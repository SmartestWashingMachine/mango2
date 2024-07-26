from PIL import ImageFont, ImageDraw, Image
from typing import List
from math import floor
from gandy.image_redrawing.base_image_redraw import BaseImageRedraw
import copy
from gandy.image_redrawing.smart.utils.get_box_size import get_box_height, get_box_width
from gandy.image_redrawing.smart.magic_box import MagicBox
from gandy.image_redrawing.smart.move_actions import (
    MoveAndPushToLeft,
    MoveAndPushToRight,
    MoveToDown,
    MoveToLeft,
    MoveToRight,
    MoveToUp,
)
from gandy.image_redrawing.smart.expand_aspect_actions import ExpandAspectAction
from gandy.image_redrawing.smart.constants import CLUTTER_THRESHOLD
from gandy.image_redrawing.smart.utils.box_aspect_good import box_aspect_good
from gandy.image_redrawing.smart.utils.box_is_bad import box_is_bad
from gandy.image_redrawing.smart.utils.calc_last_ditch_font_size import (
    calc_last_ditch_font_size,
)
from gandy.image_redrawing.smart.utils.recenter_box import recenter_box
from gandy.image_redrawing.smart.utils.compute_font_region import compute_font_region
from gandy.image_redrawing.smart.utils.load_font import load_font
from gandy.image_redrawing.smart.utils.compute_max_chars_per_line import (
    compute_max_chars_per_line,
)
from gandy.image_redrawing.smart.utils.wrap_text import wrap_text
from gandy.utils.compute_stroke_size import compute_stroke_size
from gandy.image_redrawing.smart.utils.get_vertical_spacing import get_vertical_spacing
from gandy.image_redrawing.smart.utils.compute_min_max_font_sizes import (
    compute_min_max_font_sizes,
)
from gandy.image_redrawing.smart.utils.text_overflows import text_overflows


class ImageRedrawGlobalSmartApp(BaseImageRedraw):
    def __init__(self):
        super().__init__()

    def compute_font_metrics(
        self, s_bb, text, base_font_size, min_font_size: int, draw
    ):
        """
        Tries to find the best possible font size for a given speech box.
        """
        width = get_box_width(s_bb)
        height = get_box_height(s_bb)

        best_size = None  # tuple of width and height.
        last_one_fits = False

        best_font_size = base_font_size

        while best_size is None or (best_size[0] > width or best_size[1] > height):
            candidate_font_size = best_font_size

            candidate_size = compute_font_region(candidate_font_size, width, text, draw)

            if not text_overflows(
                font_size=None,
                box_width=width,
                box_height=height,
                text=text,
                candidate_size=candidate_size,
                draw=draw,
            ):
                # Stop at the first biggest size that fits.
                best_font_size = candidate_font_size
                last_one_fits = True
                best_size = candidate_size

                break

            if candidate_font_size < min_font_size:
                # Could not fit at all :(
                best_font_size = candidate_font_size
                last_one_fits = False
                best_size = candidate_size

                break
            else:
                best_font_size -= 1

        best_font_size = max(min_font_size, best_font_size)

        # best_size is used to center the text.
        return last_one_fits, best_font_size

    def iterate_over_boxes(self, s_bboxes, texts):
        items = []

        i = 0
        for s_bbox in s_bboxes:
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

            item = (s_bb, text)
            items.append(item)

            i += 1

        # Sort such that longest texts come first.
        sorted_items = sorted(items, key=lambda x: len(x[1]), reverse=True)
        for s in sorted_items:
            yield s

    def attempt_actions(
        self, did_succeed, populated_box, other_boxes, text, img, min_font_size, draw
    ):
        new_populated_box, did_succeed, new_other_boxes = (
            populated_box,
            did_succeed,
            other_boxes,
        )

        if not did_succeed:
            (
                new_populated_box,
                did_succeed,
                new_other_boxes,
            ) = MoveToRight.attempt(
                box=populated_box,
                other_boxes=copy.deepcopy(other_boxes),
                text=text,
                img=img,
                min_font_size=min_font_size,
                draw=draw,
            )

        if not did_succeed:
            (
                new_populated_box,
                did_succeed,
                new_other_boxes,
            ) = MoveToLeft.attempt(
                box=populated_box,
                other_boxes=copy.deepcopy(other_boxes),
                text=text,
                img=img,
                min_font_size=min_font_size,
                draw=draw,
            )

        if not did_succeed:
            (
                new_populated_box,
                did_succeed,
                new_other_boxes,
            ) = MoveAndPushToRight.attempt(
                box=populated_box,
                other_boxes=copy.deepcopy(other_boxes),
                text=text,
                img=img,
                min_font_size=min_font_size,
                draw=draw,
            )

        if not did_succeed:
            (
                new_populated_box,
                did_succeed,
                new_other_boxes,
            ) = MoveAndPushToLeft.attempt(
                box=populated_box,
                other_boxes=copy.deepcopy(other_boxes),
                text=text,
                img=img,
                min_font_size=min_font_size,
                draw=draw,
            )

        if not did_succeed:
            new_populated_box, did_succeed, new_other_boxes = MoveToUp.attempt(
                box=populated_box,
                other_boxes=copy.deepcopy(other_boxes),
                text=text,
                img=img,
                min_font_size=min_font_size,
                draw=draw,
            )

        if not did_succeed:
            (
                new_populated_box,
                did_succeed,
                new_other_boxes,
            ) = MoveToDown.attempt(
                box=populated_box,
                other_boxes=copy.deepcopy(other_boxes),
                text=text,
                img=img,
                min_font_size=min_font_size,
                draw=draw,
            )

        return new_populated_box, did_succeed, new_other_boxes

    def declutter_font_size(
        self,
        bboxes,
        texts: List[str],
        min_font_size: int,
        max_font_size: int,
        img,
        draw,
    ):
        best_font_size = max_font_size

        # First get the smallest font size that is acceptable for the text boxes.
        for unpopulated_speechbox, text in self.iterate_over_boxes(
            bboxes,
            texts,
        ):
            (
                text_will_fit,
                best_font_size,  # Set here!
            ) = self.compute_font_metrics(
                unpopulated_speechbox,
                text,
                best_font_size,
                min_font_size=min_font_size,
                draw=draw,
            )

        def _compute_text_area(font_size):
            total_text_area = 0
            for unpopulated_speechbox, text in self.iterate_over_boxes(bboxes, texts):
                b = unpopulated_speechbox
                populated_box = MagicBox(b[0], b[1], b[2], b[3], text)

                box = populated_box.get_text_box(font_size, "center", draw, text)

                width = box[2] - box[0]
                height = box[3] - box[1]
                total_text_area += width * height

            return total_text_area

        # Then cut it down even further! (if the text is too cluttered)
        image_area = img.width * img.height
        total_text_area = _compute_text_area(best_font_size)
        while (
            total_text_area / image_area
        ) >= CLUTTER_THRESHOLD and best_font_size > 1:
            #print(
                #f"Text cluttered! ({total_text_area / image_area}) - cutting down font size."
            #)

            best_font_size = max(1, int(best_font_size * 0.8))
            total_text_area = _compute_text_area(best_font_size)

        #print(
            #f"Done decluttering text! TextArea=({total_text_area / image_area}) FontSize={best_font_size}"
        #)

        # best_font_size is used to draw the texts later on in case one of the texts is smaller than the others before it.
        return best_font_size

    def get_text_details(
        self,
        s_bboxes,
        texts: List[str],
        min_font_size,
        img,
        draw,
    ):
        text_details = []

        other_boxes = []
        other_boxes_metadata = []  # Currently only used for last ditch checking.

        for unpopulated_speechbox, text in self.iterate_over_boxes(s_bboxes, texts):
            b = unpopulated_speechbox
            populated_box = MagicBox(b[0], b[1], b[2], b[3], text)

            # Try expanding the boxes.
            if not box_aspect_good(populated_box):
                (
                    new_populated_box,
                    did_succeed_expanding,
                    new_other_boxes,
                ) = ExpandAspectAction(action_name="Expand Aspect").attempt(
                    box=populated_box,
                    other_boxes=other_boxes,
                    text=text,
                    img=img,
                    min_font_size=min_font_size,
                    draw=draw,
                )

                if did_succeed_expanding:
                    populated_box, other_boxes = new_populated_box, new_other_boxes

            did_succeed = not box_is_bad(
                min_font_size, text, populated_box, "center", draw, img, other_boxes
            )
            #if did_succeed:
                #print(f'Box "{text}" IS VALID. No further actions being performed.')
            #else:
                #print(f'Box "{text}" IS BAD. Actions will be performed.')

            proceeding_to_later_steps = not did_succeed

            # Each action here can repeat itself for a number of times. Ultimately, actions can have two outcomes:
            # (SUCCEED(changes made!), FAILED(no changes))

            new_populated_box, did_succeed, new_other_boxes = self.attempt_actions(
                did_succeed=did_succeed,
                populated_box=populated_box,
                other_boxes=other_boxes,
                text=text,
                img=img,
                min_font_size=min_font_size,
                draw=draw,
            )

            using_last_ditch_font_size = not did_succeed
            if not did_succeed:
                #print(f'Box "{text}" is going for a last ditch run!')
                # Last ditch effort!
                populated_box.can_change_font_size = True

                new_populated_box, did_succeed, new_other_boxes = self.attempt_actions(
                    did_succeed=did_succeed,
                    populated_box=populated_box,
                    other_boxes=other_boxes,
                    text=text,
                    img=img,
                    min_font_size=calc_last_ditch_font_size(min_font_size),
                    draw=draw,
                )

            if did_succeed and proceeding_to_later_steps:
                populated_box, other_boxes = new_populated_box, new_other_boxes

            new_sbb = populated_box

            # Try to horizontally recenter the box again afterwards.
            new_sbb = recenter_box(
                min_font_size, text, new_sbb, "center", draw, img, other_boxes
            )

            # If we're using text_overlap instead of text_overflow, the text may overlap the containing boxes, but we don't want other texts to overlap with texts too!
            other_boxes.append(new_sbb)
            other_boxes_metadata.append(
                {
                    "using_last_ditch_font_size": using_last_ditch_font_size,
                    "original_speech_box": unpopulated_speechbox,
                }
            )

        for new_sbb, sbb_metadata in zip(other_boxes, other_boxes_metadata):
            left = floor(new_sbb[0])
            top = floor(new_sbb[1])
            width = get_box_width(new_sbb)
            height = get_box_height(new_sbb)
            text = new_sbb[4]

            best_width, best_height = compute_font_region(
                min_font_size, box_width=width, text=text, draw=draw
            )

            offset_top = max((height - best_height) // 2, 0)
            offset_left = max((width - best_width) // 2, 0)
            # offset_top = offset_left = 0

            font = load_font(min_font_size)

            max_chars_per_line = compute_max_chars_per_line(font, width)
            wrapped_text = wrap_text(text, max_chars_per_line)
            text_details.append(
                [
                    wrapped_text,
                    left + offset_left,
                    top + offset_top,
                    "center",
                    new_sbb,  # For debugging.
                    sbb_metadata["using_last_ditch_font_size"],
                    sbb_metadata["original_speech_box"],
                ]
            )

        return text_details

    def draw_details(self, text_details, best_font_size, draw, image, text_colors):
        for idx, td in enumerate(text_details):
            td_is_using_last_ditch_font_size = td[-2]

            # td = A list containing [wrappedtextstring, leftinteger, topinteger] among others.
            if td_is_using_last_ditch_font_size:
                font = load_font(calc_last_ditch_font_size(best_font_size))
            else:
                font = load_font(best_font_size)

            print(
                f"Drawing SBB: {td[-3]} with True X1,Y1 == {(td[1], td[2])} IsUsingLastDitch == {td_is_using_last_ditch_font_size} BFS={best_font_size}"
            )

            draw.multiline_text(
                (td[1], td[2]),
                td[0],
                self.get_text_color(text_colors, idx),
                font,
                align="center",
                stroke_fill=self.get_stroke_color(text_colors, idx),
                stroke_width=compute_stroke_size(best_font_size),
                spacing=get_vertical_spacing(best_font_size),
            )

    def process(self, image, bboxes, target_texts, text_colors):
        new_image = image.copy()
        if len(bboxes) == 0:
            return new_image

        draw = ImageDraw.Draw(new_image)
        # draw.fontmode = "L"
        draw.fontmode = "1"

        min_font_size, max_font_size = compute_min_max_font_sizes(
            new_image.width, new_image.height
        )

        # Step -1
        best_font_size = self.declutter_font_size(
            bboxes,
            target_texts,
            min_font_size=min_font_size,
            max_font_size=max_font_size,
            img=new_image,
            draw=draw,
        )

        # Step 0 to end.
        text_details = self.get_text_details(
            bboxes,
            target_texts,
            min_font_size=best_font_size,
            img=new_image,
            draw=draw,
        )

        self.draw_details(
            text_details,
            best_font_size,
            draw=draw,
            image=new_image,
            text_colors=text_colors,
        )

        return new_image
