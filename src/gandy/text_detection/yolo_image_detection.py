import numpy as np
import albumentations as A
import logging
import cv2
import numpy as np
from gandy.state.config_state import config_state
from gandy.onnx_models.yolo import YOLOONNX
from gandy.text_detection.base_image_detection import BaseImageDetection
from gandy.text_detection.line_mixin import LineMixin
from gandy.utils.tnms import tnms
from gandy.utils.fancy_logger import logger
from gandy.utils.filter_out_overlapping_bboxes import filter_out_overlapping_bboxes

def gt_min_size(box: np.ndarray):
    widths = box[:, 2] - box[:, 0]
    heights = box[:, 3] - box[:, 1]

    # New YOLO XL model sometimes bugs out without this check.
    mask = (widths > 1) & (heights > 1)

    return box[mask]


# This function and scale_boxes is from ultralytics.
def clip_boxes(boxes: np.ndarray, shape):
    """
    It takes a list of bounding boxes and a shape (height, width) and clips the bounding boxes to the
    shape

    Args:
      boxes (torch.Tensor): the bounding boxes to clip
      shape (tuple): the shape of the image
    """
    boxes[..., [0, 2]] = boxes[..., [0, 2]].clip(0, shape[1])  # x1, x2
    boxes[..., [1, 3]] = boxes[..., [1, 3]].clip(0, shape[0])  # y1, y2
    return boxes


def scale_boxes(img1_shape, boxes, img0_shape, ratio_pad=None):
    """
    Rescales bounding boxes (in the format of xyxy) from the shape of the image they were originally specified in
    (img1_shape) to the shape of a different image (img0_shape).

    Args:
      img1_shape (tuple): The shape of the image that the bounding boxes are for, in the format of (height, width).
      boxes (torch.Tensor): the bounding boxes of the objects in the image, in the format of (x1, y1, x2, y2)
      img0_shape (tuple): the shape of the target image, in the format of (height, width).
      ratio_pad (tuple): a tuple of (ratio, pad) for scaling the boxes. If not provided, the ratio and pad will be
                         calculated based on the size difference between the two images.

    Returns:
      boxes (torch.Tensor): The scaled bounding boxes, in the format of (x1, y1, x2, y2)
    """
    if ratio_pad is None:  # calculate from img0_shape
        gain = min(
            img1_shape[0] / img0_shape[0], img1_shape[1] / img0_shape[1]
        )  # gain  = old / new
        pad = (img1_shape[1] - img0_shape[1] * gain) / 2, (
            img1_shape[0] - img0_shape[0] * gain
        ) / 2  # wh padding
    else:
        gain = ratio_pad[0][0]
        pad = ratio_pad[1]

    boxes[..., [0, 2]] -= pad[0]  # x padding
    boxes[..., [1, 3]] -= pad[1]  # y padding
    boxes[..., :4] /= gain

    boxes = clip_boxes(boxes, img0_shape)
    return boxes


def cxcy_to_corners(dets):
    cx = dets[:, 0]
    cy = dets[:, 1]
    half_width = dets[:, 2] / 2
    half_height = dets[:, 3] / 2

    x1 = cx - half_width
    y1 = cy - half_height
    x2 = cx + half_width
    y2 = cy + half_height

    return np.stack((x1, y1, x2, y2), axis=-1)


