from gandy.text_detection.yolo_image_detection import YOLOTDImageDetectionApp
import numpy as np
import torch
from gandy.text_detection.line_mixin import LineMixin, ExpandedLineMixin


# From ultralytics
def xywh2xyxy(x):
    """
    Convert bounding box coordinates from (x, y, width, height) format to (x1, y1, x2, y2) format where (x1, y1) is the
    top-left corner and (x2, y2) is the bottom-right corner.

    Args:
        x (np.ndarray | torch.Tensor): The input bounding box coordinates in (x, y, width, height) format.

    Returns:
        y (np.ndarray | torch.Tensor): The bounding box coordinates in (x1, y1, x2, y2) format.
    """
    assert (
        x.shape[-1] == 4
    ), f"input shape last dimension expected 4 but input shape is {x.shape}"
    y = (
        torch.empty_like(x) if isinstance(x, torch.Tensor) else np.empty_like(x)
    )  # faster than clone/copy
    dw = x[..., 2] / 2  # half-width
    dh = x[..., 3] / 2  # half-height
    y[..., 0] = x[..., 0] - dw  # top left x
    y[..., 1] = x[..., 1] - dh  # top left y
    y[..., 2] = x[..., 0] + dw  # bottom right x
    y[..., 3] = x[..., 1] + dh  # bottom right y
    return y


class RTDetrImageDetectionApp(YOLOTDImageDetectionApp):
    def map_bboxes_data(self, bboxes_data, padded_hw):
        # [300, 5]

        bboxes_pos = xywh2xyxy(bboxes_data[:, :4])  # [n_boxes, 4]

        bboxes_scores = bboxes_data[:, 4]

        bboxes_pos[:, 0] *= padded_hw[1]  # orig_img.width
        bboxes_pos[:, 2] *= padded_hw[1]  # orig_img.width
        bboxes_pos[:, 1] *= padded_hw[0]  # orig_img.height
        bboxes_pos[:, 3] *= padded_hw[0]  # orig_img.height

        # bboxes_pos = np.transpose(bboxes_pos) # [4, n_boxes]

        return bboxes_pos, bboxes_scores


class RTDetrLineImageDetectionApp(RTDetrImageDetectionApp, LineMixin):
    pass

class RTDetrExpandedLineImageDetectionApp(RTDetrImageDetectionApp, ExpandedLineMixin):
    pass