from gandy.image_redrawing.smart.utils.compute_text_box import compute_text_box


class MagicBox:
    """
    A wrapper class for a speech box (coords are for speech box). Internally caches the text box.
    """

    def __init__(self, x1, y1, x2, y2, text: str, can_change_font_size=False) -> None:
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.text = text

        self._text_box = None

        self._text_align_direction = None
        self._font_size = None
        self._old_x1 = None
        self._old_y1 = None
        self._old_x2 = None
        self._old_y2 = None
        self._text = None

        # If True and this box already has a font_size set, then this text box will be recomputed when receiving a different font size.
        # Otherwise, the box will remain the same with the old, larger font size even if a smaller font size is received.
        # This is just a hacky workaround for last ditch effort attempts - we only allow the last ditch effort boxes to be reduced in font size.
        self.can_change_font_size = can_change_font_size

    def __getitem__(self, idx):
        if idx == 0:
            return self.x1
        elif idx == 1:
            return self.y1
        elif idx == 2:
            return self.x2
        elif idx == 3:
            return self.y2
        elif idx == 4 or idx == -1:
            return self.text
        else:
            raise IndexError(f"Bad index for MagicBox: {idx}")

    def __setitem__(self, idx, value):
        if idx == 0:
            self.x1 = value
        elif idx == 1:
            self.y1 = value
        elif idx == 2:
            self.x2 = value
        elif idx == 3:
            self.y2 = value
        elif idx == 4 or idx == -1:
            self.text = value
        else:
            raise IndexError(f"Bad index for MagicBox: {idx}")

    def validate_font_size_is_same(self, font_size):
        font_size_is_diff = False
        if self._font_size is None:
            font_size_is_diff = True
        elif self._font_size != font_size and self.can_change_font_size:
            font_size_is_diff = True

        return not font_size_is_diff

    def get_text_box(self, font_size, text_align_direction, draw, text=None):
        text = text or self.text

        # If true, just return the cached text box.
        if (
            self.x1 == self._old_x1
            and self.y1 == self._old_y1
            and self.x2 == self._old_x2
            and self.y2 == self._old_y2
            and self._font_size == font_size
            and self.validate_font_size_is_same(font_size)
            and self._text_align_direction == text_align_direction
            and self._text == text
        ):
            return self._text_box

        self._text_box = compute_text_box(
            font_size, text, self, text_align_direction, draw
        )
        self._old_x1 = self.x1
        self._old_y1 = self.y1
        self._old_x2 = self.x2
        self._old_y2 = self.y2
        self._font_size = font_size
        self._text_align_direction = text_align_direction
        self._text = text

        return self._text_box

    def __repr__(self) -> str:
        return f"{self.text} - [{self.x1}, {self.y1}, {self.x2}, {self.y2}]"
