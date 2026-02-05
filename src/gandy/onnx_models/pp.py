from gandy.onnx_models.base_onnx_model import BaseONNXModel
import cv2
from PIL import Image
import numpy as np

def merge_boxes(boxes):
    """Calculates the bounding box that encompasses all boxes in the list."""
    if not boxes:
        return None
    x_min = min(b[0] for b in boxes)
    y_min = min(b[1] for b in boxes)
    x_max = max(b[2] for b in boxes)
    y_max = max(b[3] for b in boxes)
    return (x_min, y_min, x_max, y_max)

def calculate_overlap_ratio(b1_start, b1_end, b2_start, b2_end):
    """Generic 1D overlap ratio (intersection / box_length)."""
    box_len = b1_end - b1_start
    if box_len <= 0: return 0.0
    
    intersection = min(b1_end, b2_end) - max(b1_start, b2_start)
    return max(0, intersection) / box_len

# TODO: We may not want this in the future... This is currently needed due to LineMixin messing up the reading order sometimes.
def group_and_merge_bboxes(boxes, overlap_threshold=0.5):
    if not boxes:
        return []

    avg_aspect_ratio = sum((b[2]-b[0])/(b[3]-b[1]) for b in boxes) / len(boxes)
    is_horizontal = avg_aspect_ratio >= 1.0

    # Horizontal: Group by Y (idx 1,3), Sort by X (idx 0)
    # Vertical:   Group by X (idx 0,2), Sort by Y (idx 1)
    group_idx = (1, 3) if is_horizontal else (0, 2)
    sort_idx = 0 if is_horizontal else 1

    # TODO: Maybe unnecessary.
    boxes.sort(key=lambda b: (b[group_idx[0]], b[sort_idx]))

    lines = []
    current_group = []
    curr_min, curr_max = -1, -1

    for box in boxes:
        b_min, b_max = box[group_idx[0]], box[group_idx[1]]
        
        overlap = calculate_overlap_ratio(b_min, b_max, curr_min, curr_max)

        if current_group and overlap >= overlap_threshold:
            current_group.append(box)

            curr_min = min(curr_min, b_min)
            curr_max = max(curr_max, b_max)
        else:
            if current_group:
                lines.append(merge_boxes(current_group))
            current_group = [box]
            curr_min, curr_max = b_min, b_max

    if current_group:
        lines.append(merge_boxes(current_group))

    return lines

