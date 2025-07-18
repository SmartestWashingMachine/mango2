from gandy.text_detection.base_image_detection import BaseImageDetection
import numpy as np


class LineMixin(BaseImageDetection):
    def get_images(self, image, return_image_if_fails = True):
        """
        Returns one image object per detected text line. Can boost OCR accuracy.

        image = PIL image cropped to a text region.
        """
        self.load_model()

        bboxes: np.ndarray = self.process(
            image, do_sort=False, return_list=False
        )  # [N, 4] (where 4 == (x1, y1, x2, y2))

        # Sort from left-to-right to right-to-left
        if bboxes.shape[0] > 1:
            image_width, image_height = image.size
            x1 = bboxes[:, 0]  # [N]
            y1 = bboxes[:, 1]
            x2 = bboxes[:, 2]
            y2 = bboxes[:, 3]

            width = x2 - x1
            height = y2 - y1

            aspect_ratio = width / height
            avg_aspect_ratio = aspect_ratio.mean()

            # Previous avg aspect ratio was 0.5.
            if avg_aspect_ratio <= 1.0:
                # Here we assume texts are vertical.
                # For vertical texts, the horizontal distance is far more important than the vertical distance.
                x_weight = 1.0
                y_weight = 0.01
            else:
                # Here we assume texts are horizontal.
                # For horizontal texts, the vertical distance is far more important.
                x_weight = 0.01
                y_weight = 1.0

            # Here it's assumed that (x1, y1) are the points for each box, and the closest points to the TOP RIGHT of the image come first.
            x_comp = (image_width - x1) ** 2
            y_comp = (y1) ** 2

            distances = ((x_comp * x_weight) + (y_comp * y_weight)) ** 0.5
            sorted_indices = np.argsort(
                distances, axis=0
            )  # [N] (The rightmost indices come first.)
            bboxes = bboxes[sorted_indices, :]

        # Then return the new line bboxes.
        if bboxes.shape[0] == 0 and return_image_if_fails:
            # No text lines detected can sometimes occur for very small single line text. In this case just scan the whole image for text recognition later on.
            im_width, im_height = image.size
            frame_bboxes = np.array([[0, 0, im_width, im_height]])
            return frame_bboxes
        else:
            return bboxes


class ExpandedLineMixin(LineMixin):
    def get_images(self, image, return_image_if_fails = True):
        """
        Returns one image object per detected text line. Can boost OCR accuracy.

        image = PIL image cropped to a text region.
        """
        self.load_model()

        bboxes: np.ndarray = self.process(
            image, do_sort=False, return_list=False
        )  # [N, 4] (where 4 == (x1, y1, x2, y2))

        # Sort from left-to-right to right-to-left
        if bboxes.shape[0] > 1:
            x1 = bboxes[:, 0]  # [N]
            y1 = bboxes[:, 1]
            x2 = bboxes[:, 2]
            y2 = bboxes[:, 3]

            width = x2 - x1
            height = y2 - y1

            aspect_ratio = width / height
            avg_aspect_ratio = aspect_ratio.mean()

            # Previous avg aspect ratio was 0.5.
            if avg_aspect_ratio <= 1.0:
                return super().get_images(image, return_image_if_fails)

            # Here we assume texts are horizontal.
            # Closest points to the TOP LEFT of the image come first.

            x_comp = (x1)
            y_comp = (y1) * 3

            distances = (x_comp + y_comp) ** 0.5

            sorted_indices = np.argsort(
                distances, axis=0
            )  # [N] (The rightmost indices come first.)
            bboxes = bboxes[sorted_indices, :]

        # Then return the new line bboxes.
        if bboxes.shape[0] == 0 and return_image_if_fails:
            # No text lines detected can sometimes occur for very small single line text. In this case just scan the whole image for text recognition later on.
            im_width, im_height = image.size
            frame_bboxes = np.array([[0, 0, im_width, im_height]])
            return frame_bboxes
        else:
            return bboxes

# Expands each line slightly to account for tight fits.
class ExpandedLineMixinWithMargin(ExpandedLineMixin):
    def get_images(self, image, return_image_if_fails=True):
        im_width, im_height = image.size
        bboxes: np.ndarray = super().get_images(image, return_image_if_fails)

        x1 = bboxes[:, 0]  # [N]
        y1 = bboxes[:, 1]
        x2 = bboxes[:, 2]
        y2 = bboxes[:, 3]

        width = x2 - x1
        height = y2 - y1

        aspect_ratio = width / height
        avg_aspect_ratio = aspect_ratio.mean()

        extension_factor = 0.01

        if extension_factor > 0.0:
            if avg_aspect_ratio <= 1.0:
                # Vertical. Extend Y1 and Y2.
                bboxes[:, 1] = np.clip(bboxes[:, 1] - (height * extension_factor), a_min=0, a_max=im_height)
                bboxes[:, 3] = np.clip(bboxes[:, 3] + (height * extension_factor), a_min=0, a_max=im_height)
            else:
                # Horizontal. Extend X1 and X2.
                bboxes[:, 0] = np.clip(bboxes[:, 0] - (width * extension_factor), a_min=0, a_max=im_width)
                bboxes[:, 2] = np.clip(bboxes[:, 2] + (width * extension_factor), a_min=0, a_max=im_width)

        return bboxes
