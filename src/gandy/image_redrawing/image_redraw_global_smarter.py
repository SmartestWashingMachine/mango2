from gandy.full_pipelines.base_app import BaseApp
from gandy.utils.speech_bubble import SpeechBubble
from gandy.image_redrawing.base_image_redraw import BaseImageRedraw
from PIL import Image, ImageDraw
from typing import List, Union
from gandy.image_redrawing.smarter.checks import text_intersects, text_intersects_on_direction, text_overflows
from gandy.image_redrawing.smarter.text_box import TextBox, FONT_MANAGER
from gandy.image_redrawing.smarter.policy import MoveAction
from gandy.image_redrawing.smarter.image_fonts import compute_min_max_font_sizes, compute_stroke_size, get_vertical_spacing, print_spam
from gandy.image_redrawing.smarter.declutter_font_size import declutter_font_size
from gandy.image_redrawing.smarter.recentering_boxes import try_center_boxes
from gandy.state.debug_state import debug_state
from gandy.state.config_state import config_state
import json
from gandy.utils.fancy_logger import logger

"""

--- Step 0:

Compute a minimum and maximum possible font size, based on the image size.

--- Step 1:

Derive a single constant font size from the minimum and maximum font sizes, based on the amount of text in the image.

The more text in the image, the smaller the font size.

--- Step 2:

We iterate over each and every box, and IF the text intersects with other texts OR overflows the image:
  We run through a set of actions, looking for possible actions that makes the box viable.

  Each action can move or expand the box itself. Each action can also move (but not expand) OTHER boxes.
  Some actions are "stackable". When the box itself is mutated via a stackable action, and if it fails, the mutated box is kept.


WHAT ARE ACTIONS?

Actions mutate the selected box and possibly even other boxes.

Actions can be in several different states:

PROG (VAR timeLeft) -> The default state. The action is processed here.
  After processing, go to VALID (timeLeft).

VALID (VAR timeLeft) -> Validate the results of PROG.
  If a NON-FATAL error is found AND there is time left, go back to PROG (timeLeft - 1).
  If a FATAL error is found, go to FAIL.
  If no errors are found, go to SUCCESS.
  If there is no time left, also go to FAIL.

FAIL -> Triggered on a fatal error or when no time is left. The action will stop processing and if the action is not stackable, any mutations on the box will be lost.

SUCCESS -> Return the results!

~~~~~

WHAT ARE OUR ACTIONS?

For now, it'll be:

Expanding Aspect Ratio (stackable)
Move Left
Move Right
Move Up
Move Down

Move/Push for the same directions

And: Repeat previous non-stackable ones but with the current candidate having a much smaller font size.

~~~~~

WHAT IS A BOX?

A box, not to be confused with a SpeechBubble, is a set of coordinates that tightly wraps the text, if it were to be drawn on the image.

"""
def _midp(x: TextBox):
    return ((x.x1 + x.x2) / 2, (x.y1 + x.y2) / 2)

class CacheDraw():
    def __init__(self, draw) -> None:
        self.cache = {}
        self.draw = draw

    def do_draw(self, coords, text: str, font, align: str, stroke_width, spacing, item):
        drawn = self.draw.multiline_textbbox(coords, text, font, align=align, stroke_width=stroke_width, spacing=spacing)
        self.cache[item] = { 'coords': coords, 'drawn': drawn, }

        return drawn

    def multiline_textbbox(self, coords, text: str, font, align: str, stroke_width, spacing):
        #x_space = coords[2] - coords[0]
        #y_space = coords[3] - coords[1]
        #item = f'{x_space}_{y_space}_{text}_{font.size}_{align}_{stroke_width}_{spacing}'

        item = f'{text}_{font.size}_{align}_{stroke_width}_{spacing}'
        existing_item = self.cache.get(item, None)

        if existing_item is None:
            # First time this item was seen.
            return self.do_draw(coords, text, font, align, stroke_width, spacing, item)

        return [
            coords[0] + (existing_item['drawn'][0] - existing_item['coords'][0]),
            coords[1] + (existing_item['drawn'][1] - existing_item['coords'][1]),
            coords[0] + (existing_item['drawn'][2] - existing_item['drawn'][0]),
            coords[1] + (existing_item['drawn'][3] - existing_item['drawn'][1]),
        ]


