import math
import albumentations as A
from PIL import Image
import numpy as np
from gandy.utils.fancy_logger import logger

gray_tfm = A.Compose([A.ToGray(p=1.0)])

# Code not mine - it's from Huggingface.
# llama.cpp has built-in code to replicate smart_resize...
# but theirs requires us to calculate the exact image min size / max size and convert it into N tokens - a total headache to calculate for varying models.
def smart_resize(
    height: int,
    width: int,
    factor: int = 28,
    min_pixels: int = 28 * 28 * 130,
    max_pixels: int = 28 * 28 * 1280,
):
    """Rescales the image so that the following conditions are met:
    1. Both dimensions (height and width) are divisible by 'factor'.
    2. The total number of pixels is within the range ['min_pixels', 'max_pixels'].
    3. The aspect ratio of the image is maintained as closely as possible.
    """
    # if height < factor or width < factor:
    #    raise ValueError(f"height:{height} or width:{width} must be larger than factor:{factor}")
    # if int(height < factor//4) + int(width < factor//4):
    #     raise ValueError(f"height:{height} or width:{width} must be larger than factor:{factor//4}")

    if height < factor:
        print(f"smart_resize: height={height} < factor={factor}, reset height=factor")
        width = round((width * factor) / height)
        height = factor

    if width < factor:
        print(f"smart_resize: width={width} < factor={factor}, reset width=factor")
        height = round((height * factor) / width)
        width = factor

    if max(height, width) / min(height, width) > 200:
        raise ValueError(
            f"absolute aspect ratio must be smaller than 200, got {max(height, width) / min(height, width)}"
        )
    h_bar = round(height / factor) * factor
    w_bar = round(width / factor) * factor
    if h_bar * w_bar > max_pixels:
        beta = math.sqrt((height * width) / max_pixels)
        h_bar = math.floor(height / beta / factor) * factor
        w_bar = math.floor(width / beta / factor) * factor
    elif h_bar * w_bar < min_pixels:
        beta = math.sqrt(min_pixels / (height * width))
        h_bar = math.ceil(height * beta / factor) * factor
        w_bar = math.ceil(width * beta / factor) * factor
    return h_bar, w_bar

def pseudo_smart_resize(image, min_pixels, max_pixels, patch_size, merge_size):
    image = Image.fromarray(image).convert("RGB")

    resized_height, resized_width = smart_resize(
        image.height,
        image.width,
        factor=patch_size * merge_size,
        min_pixels=min_pixels,
        max_pixels=max_pixels,
    )

    image = image.resize((resized_width, resized_height), resample=Image.BICUBIC)
    image = np.array(image)

    # ... some creative liberties are taken here.
    return gray_tfm(image=image)["image"]

def create_pseudo_smart_resize(min_pixels, max_pixels, patch_size, merge_size):
    def _inner(image):
        with logger.begin_event("Pseudo smart image resizing", min_pixels=min_pixels, max_pixels=max_pixels, patch_size=patch_size, merge_size=merge_size) as ctx:
            after = pseudo_smart_resize(image, min_pixels, max_pixels, patch_size, merge_size)

            ctx.log("Done resizing image", before_shape=image.shape, after_shape=after.shape)
            return {
                "image": after,
            }
    return _inner
