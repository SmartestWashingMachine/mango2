from gandy.utils.speech_bubble import SpeechBubble
from gandy.image_redrawing.base_image_redraw import BaseImageRedraw
from PIL import Image, ImageDraw
from typing import List, Union
from gandy.image_redrawing.physics.manipulate_layout import manipulate_layout
from gandy.image_redrawing.physics.compute_global_font_size import compute_global_font_size
from gandy.image_redrawing.physics.text_block import TextBlock
from gandy.image_redrawing.physics.draw_manager import DrawManager
from gandy.image_redrawing.physics.font_manager import FONT_MANAGER
from gandy.state.debug_state import debug_state
from gandy.state.config_state import config_state
import json
from gandy.utils.fancy_logger import logger
import uuid

SCALE_FACTOR = 4 # Scale image up then down for sharper looking texts. Ridiculous, isn't it? Thanks PIL...

def create_upscaled_text_canvas(image: Image.Image, bboxes):
    mapped_bboxes = [[b[0] * SCALE_FACTOR, b[1] * SCALE_FACTOR, b[2] * SCALE_FACTOR, b[3] * SCALE_FACTOR] for b in bboxes]

    up_image = Image.new('RGBA', (int(image.width * SCALE_FACTOR), int(image.height * SCALE_FACTOR)), (255, 255, 255, 0))
    up_image.tile_width = int(up_image.width * SCALE_FACTOR)
    up_image.tile_height = int(up_image.height * SCALE_FACTOR)

    return up_image, mapped_bboxes

def create_text_canvas(image: Image.Image):
    text_canvas = Image.new('RGBA', (image.width, image.height), (255, 255, 255, 0))

    # We might be tiling the image (e.g: a long vertical comic),
    # in which case we want to shift the boxes by the size of a TILE, rather than the entire large IMAGE size.
    text_canvas.tile_width = int(image.width * (config_state.tile_width / 100))
    text_canvas.tile_height = int(image.height * (config_state.tile_height / 100))

    return text_canvas

def downscale_text_canvas(image: Image.Image):
    # By the point we downscale we don't care for the tile sizes anymore.
    return image.resize((int(image.width // SCALE_FACTOR), int(image.height // SCALE_FACTOR)), resample=Image.BILINEAR)

class ImageRedrawPhysics(BaseImageRedraw):
    def __init__(self):
        super().__init__()

    def uppercase_text(self, text: str):
        return text.upper()

    def get_text_color(
        self, text_colors: Union[List[str], None], idx, default_color="black"
    ):
        return text_colors[idx] if text_colors is not None else default_color

    def get_stroke_color(self, text_colors: Union[List[str], None], idx):
        if text_colors is not None:
            if text_colors[idx] == "white":
                return "black"  # #000
            else:
                return "white"

        return "white"

    def save_recording(self, image, bboxes, target_texts, text_colors):
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
    
    def redraw_from_blocks(self, image: Image.Image, draw_manager: DrawManager, text_boxes: List[TextBlock], text_colors):
        for idx, tb in enumerate(text_boxes):
            font = FONT_MANAGER.get_font(tb.font_size)

            draw_manager.draw.multiline_text(
                (tb.final_bbox[0], tb.final_bbox[1]),
                tb.wrapped_lines,
                self.get_text_color(text_colors, idx),
                font,
                align="center",
                stroke_fill=self.get_stroke_color(text_colors, idx),
                stroke_width=draw_manager.compute_stroke_size(tb.font_size),
                spacing=draw_manager.get_vertical_spacing(tb.font_size),
            )

        return image

    def process(
        self,
        image: Image.Image,
        bboxes: List[SpeechBubble],
        target_texts: List[str],
        text_colors: List[str],
    ):
        original_image_width = image.width
        original_image_height = image.height
        should_upscale = False and original_image_width < 10000 and original_image_height < 10000

        with logger.begin_event("Copy image"):
            if debug_state.debug or debug_state.debug_redraw:
                self.save_recording(image, bboxes, target_texts, text_colors)

        with logger.begin_event("Create upscaled text canvas"):
            if should_upscale:
                text_canvas, bboxes = create_upscaled_text_canvas(image, bboxes) # Tile sizes are changed here too accordingly.
            else:
                text_canvas = create_text_canvas(image)

        blocks = []
        for bb, target_text in zip(bboxes, target_texts):
            bl_id = uuid.uuid4().hex
            bl = TextBlock(
                uuid=bl_id,
                translated_text=target_text,
                original_bbox=bb,
                final_bbox=None, # Initialized later on.
                font_size=None,
                wrapped_lines=None,
                mass=None,
                anchor_point=None,
                displacement=None,
            )
            blocks.append(bl)

        draw = ImageDraw.Draw(text_canvas)
        draw.fontmode = "L"
        draw_manager = DrawManager(draw)

        compute_global_font_size(blocks, draw_manager, text_canvas)

        manipulate_layout(blocks, text_canvas)

        with logger.begin_event("Downscale text canvas", original_size=[original_image_width, original_image_height], cur_size=text_canvas.size):
            if should_upscale:
                text_canvas = downscale_text_canvas(text_canvas)

        with logger.begin_event("Drawing on text canvas"):
            text_canvas = self.redraw_from_blocks(text_canvas, draw_manager, blocks, text_colors)

        with logger.begin_event("Paste text canvas onto image"):
            new_image = Image.alpha_composite(image.convert('RGBA'), text_canvas)

        return new_image

    def unload_model(self):
        super().unload_model()