SCALE_FACTOR = 4 # Scale image up then down for sharper looking texts. Ridiculous, isn't it? Thanks PIL...

def upscale_items(image: Image.Image, bboxes):
    mapped_bboxes = [[b[0] * SCALE_FACTOR, b[1] * SCALE_FACTOR, b[2] * SCALE_FACTOR, b[3] * SCALE_FACTOR] for b in bboxes]

    up_image = image.resize((int(image.width * SCALE_FACTOR), int(image.height * SCALE_FACTOR)), resample=Image.LANCZOS)
    up_image.tile_width = int(up_image.width * SCALE_FACTOR)
    up_image.tile_height = int(up_image.height * SCALE_FACTOR)

    return up_image, mapped_bboxes

def downscale_items(image: Image.Image):
    # By the point we downscale we don't care for the tile sizes anymore.
    return image.resize((int(image.width // SCALE_FACTOR), int(image.height // SCALE_FACTOR)), resample=Image.LANCZOS)

class ImageRedrawGlobalSmarter(BaseImageRedraw):
    def __init__(self, actions: List[MoveAction]):
        super().__init__()

        self.actions = actions

    def box_is_bad(self, box: TextBox, others: List[TextBox], img: Image.Image, return_reason = False):
        if text_intersects(box, others):
            if return_reason:
                return True, "intersects"
            return True
        if text_overflows(box, img):
            if return_reason:
                return True, "overflows"
            return True

        if return_reason:
            return False, ""
        return False

    def better_box(self, box: TextBox, others: List[TextBox], img: Image.Image):
        next_action_idx = 0

        box_is_bad = self.box_is_bad(box, others, img)

        for next_action_idx in range(len(self.actions)):
            cur_action = self.actions[next_action_idx]
            if box_is_bad or (cur_action.stackable and not cur_action.only_on_failure):
                box, others, did_succeed = cur_action.begin(candidate=box, others=others, img=img)

                box_is_bad = self.box_is_bad(box, others, img)

        return box, others
    


    def redraw_from_tboxes(self, image: Image.Image, draw: ImageDraw.ImageDraw, text_boxes: List[TextBox], text_colors):
        # picked_font_size = text_boxes[0].font_size if len(text_boxes) > 0 else 1

        for idx, tb in enumerate(text_boxes):
            font = FONT_MANAGER.get_font(tb.font_size)

            draw.multiline_text(
                (tb.x1, tb.y1),
                tb.text,
                self.get_text_color(text_colors, idx),
                font,
                align="center",
                stroke_fill=self.get_stroke_color(text_colors, idx),
                stroke_width=compute_stroke_size(tb.font_size),
                spacing=get_vertical_spacing(tb.font_size),
            )

        return image

    def process(
        self,
        image: Image.Image,
        bboxes: List[SpeechBubble],
        target_texts: List[str],
        text_colors: List[str],
    ):
        with logger.begin_event("Copy image"):
            if debug_state.debug or debug_state.debug_redraw:
                self.save_recording(image, bboxes, target_texts, text_colors)
            # Initialize the TextBoxes and other vars.

            original_image_width = image.width
            original_image_height = image.height
            if original_image_width < 10000 and original_image_height < 10000:
                new_image = image.copy().convert('RGB')
            else:
                new_image = image.convert('RGB')

        with logger.begin_event("Upscale image"):
            # We might be tiling the image (e.g: a long vertical comic),
            # in which case we want to shift the boxes by the size of a TILE, rather than the entire large IMAGE size.
            new_image.tile_width = int(new_image.width * (config_state.tile_width / 100))
            new_image.tile_height = int(new_image.height * (config_state.tile_height / 100))

            if original_image_width < 10000 and original_image_height < 10000:
                new_image, bboxes = upscale_items(new_image, bboxes) # Tile sizes are changed here too accordingly.

        draw = ImageDraw.Draw(new_image)
        draw.fontmode = "L"

        def _make_metadata(bb: SpeechBubble, t: str):
            return {
                'bb': bb,
                't': t,
            }

        with logger.begin_event("Compute font size"):
            cached_draw = CacheDraw(draw=draw)
            container_boxes = [TextBox.from_speech_bubble(bb, t, font_size=-1, draw=cached_draw, img=new_image, container='make', metadata={}) for (bb, t) in zip(bboxes, target_texts)]
            text_boxes = [TextBox.from_speech_bubble(bb, t, font_size=-1, draw=cached_draw, img=new_image, container='make', metadata=_make_metadata(bb, t)) for (bb, t) in zip(bboxes, target_texts)]

            # Get the acceptable font size range.
            min_font_size, max_font_size = compute_min_max_font_sizes(new_image)

            # Then pick a font size.
            # The font size is set in each text box inside this method.
            # Actually... Only the max font size is used to account for in this method.
            picked_font_size = declutter_font_size(text_boxes, min_font_size, max_font_size, new_image, container_boxes)
            for idx, b in enumerate(text_boxes):
                # container_boxes is used to compute the X and Y offsets to center the box.
                # container_text_boxes is used to determine if the text box is nearby the original detection area.
                # the metadata here is used for recentering the box after all actions are performed on all boxes.
                b.metadata['container_text_box'] = TextBox.from_speech_bubble(b.metadata['bb'], b.metadata['t'], font_size=picked_font_size, draw=draw, img=new_image, container='make', metadata={})
                b.metadata['container_box'] = container_boxes[idx]

        with logger.begin_event("Compute box positions"):
            top_right_corner = (new_image.width, 0)
            def _dist(p1, p2):
                return (((p1[0] - p2[0]) ** 2) + (p1[1] - p2[1]) ** 2) ** 0.5

            text_boxes = sorted(text_boxes, key=lambda x: _dist(top_right_corner, _midp(x)), reverse=True)

            # For every invalid box, use actions to attempt to make it valid.
            for idx in range(len(text_boxes)):
                cur_box = text_boxes[idx]
                others = text_boxes[:idx] + text_boxes[(idx + 1):]

                better_box, other_boxes = self.better_box(cur_box, others, new_image)
                # text_boxes[idx] = better_box

                text_boxes = [better_box] + other_boxes

            text_boxes = try_center_boxes(new_image, text_boxes)
            text_boxes = try_center_boxes(new_image, text_boxes) # Center again! (As some of the next boxes need to be centered first)

        # Actually draw the text on the image.
        with logger.begin_event("Draw text"):
            self.redraw_from_tboxes(new_image, draw, text_boxes, text_colors)

        print_spam('Drawn Boxes:')
        print_spam(text_boxes)

        with logger.begin_event("Downscale image", original_size=[original_image_width, original_image_height], cur_size=new_image.size):
            if original_image_width < 10000 and original_image_height < 10000:
                new_image = downscale_items(new_image)
        return new_image

    def save_recording(self, image, bboxes, target_texts, text_colors):
        import uuid
        import os

        did = uuid.uuid4().hex
        os.makedirs(f'./debugdumps/smartredraw/{did}', exist_ok=True)

        # Save and load with same extension; lest bit depth be different, causing differing font sizing.
        image.save(f'./debugdumps/smartredraw/{did}/{debug_state.metadata["cur_img_name"]}.png')

        data = { 'bboxes': bboxes, 'target_texts': target_texts, 'text_colors': text_colors, }
        with open(f'./debugdumps/smartredraw/{did}/data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f)

    def run_recording(self, did: str):
        from glob import glob

        img_path = glob(f'./debugdumps/smartredraw/{did}/*.png')[0]
        image = Image.open(img_path)

        with open(f'./debugdumps/smartredraw/{did}/data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

        return self.process(image, data['bboxes'], data['target_texts'], data['text_colors'])