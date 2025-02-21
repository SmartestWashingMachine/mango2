from gandy.text_detection.yolo_image_detection import YOLOTDImageDetectionApp
import numpy as np
import torch
from gandy.state.config_state import config_state
from gandy.utils.fancy_logger import logger
from gandy.onnx_models.dfine import DFineONNX
from gandy.text_detection.line_mixin import ExpandedLineMixin
import albumentations as A
from PIL import Image

class DFineImageDetectionApp(YOLOTDImageDetectionApp):
    def load_model(self):
        if not self.loaded:
            can_cuda = self.check_cuda()

            logger.info(
                f"Loading object detection model ({self.model_name})... CUDA: {config_state.use_cuda} FORCE CPU: {config_state.force_td_cpu} WILLCUDA={can_cuda}"
            )
            self.model = DFineONNX(
                f"models/yolo/{self.model_name}.onnx", use_cuda=can_cuda,
            )

            logger.info("Done loading object detection model!")

            self.loaded = True

    def detect_bboxes(self, image):
        if image.mode != "RGB":
            image = image.convert("RGB")  # Needs 3 channels.

        logger.log_message(
            "Passing image into DFINE object detection model..."
        )

        # [1, 1] refers to padded_hw. It's unused here but we still need to return some dummy value.
        return self.model.full_pipe(image), [1, 1]
    
    def map_bboxes_data(self, bboxes_data, padded_hw):
        bboxes_data = np.transpose(bboxes_data)  # [N, 5]

        bboxes_pos = bboxes_data[:, :4]
        bboxes_scores = bboxes_data[:, 4]

        # Must return [n_boxes, 4] and [n_boxes]
        return bboxes_pos, bboxes_scores
    
    def scale_boxes(self, img1_shape, boxes, img0_shape, ratio_pad=None):
        return boxes
    
    def process_before_tnms(self, bboxes_scores, bboxes_pos, image_width, image_height):
        # D-FINE (and DETR...) models sometimes "bug" out and place a bounding box around nearly the ENTIRE image - we almost never want this.
        # (Exceptions being the line model variants)
        # Unlike YOLO and DETR, D-FINE models are already scaled to the actual image size by this point.
        bboxes_heights = bboxes_pos[:, 3] - bboxes_pos[:, 1]
        bboxes_widths = bboxes_pos[:, 2] - bboxes_pos[:, 0]
        bboxes_areas = (bboxes_heights * bboxes_widths)

        image_area = image_width * image_height

        valid_mask = (bboxes_areas / image_area) <= 0.94
        bboxes_pos = bboxes_pos[valid_mask, :]
        bboxes_scores = bboxes_scores[valid_mask]

        return bboxes_pos, bboxes_scores

class DFineLineImageDetectionApp(DFineImageDetectionApp, ExpandedLineMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_image_transform(self):
        transforms = [
            A.ToGray(always_apply=True),
        ]

        return A.Compose(transforms)

    def check_cuda(self):
        can_cuda = config_state.use_cuda and not config_state.force_tl_cpu
        return can_cuda
    
    def detect_bboxes(self, image):
        if image.mode != "RGB":
            image = image.convert("RGB")

        image = self.transform(image=np.array(image))['image']
        image = Image.fromarray(image)

        logger.log_message(
            "Passing image into DFINE line object detection model..."
        )

        # [1, 1] refers to padded_hw. It's unused here but we still need to return some dummy value.
        return self.model.full_pipe(image), [1, 1]
    
    def process_before_tnms(self, bboxes_scores, bboxes_pos, image_width, image_height):
        return bboxes_pos, bboxes_scores