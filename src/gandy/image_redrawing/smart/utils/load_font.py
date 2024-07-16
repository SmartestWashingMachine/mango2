from PIL import ImageFont


def load_font(font_size):
    font = ImageFont.truetype("resources/fonts/font.otf", font_size, encoding="unic")
    return font
