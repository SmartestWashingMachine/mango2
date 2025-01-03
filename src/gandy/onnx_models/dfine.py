from gandy.onnx_models.base_onnx_model import BaseONNXModel
import torchvision.transforms as T
import torch
from PIL import Image
import numpy as np

# A lot of code borrowed from: https://github.com/Peterande/D-FINE/blob/master/tools/inference/onnx_inf.py
# Can I just say how GRATEFUL I am to have a working functional ONNX example? Ultralytics was so... "vague" OML.

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

class DFineONNX(BaseONNXModel):
    def __init__(self, onnx_path, use_cuda):
        super().__init__(use_cuda=use_cuda)

        self.load_session(onnx_path)

        self.tensor_transforms = T.Compose([
            T.ToTensor(),
        ])

    def forward(self, x: Image.Image):
        resized_im_pil, ratio, pad_w, pad_h = resize_with_aspect_ratio(x, 1024)
        orig_size = torch.tensor([[resized_im_pil.size[1], resized_im_pil.size[0]]])

        im_data = self.tensor_transforms(resized_im_pil).unsqueeze(0)
        output = self.ort_sess.run(
            output_names=None,
            input_feed={'images': im_data.numpy(), "orig_target_sizes": orig_size.numpy()}
        )

        # bboxes_data mapped to be like YOLOONNX - [1, 5, 8400] where the 2nd axis (5 elements) represents the coordinates and the confidence score.
        labels, boxes, scores = output
        bboxes = []

        # [0] refers to the first image in the batch - the only image.
        for lbl, bb, scr in zip(labels[0], boxes[0], scores[0]):
            bb = [
                # Unpad.
                (bb[0] - pad_w) / ratio,
                (bb[1] - pad_h) / ratio,
                (bb[2] - pad_w) / ratio,
                (bb[3] - pad_h) / ratio,
                # Add confidence.
                scr,
            ]

            # Clip - rarely DETR goes under/over.
            bb[0] = max(0, bb[0])
            bb[1] = max(0, bb[1])
            bb[2] = min(x.width, bb[2])
            bb[3] = min(x.height, bb[3])

            bboxes.append(bb)

        # [1("bsz"), 5(coords + score), N(number of boxes)]
        return np.stack(bboxes, axis=1)[np.newaxis, ...]
