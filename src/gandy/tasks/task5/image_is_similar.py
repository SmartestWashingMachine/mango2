from PIL import Image
from typing import List
import imagehash
from gandy.utils.fancy_logger import logger


# NOTE: dhash almost never works for full-sized images (even if grayscale). Maybe better luck with text region crops?
def image_is_similar(
    image: Image.Image, others: List, log_message, threshold=3, mode="image"
):
    with logger.begin_event(log_message, cached_images=len(others)) as ctx:
        # Returns None if no image is similar to the one given, or the first index otherwise.
        if mode == "image":
            transformed_image = imagehash.average_hash(image, hash_size=256)
        else:
            transformed_image = imagehash.dhash(image)

        closest_distance = 999999

        hamming_distance = None

        for idx, o in enumerate(others):
            if o is None:
                continue

            hamming_distance = transformed_image - o

            if hamming_distance <= closest_distance:
                closest_distance = hamming_distance

            if hamming_distance <= threshold:
                ctx.log("Done finding similar images", distance=hamming_distance)
                return idx, transformed_image

        ctx.log("Done finding similar images", closest_distance=hamming_distance)
        return None, transformed_image
