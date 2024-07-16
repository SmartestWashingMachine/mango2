from PIL import Image
import numpy as np
from gandy.onnx_models.ttnet import TTNetONNX
from gandy.image_cleaning.base_image_clean import BaseImageClean
from gandy.onnx_models.edge_connect import EdgeConnectONNX
from math import floor
import albumentations as A
from gandy.state.config_state import config_state


class TNetEdgeImageClean(BaseImageClean):
    def __init__(self):
        super().__init__()

        self.transform = self.get_image_transform()

    def can_load(self):
        return super().can_load(path_exists="models/ttnet/ttnet.onnx")

    def load_model(self):
        # TSeg detects segmentation binary masks for the text.
        self.tnet_model = TTNetONNX(
            "models/ttnet/ttnet.onnx", use_cuda=config_state.use_cuda
        )

        # Modified EdgeConnect to inpaint.
        self.edge_connect = EdgeConnectONNX(
            "models/edge_connect/edge_connect.onnx",
            use_cuda=config_state.use_cuda,
        )

        return super().load_model()

    def get_image_transform(self):
        # Just to detect text masks.
        transforms = [A.ToGray(always_apply=True)]

        return A.Compose(transforms)

    def detect_mask(self, cropped_image):
        return self.tnet_model.full_pipe(cropped_image)[
            0
        ]  # We don't care for confidence scores.

    def process(self, image: Image.Image, bboxes):
        full_mask_image = image.copy()
        full_mask_image = np.array(full_mask_image)
        full_mask_image[:, :, :] = 0  # Fill background.
        full_mask_image = full_mask_image[:, :, :1]  # Only get 1 channel.

        for bbox in bboxes:
            x1, y1, x2, y2 = bbox
            x1 = floor(x1)
            y1 = floor(y1)
            x2 = floor(x2)
            y2 = floor(y2)

            cropped_image = image.crop([x1, y1, x2, y2])

            cropped_image = np.array(cropped_image)
            cropped_image = self.transform(image=cropped_image)["image"]

            detected_mask = self.detect_mask(
                cropped_image
            )  # Expected to be H * W * 1 (where 1 = channel)
            detected_mask = detected_mask * 255

            # Add that text mask. Should be in range [0, 255]

            # NOTE: Sometimes the mask is larger than the image due to bounding box rounding errors. Todo fix. Currently bandaid fix.
            if x2 > full_mask_image.shape[1]:
                detected_mask = detected_mask[:, 0 : full_mask_image.shape[1] - x1, :]
            if y2 > full_mask_image.shape[0]:
                detected_mask = detected_mask[0 : full_mask_image.shape[0] - y1, :, :]

            full_mask_image[y1:y2, x1:x2] = detected_mask

        # Clean!
        inp = (np.array(image), full_mask_image)
        inpainted_image = self.edge_connect.full_pipe(inp)

        inpainted_image = Image.fromarray(inpainted_image)
        return inpainted_image
