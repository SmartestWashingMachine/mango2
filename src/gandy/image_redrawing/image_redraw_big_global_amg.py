from PIL import Image
from gandy.image_redrawing.image_redraw_big_global import ImageRedrawBigGlobalApp
from gandy.image_redrawing.amg_convert import to_amg


class ImageRedrawBigGlobalAMGApp(ImageRedrawBigGlobalApp):
    def process(self, image: Image, bboxes, target_texts, *args, **kwargs):
        typed_image = super().process(image, bboxes, target_texts, *args, **kwargs)

        return to_amg(typed_image, bboxes, target_texts)
