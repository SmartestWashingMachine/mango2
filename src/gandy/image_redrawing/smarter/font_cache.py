from PIL import ImageFont
from typing import Dict, List
from string import ascii_letters

def load_font(font_size):
    font = ImageFont.truetype("resources/fonts/font.otf", font_size, encoding="unic")
    return font

class FontManager():
    def __init__(self):
        self.font = None
        self.font_size = None

        self.char_size_map: Dict[int, Dict[str, int]] = {}

    def get_font(self, font_size: int):
        if font_size == self.font_size and self.font is not None:
            return self.font

        self.font = load_font(font_size)
        self.font_size = font_size

        self.char_size_map[self.font_size] = self.char_size_map.get(self.font_size, {})

        return self.font
    
    def _get_size_of_char(self, s: str, font_size: int):
        size_map = self.char_size_map[font_size]

        if s not in size_map:
            # Compute and add to cache.
            self.char_size_map[font_size][s] = self.font.getsize(s)[0]

        # Return from cache.
        return self.char_size_map[font_size][s]
    
    def compute_max_chars_per_line(self, font_size: int, box_width: float):
        """
        Calculate the max number of characters that can fit in a single line for a speech bubble.
        """
        avg_char_width = sum((self._get_size_of_char(char, font_size)) for char in ascii_letters) / len(
            ascii_letters
        )

        candidate_max_char_count = max(
            1, int(box_width / avg_char_width)
        )  # Max true chars before it overflows the width. AKA chars per line.

        return candidate_max_char_count
    
FONT_MANAGER = FontManager()
