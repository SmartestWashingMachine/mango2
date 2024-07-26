from gandy.state.config_state import config_state

def compute_stroke_size(font_size: int):
    min_stroke_size = 1

    comp = round(font_size * (config_state.stroke_size / 8))

    return max(min_stroke_size, comp)
