from gandy.full_pipelines.base_app import BaseApp
from gandy.utils.speech_bubble import SpeechBubble
from gandy.image_redrawing.base_image_redraw import BaseImageRedraw
from PIL import Image, ImageDraw
from typing import List, Union
from gandy.image_redrawing.smarter.checks import text_intersects, text_intersects_on_direction, text_overflows
from gandy.image_redrawing.smarter.text_box import TextBox
from gandy.image_redrawing.smarter.actions.move_action import MoveAction
from gandy.image_redrawing.smarter.actions.move_push_action import MoveAndPushAction
from gandy.image_redrawing.smarter.actions.expand_aspect_action import ExpandAspectAction
from gandy.image_redrawing.smarter.image_fonts import compute_min_max_font_sizes, compute_stroke_size, get_vertical_spacing, load_font
from gandy.image_redrawing.smarter.declutter_font_size import declutter_font_size
from gandy.state.debug_state import debug_state
import json

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

SCALE_FACTOR = 4 # Scale image up then down for sharper looking texts. Ridiculous, isn't it? Thanks PIL...

def upscale_items(image: Image.Image, bboxes):
    mapped_bboxes = [[b[0] * SCALE_FACTOR, b[1] * SCALE_FACTOR, b[2] * SCALE_FACTOR, b[3] * SCALE_FACTOR] for b in bboxes]

    return image.resize((int(image.width * SCALE_FACTOR), int(image.height * SCALE_FACTOR)), resample=Image.LANCZOS), mapped_bboxes

