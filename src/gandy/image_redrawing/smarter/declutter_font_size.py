
from PIL import Image
from gandy.image_redrawing.smarter.text_box import TextBox
from gandy.image_redrawing.smarter.image_fonts import print_spam
from typing import List

CLUTTER_THRESHOLD = 0.15

# FROM: GlobalSmart
def declutter_font_size(
    text_boxes: List[TextBox],
    min_font_size: int,
    max_font_size: int,
    img: Image.Image,
):
    best_font_size = max_font_size

    for tb in text_boxes:
        tb.set_font_size(best_font_size)

    # Then cut it down even further! (if the text is too cluttered)
    image_area = img.width * img.height
    total_text_area = sum(tb.get_area() for tb in text_boxes)
    while (
        total_text_area / image_area
    ) >= CLUTTER_THRESHOLD and best_font_size > 1:
        print_spam(
            f"Text cluttered! ({total_text_area / image_area}) - cutting down font size."
        )

        best_font_size = max(1, int(best_font_size * 0.8))

        for tb in text_boxes:
            tb.set_font_size(best_font_size)
        total_text_area = sum(tb.get_area() for tb in text_boxes)

    print_spam(
        f"Done decluttering text! TextArea=({total_text_area / image_area}) FontSize={best_font_size}"
    )

    # best_font_size is used to draw the texts later on in case one of the texts is smaller than the others before it.
    return best_font_size