# This is copied from D-Fine, but is probably not equivalent to whatever preprocessing they use.
def resize_with_aspect_ratio(image, size, interpolation=Image.BICUBIC):
    """Resizes an image while maintaining aspect ratio and pads it."""
    original_width, original_height = image.size
    ratio = min(size / original_width, size / original_height)
    new_width = int(original_width * ratio)
    new_height = int(original_height * ratio)
    image = image.resize((new_width, new_height), interpolation)

    # Create a new image with the desired size and paste the resized image onto it
    new_image = Image.new("RGB", (size, size))
    new_image.paste(image, ((size - new_width) // 2, (size - new_height) // 2))
    return new_image, ratio, (size - new_width) // 2, (size - new_height) // 2

class PpONNX(BaseONNXModel):
    def __init__(self, onnx_path, use_cuda):
        super().__init__(use_cuda=use_cuda)

        self.load_session(onnx_path)

        self.box_thresh = 0.6
        self.thresh = 0.3
        self.unclip = 1.5

    # Partially vibe-verified.
    def map_to_boxes(self, pred_map, thresh=0.3, box_thresh=0.6, unclip_ratio=1.5):
        dest_h, dest_w = pred_map.shape[1:3]
        pred = pred_map[0]

        thresh = self.thresh
        box_thresh = self.box_thresh
        unclip_ratio = self.unclip

        bitmap = (pred > thresh).astype(np.uint8)

        contours, _ = cv2.findContours((bitmap * 255), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        boxes = []
        for contour in contours:
            # Get the oriented bounding "box" from the segmentation map.
            rect = cv2.minAreaRect(contour)
            points = cv2.boxPoints(rect)

            points = sorted(list(points), key=lambda x: x[0])
            if points[1][1] > points[0][1]:
                index_1, index_4 = 0, 1
            else:
                index_1, index_4 = 1, 0
            if points[3][1] > points[2][1]:
                index_2, index_3 = 2, 3
            else:
                index_2, index_3 = 3, 2

            box = np.array([points[index_1], points[index_2], points[index_3], points[index_4]])

            # Just a heuristic.
            if min(rect[1]) < 3:
                continue

            # We calculate the mean score of the pixels INSIDE the box
            xmin = np.clip(np.floor(box[:, 0].min()).astype(int), 0, dest_w - 1)
            xmax = np.clip(np.ceil(box[:, 0].max()).astype(int), 0, dest_w - 1)
            ymin = np.clip(np.floor(box[:, 1].min()).astype(int), 0, dest_h - 1)
            ymax = np.clip(np.ceil(box[:, 1].max()).astype(int), 0, dest_h - 1)

            mask = np.zeros((ymax - ymin + 1, xmax - xmin + 1), dtype=np.uint8)
            shifted_box = box.copy()
            shifted_box[:, 0] -= xmin
            shifted_box[:, 1] -= ymin
            cv2.fillPoly(mask, [shifted_box.astype(np.int32)], 1)

            # The crucial part: mean of probability map in that region
            score = cv2.mean(pred[ymin:ymax + 1, xmin:xmax + 1], mask)[0]

            if score < box_thresh:
                continue

            # Vatti Unclip (Expansion)
            # Distance = (Area * unclip_ratio) / Perimeter
            area = cv2.contourArea(box)
            perimeter = cv2.arcLength(box, True)
            if perimeter == 0: continue
            distance = area * unclip_ratio / perimeter

            new_w, new_h = rect[1][0] + distance * 2, rect[1][1] + distance * 2
            expanded_rect = (rect[0], (new_w, new_h), rect[2])
            expanded_box = cv2.boxPoints(expanded_rect)

            x1, y1 = np.min(expanded_box, axis=0)
            x2, y2 = np.max(expanded_box, axis=0)

            boxes.append([x1, y1, x2, y2])

        return boxes

    def np_transform(self, image: Image.Image):
        arr = np.array(image, dtype=np.uint8)
        norm = arr.astype(np.float32) / 255.0 # Scale to [0, 1] just like torchvision's ToTensor.

        # From HWC to CHW
        norm = np.transpose(norm, (2, 0, 1))

        return norm

        """
        If I'm reading the code right, they use BGR and normalize too? Yet I'm getting better results here WITHOUT doing that...

        # RGB to BGR
        norm = norm[::-1, :, :]

        # Normalize.
        mu = np.array([0.485, 0.456, 0.406], dtype=np.float32)[:, np.newaxis, np.newaxis] # [3, 1, 1]
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)[:, np.newaxis, np.newaxis]

        norm = (norm - mu) / std

        return norm
        """

    def forward(self, x: Image.Image):
        resized_im_pil, ratio, pad_w, pad_h = resize_with_aspect_ratio(x, 960)

        im_data = self.np_transform(resized_im_pil)
        im_data = im_data[None, ...] # Unsqueeze to get a batch size of 1.

        output = self.ort_sess.run(
            output_names=None,
            input_feed={"x": im_data,}
        )

        mapped_boxes = self.map_to_boxes(output[0][0, ...]) # First [0] to get first output (only output). Only 1 image in batch so we take that.

        bboxes = []
        for bb in mapped_boxes:
            bb = [
                # Unpad.
                (bb[0] - pad_w) / ratio,
                (bb[1] - pad_h) / ratio,
                (bb[2] - pad_w) / ratio,
                (bb[3] - pad_h) / ratio,
            ]

            # Clip - rarely DETR goes under/over.
            bb[0] = max(0, bb[0])
            bb[1] = max(0, bb[1])
            bb[2] = min(x.width, bb[2])
            bb[3] = min(x.height, bb[3])

            bboxes.append(bb)

        bboxes = group_and_merge_bboxes(bboxes, overlap_threshold=0.35)
        bboxes = [[*b, 1.0] for b in bboxes] # Add dummy confidence score.

        if len(bboxes) == 0:
            """
            TODO
            Filter out properly. This would break a core assumption for the API though.
            Currently we assume there's ALWAYS text in a region to detect, and if nothing is found line-wise,
            we scan the entire region as a fallback.

            But PP is different; no lines found may mean the region model itself was faulty.
            So we would want YOLOTD to properly work with nothing found...
            And then modify TROCR to optionally check if the line app permits empty detections, skipping it with empty text if so.

            "But what about inpainting?!" - We would also need to ensure cleaning/inpainting ignores empty texts. 
            (^ I think that's already the case)

            EDIT: No, this is not the case.
            """
            bboxes = [[0, 0, x.width, x.height, 1.0]]

        return np.stack(bboxes, axis=1)[np.newaxis, ...]