def downscale_items(image: Image.Image):
    return image.resize((int(image.width // SCALE_FACTOR), int(image.height // SCALE_FACTOR)), resample=Image.LANCZOS)

MOVE_PCT = 0.01

ACTIONS: List[MoveAction] = [
    # Stackables.
    ExpandAspectAction(stackable=True),
    # Only move.
    MoveAction(offset_pct=[MOVE_PCT, 0, 0, 0], fatal_error_overlapping_direction="l", action_name="MoveRight"),
    MoveAction(offset_pct=[-MOVE_PCT, 0, 0, 0], fatal_error_overlapping_direction="r", action_name="MoveLeft"),
    MoveAction(offset_pct=[0, MOVE_PCT, 0, 0], fatal_error_overlapping_direction="u", action_name="MoveDown"),
    MoveAction(offset_pct=[0, -MOVE_PCT, 0, 0], fatal_error_overlapping_direction="d", action_name="MoveUp"),
    # Move and push.
    MoveAndPushAction(offset_pct=[MOVE_PCT, 0, 0, 0], fatal_error_overlapping_direction="l", action_name="PushRight"),
    MoveAndPushAction(offset_pct=[-MOVE_PCT, 0, 0, 0], fatal_error_overlapping_direction="r", action_name="PushLeft"),
    MoveAndPushAction(offset_pct=[0, MOVE_PCT, 0, 0], fatal_error_overlapping_direction="u", action_name="PushDown"),
    MoveAndPushAction(offset_pct=[0, -MOVE_PCT, 0, 0], fatal_error_overlapping_direction="d", action_name="PushUp"),
    # Diagonal move and move+push.
    MoveAction(offset_pct=[MOVE_PCT, MOVE_PCT, 0, 0], fatal_error_overlapping_direction="lu", action_name="MoveDownRight"),
    #MoveAction(offset_pct=[MOVE_PCT * 0.2, MOVE_PCT * 3, 0, 0], fatal_error_overlapping_direction="lu", action_name="MoveDownRightExtended"),
    MoveAndPushAction(offset_pct=[MOVE_PCT, MOVE_PCT, 0, 0], fatal_error_overlapping_direction="lu", action_name="PushMoveDownRight"),
    #MoveAction(offset_pct=[-MOVE_PCT * 0.2, MOVE_PCT * 3, 0, 0], fatal_error_overlapping_direction="ru", action_name="MoveDownLeftExtended"),
    MoveAction(offset_pct=[-MOVE_PCT, MOVE_PCT, 0, 0], fatal_error_overlapping_direction="ru", action_name="MoveDownLeft"),
    MoveAndPushAction(offset_pct=[-MOVE_PCT, MOVE_PCT, 0, 0], fatal_error_overlapping_direction="ru", action_name="PushMoveDownLeft"),
]

class ImageRedrawGlobalSmarter(BaseImageRedraw):
    def __init__(self):
        super().__init__()

    def box_is_bad(self, box: TextBox, others: List[TextBox], img: Image.Image):
        if text_intersects(box, others):
            return True
        if text_overflows(box, img):
            return True
        
        return False

    def better_box(self, box: TextBox, others: List[TextBox], img: Image.Image):
        next_action_idx = 0

        while self.box_is_bad(box, others, img):
            if next_action_idx >= len(ACTIONS):
                break

            cur_action = ACTIONS[next_action_idx]
            box, others, did_succeed = cur_action.begin(time_left=30, candidate=box, others=others, img=img)

            next_action_idx += 1

        return box, others
    
    def try_center_boxes(self, image: Image.Image, text_boxes: List[TextBox], container_boxes: List[TextBox]):
        def _boxes_nearby(tb: TextBox, cb: TextBox):
            def _midp(x: TextBox):
                return ((x.x1 + x.x2) / 2, (x.y1 + x.y2) / 2)
            
            def _dist(p1, p2):
                return (((p1[0] - p2[0]) ** 2) + (p1[1] - p2[1]) ** 2) ** 0.5

            def _dist_1d(a, b):
                return abs(a - b)

            tb_mid = _midp(tb)
            cb_mid = _midp(cb)
            dist_thr = 0.25
            return _dist_1d(tb_mid[0], cb_mid[0]) <= (image.width * dist_thr) and _dist_1d(tb_mid[1], cb_mid[1]) <= (image.height * dist_thr)
            #return _dist(_midp(tb), _midp(cb)) <= DIST_THR

        new_boxes: List[TextBox] = []
        for idx in range(len(text_boxes)):
            tb = text_boxes[idx]

            others = text_boxes[:idx] + text_boxes[idx + 1:]
            # If the box wasn't moved too far from its original location, try to vertically center it.
            if _boxes_nearby(tb, container_boxes[idx]):
                x_add = max(0, (container_boxes[idx].get_width() - tb.get_width()) // 2)
                y_add = max(0, (container_boxes[idx].get_height() - tb.get_height()) // 2)
                #y_add = 0 

                centered_box = TextBox.shift_from(tb, offset_pct=[x_add, y_add, 0, 0], is_abs=True)
                if not self.box_is_bad(centered_box, others, image):
                    new_boxes.append(centered_box)
                else:
                    new_boxes.append(tb)
            else:
                new_boxes.append(tb)

        return new_boxes

    def redraw_from_tboxes(self, image: Image.Image, draw: ImageDraw.ImageDraw, text_boxes: List[TextBox], text_colors):
        picked_font_size = text_boxes[0].font_size if len(text_boxes) > 0 else 1

        font = load_font(picked_font_size)

        for idx, tb in enumerate(text_boxes):
            draw.multiline_text(
                (tb.x1, tb.y1),
                tb.text,
                self.get_text_color(text_colors, idx),
                font,
                align="center",
                stroke_fill=self.get_stroke_color(text_colors, idx),
                stroke_width=compute_stroke_size(picked_font_size),
                spacing=get_vertical_spacing(picked_font_size),
            )

        return image

    def process(
        self,
        image: Image.Image,
        bboxes: List[SpeechBubble],
        target_texts: List[str],
        text_colors: List[str],
    ):
        if debug_state.debug:
            self.save_recording(image, bboxes, target_texts, text_colors)
        # Initialize the TextBoxes and other vars.
        new_image = image.copy()

        new_image, bboxes = upscale_items(new_image, bboxes)

        draw = ImageDraw.Draw(new_image)
        draw.fontmode = "1"

        text_boxes = [TextBox.from_speech_bubble(bb, t, font_size=-1, draw=draw, img=new_image) for (bb, t) in zip(bboxes, target_texts)]

        # Get the acceptable font size range.
        min_font_size, max_font_size = compute_min_max_font_sizes(new_image)

        # Then pick a font size.
        # The font size is set in each text box inside this method.
        # Actually... Only the max font size is used to account for in this method.
        picked_font_size = declutter_font_size(text_boxes, min_font_size, max_font_size, new_image)

        # For every invalid box, use actions to attempt to make it valid.
        for idx in range(len(text_boxes)):
            cur_box = text_boxes[idx]
            others = text_boxes[:idx] + text_boxes[(idx + 1):]

            better_box, other_boxes = self.better_box(cur_box, others, new_image)
            # text_boxes[idx] = better_box

            text_boxes = [better_box] + other_boxes

        container_boxes = list(reversed([TextBox.from_speech_bubble(bb, t, font_size=-1, draw=draw, img=new_image) for (bb, t) in zip(bboxes, target_texts)]))
        text_boxes = self.try_center_boxes(new_image, text_boxes, container_boxes)

        # Actually draw the text on the image.
        self.redraw_from_tboxes(new_image, draw, text_boxes, text_colors)

        print('Drawn Boxes:')
        print(text_boxes)

        new_image = downscale_items(new_image)
        return new_image

    def save_recording(self, image, bboxes, target_texts, text_colors):
        import uuid
        import os

        did = uuid.uuid4().hex
        os.makedirs(f'./debugdumps/smartredraw/{did}', exist_ok=True)

        # Save and load with same extension; lest bit depth be different, causing differing font sizing.
        image.save(f'./debugdumps/smartredraw/{did}/image.png')

        data = { 'bboxes': bboxes, 'target_texts': target_texts, 'text_colors': text_colors, }
        with open(f'./debugdumps/smartredraw/{did}/data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f)

    def run_recording(self, did: str):
        image = Image.open(f'./debugdumps/smartredraw/{did}/image.png')

        with open(f'./debugdumps/smartredraw/{did}/data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

        return self.process(image, data['bboxes'], data['target_texts'], data['text_colors'])