class YOLOImageDetectionApp(BaseImageDetection):
    def __init__(self):
        """
        This app uses a custom YOLOv8 model (pretrained with COCO, finetuned on a custom dataset).
        """
        super().__init__()

        self.transform = self.get_image_transform()
        self.confidence_threshold = 0
        self.iou_thr = 0.25

        self.image_size = 640

        self.filter_out_overlapping_bboxes = False

    # The code for this method is from ultralytics YOLO with a bit of tweaks (keeping stride and new_shape fixed).
    def resize_np_img(self, img):
        new_shape = [self.image_size, self.image_size]

        shape = img.shape[:2]  # current shape [height, width]

        # Scale ratio (new / old)
        r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])

        # Compute padding
        new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
        dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]  # wh padding

        # minimum rectangle
        # Does not work for ONNX. Why? Ask ultralytics! Unfortunately, you'll likely just get a GPT answer...
        # This will slightly impact accuracy (at least from my personal experiments). Oh well...
        # stride = 32
        # dw, dh = np.mod(dw, stride), np.mod(dh, stride)  # wh padding

        dw /= 2  # divide padding into 2 sides
        dh /= 2

        if shape[::-1] != new_unpad:  # resize
            img = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)
        top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
        left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
        img = cv2.copyMakeBorder(
            img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=(114, 114, 114)
        )  # add border

        return img

    def get_image_transform(self):
        transforms = [
            # A.Resize(640, 640, interpolation=cv2.INTER_LINEAR),
            A.ToGray(always_apply=True),
        ]

        return A.Compose(transforms)

    def load_model(self):
        if not hasattr(self, "model"):
            raise RuntimeError(
                "YOLOImageDetectionApp is a base app intended to be used by other classes. Instead, use YOLOTD."
            )

        self.loaded = True

    def unload_model(self):
        try:
            del self.model
            logger.info("Unloading object detection model...")
        except:
            pass
        self.model = None

        return super().unload_model()

    def map_bboxes_data(self, bboxes_data, padded_hw):
        bboxes_data = np.transpose(bboxes_data)  # [8400, 5]

        bboxes_pos = cxcy_to_corners(bboxes_data[:, :4])
        bboxes_scores = bboxes_data[:, 4]

        # Must return [n_boxes, 4] and [n_boxes]
        return bboxes_pos, bboxes_scores

    def fuse_boxes(self, bboxes_data, padded_hw):
        logger.log_message(
            f"Using non maximum suppression to postprocess object detections..."
        )

        # bboxes_data for YOLO = [1, 5, 8400] where the 2nd axis (5 elements) represents the coordinates and the confidence score.
        bboxes_data = bboxes_data[0]  # Remove batch. [5, 8400]

        bboxes_pos, bboxes_scores = self.map_bboxes_data(bboxes_data, padded_hw)

        # NMS
        keep = tnms(
            bboxes_pos,
            bboxes_scores,
            thresh=self.iou_thr,
        )

        processed_boxes = bboxes_pos[keep, :]
        scores = bboxes_scores[keep]

        if self.confidence_threshold is not None:
            boxes = []
            for i in range(len(scores)):
                if scores[i] >= self.confidence_threshold:
                    boxes.append(processed_boxes[i])

            if len(boxes) > 0:
                boxes = np.stack(boxes, axis=0)
            else:
                boxes = np.empty((0, 4))
        else:
            boxes = processed_boxes

        logger.log_message(f"Done using NMS! (Filtered Boxes #: {boxes.shape[0]})")

        return boxes

    def detect_bboxes(self, image):
        image = image.convert("RGB")  # Needs 3 channels.

        logger.log_message(
            "Transforming image before passing it into object detection model..."
        )

        t_x = self.transform(image=np.array(image))["image"]

        t_x = self.resize_np_img(t_x)

        t_x = t_x.astype(np.float32) / 255.0  # Normalize.
        t_x = np.transpose(t_x, (2, 0, 1))  # Channels last to channels first. CHW
        t_x = t_x[np.newaxis, ...]  # Unsqueeze to get batch=1. BCHW

        return self.model.full_pipe(t_x), t_x.shape[2:]

    def process(self, image, do_sort=True, return_list=True):
        image_width, image_height = image.size

        logger.log_message("Detecting boxes...")
        dict_output, padded_hw = self.detect_bboxes(image)

        logger.log_message("Fusing boxes...")
        bboxes = self.fuse_boxes(dict_output, padded_hw)

        logger.log_message("Sorting boxes...")
        if do_sort:
            bboxes = self.sort_bboxes(bboxes, image_width, image_height)

        # bboxes = self.rescale_bboxes(bboxes, image_width, image_height)
        bboxes = scale_boxes(padded_hw, bboxes, (image_height, image_width))

        # EDIT: No longer needed I think. Don't let me down YOLO! bboxes = gt_min_size(bboxes)

        if return_list:
            bboxes = bboxes.tolist()

            if self.filter_out_overlapping_bboxes:
                bboxes = filter_out_overlapping_bboxes(bboxes)

            return bboxes
        else:
            assert not self.filter_out_overlapping_bboxes

            return bboxes


class YOLOTDImageDetectionApp(YOLOImageDetectionApp):
    def __init__(self, confidence_threshold=0.5, iou_thr=0.25, model_name="yolo_td", image_size = 640, filter_out_overlapping_bboxes = False):
        """
        Slower than the RCNNImageDetectionApp, but more precise.
        """
        super().__init__()

        self.confidence_threshold = confidence_threshold
        self.model_name = model_name
        self.iou_thr = iou_thr

        self.image_size = image_size
        self.filter_out_overlapping_bboxes = filter_out_overlapping_bboxes

    def can_load(self):
        return super().can_load(f"models/yolo/{self.model_name}.onnx")

    def load_model(self):
        if not self.loaded:
            can_cuda = config_state.use_cuda and not config_state.force_td_cpu

            logger.info(
                f"Loading object detection model ({self.model_name})... CUDA: {config_state.use_cuda} FORCE CPU: {config_state.force_td_cpu}"
            )
            self.model = YOLOONNX(
                f"models/yolo/{self.model_name}.onnx", use_cuda=can_cuda,
            )

            logger.info("Done loading object detection model!")

            return super().load_model()

    def unload_model(self):
        try:
            del self.model
            logger.info("Unloading object detection model...")
        except:
            pass
        self.model = None

        return super().unload_model()


class YOLOLineImageDetectionApp(YOLOImageDetectionApp, LineMixin):
    def __init__(self, confidence_threshold=0.25, iou_thr=0.4, model_name="yolo_line", image_size = 640):
        """
        Detects text lines in speech bubbles.
        """
        super().__init__()

        self.confidence_threshold = confidence_threshold
        self.model_name = model_name
        self.iou_thr = iou_thr

        self.image_size = image_size

    def load_model(self):
        if not self.loaded:
            can_cuda = config_state.use_cuda and not config_state.force_translation_cpu
            logger.info(
                f"Loading object line detection model ({self.model_name})... CUDA: {config_state.use_cuda} FORCE CPU: {config_state.force_td_cpu}"
            )
            self.model = YOLOONNX(
                f"models/yolo/{self.model_name}.onnx", use_cuda=can_cuda,
            )

            logger.info("Done loading object line detection model!")

            return super().load_model()

    def can_load(self):
        return super().can_load(f"models/yolo/{self.model_name}.onnx")
