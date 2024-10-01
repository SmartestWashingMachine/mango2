from typing import List
from PIL import ImageDraw, Image
from gandy.image_redrawing.smarter.image_fonts import load_font, compute_stroke_size, get_vertical_spacing, compute_max_chars_per_line, wrap_text

def _v_add(v: float, pct: float, img_side: int):
    if pct == 0:
        return v        
    return v + (img_side * pct)

class TextBox():
    def __init__(self, x1: float, y1: float, x2: float, y2: float, text: str, font_size: int, draw: ImageDraw.ImageDraw, img: Image.Image) -> None:
        self.img = img
        self.draw = draw

        self.container_x1 = x1
        self.container_y1 = y1
        self.container_x2 = x2
        self.container_y2 = y2
        self.font_size = font_size
        self.text = text
        self.original_text = text

        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

        #self.x_add = (self.x2 - self.x1) // 2
        #self.y_add = (self.y2 - self.y1) // 2

        if self.font_size != -1:
            self.recompute()

    def recompute(self):
        font = load_font(self.font_size)

        max_chars_per_line = compute_max_chars_per_line(font, self.get_width())
        wrapped_text = wrap_text(self.original_text, max_chars_per_line)

        self.x_add = 0
        self.y_add = 0
        #self.x_add = (self.x2 - self.x1) // 2
        #self.y_add = (self.y2 - self.y1) // 2

        bbox = self.draw.multiline_textbbox(
            #(self.x1, self.y1), # NVM: "Draw" at origin so we can easily calculate width and height (A - 0 == 0).
            (self.x1 + self.x_add, self.y1 + self.y_add),
            wrapped_text,
            font,
            align="center",
            stroke_width=compute_stroke_size(self.font_size),
            spacing=get_vertical_spacing(self.font_size),
        )

        self._bbox = bbox

        #When drawing, the point of origin changes -_-
        #self.x1 = bbox[0]
        #self.y1 = bbox[1]
        self.x2 = bbox[2]# - bbox[0] + self.x1
        self.y2 = bbox[3]# - bbox[1] + self.y1
        self.text = wrapped_text

    def get_with_margin(self):
        # NOTE: Only use this for text_intersects_on_direction - it can make the box smaller than it actually is.

        CLOSE_FACTOR = 0.002
        # image is only used here for margin calculation.
        mx = self.img.width * CLOSE_FACTOR
        my = self.img.height * CLOSE_FACTOR

        new_x1 = max(self.x1 - mx, 0)
        new_y1 = max(self.y1 - my, 0)

        # X2 and Y2 might be greater than the image size.
        new_x2 = min(self.x2 + mx, self.img.width)
        new_y2 = min(self.y2 + my, self.img.height)
        return TextBox(new_x1, new_y1, new_x2, new_y2, text=self.text, font_size=self.font_size, draw=self.draw, img=self.img)

    def get_width(self):
        return self.x2 - self.x1
    
    def get_height(self):
        return self.y2 - self.y1

    def get_area(self):
        return self.get_width() * self.get_height()
    
    def set_font_size(self, fz: int):
        self.font_size = fz
        self.recompute()

    @classmethod
    def shift_from(cls, candidate, offset_pct: List[float], is_abs = False):
        iwid = candidate.img.width
        ihei = candidate.img.height

        if is_abs:
            coords = [candidate.x1 + offset_pct[0], candidate.y1 + offset_pct[1], candidate.x2 + offset_pct[2], candidate.y2 + offset_pct[3]]
        else:
            coords = [_v_add(candidate.x1, offset_pct[0], iwid), _v_add(candidate.y1, offset_pct[1], ihei), _v_add(candidate.x2, offset_pct[2], iwid), _v_add(candidate.y2, offset_pct[3], ihei)]

        return cls.from_speech_bubble(
            coords,
            text=candidate.text,
            font_size=candidate.font_size,
            draw=candidate.draw,
            img=candidate.img,
            #**candidate.__dict__,
        )
    
    @classmethod
    def clone(cls, candidate):
        return cls.shift_from(candidate, [0, 0, 0, 0])

    @classmethod
    def from_speech_bubble(cls, bb, text: str, font_size: int, draw: ImageDraw.ImageDraw, img: Image.Image):
        return cls(
            x1=bb[0],
            y1=bb[1],
            x2=bb[2],
            y2=bb[3],
            text=text,
            font_size=font_size,
            draw=draw,
            img=img,
        )
    
    def __repr__(self) -> str:
        return f'TextBox: {[int(self.x1), int(self.y1), int(self.x2), int(self.y2)]} || "{self.simple()}"'
    
    def simple(self):
        return self.text[:10].replace('\\n', ' ').replace('\n', ' ').strip()