from PIL import ImageDraw
from gandy.state.config_state import config_state
from gandy.image_redrawing.physics.font_manager import FONT_MANAGER

class DrawManager():
    def __init__(self, draw: ImageDraw.ImageDraw):
        self.draw = draw

    def compute_stroke_size(self, font_size: int):
        min_stroke_size = 1

        comp = round(font_size * (config_state.stroke_size / 8))

        return max(min_stroke_size, comp)

    def get_vertical_spacing(self, font_size: int):
        return 3 - self.compute_stroke_size(font_size)

    def bbox_from_wrapped_text(self, wrapped_text: str, font_size: int):
        bbox = self.draw.multiline_textbbox(
            # "Draw" at origin so we can easily calculate width and height (A - 0 == 0).
            (0, 0),
            wrapped_text,
            FONT_MANAGER.get_font(font_size),
            align="center",
            stroke_width=self.compute_stroke_size(font_size),
            spacing=self.get_vertical_spacing(font_size),
        )

        # center_on_point() is called later on to actually move the bbox.
        return bbox
