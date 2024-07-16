from gandy.image_redrawing.image_redraw_global_smart import (
    ImageRedrawGlobalSmartApp,
    load_font,
)
from random import choices


def add_padding(box, img):
    padding_pct = 0.15

    width = box[2] - box[0]
    height = box[3] - box[1]

    xa = int(width * padding_pct)
    ya = int(height * padding_pct)

    return [
        max(box[0] - xa, 0),
        max(box[1] - ya, 0),
        min(box[2] + xa, img.width - 1),
        min(box[3] + ya, img.height - 1),
    ]


def get_center_of_box(box):
    return (
        box[0] + ((box[2] - box[0]) / 2),
        box[1] + ((box[3] - box[1]) / 2),
    )


class ImageRedrawGlobalSmartBackgroundApp(ImageRedrawGlobalSmartApp):
    def __init__(self):
        super().__init__()

    def draw_details(self, text_details, best_font_size, draw, image, text_colors):
        for td in text_details:
            chosen_color = tuple(choices(range(256), k=3))

            td_box = td[-1]
            td_coords = [td_box[0], td_box[1], td_box[2], td_box[3]]

            draw.rounded_rectangle(
                add_padding(td_coords, image),
                outline=chosen_color + (255,),
                width=1,
                radius=6,
            )

            draw.line(
                [
                    get_center_of_box(td[-1]),
                    get_center_of_box(td[-3]),
                ],
                fill=chosen_color + (255,),
                width=6,
            )

        for idx, td in enumerate(text_details):
            # td = A list containing [wrappedtextstring, leftinteger, topinteger]
            font = load_font(best_font_size)

            draw.multiline_text(
                (td[1], td[2]),
                td[0],
                self.get_text_color(text_colors, idx),
                font,
                align="center",
                stroke_fill=self.get_stroke_color(text_colors, idx),
                stroke_width=max(2, best_font_size // 7),
            )

        return image
