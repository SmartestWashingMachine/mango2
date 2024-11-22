from PIL import Image
from gandy.utils.speech_bubble import SpeechBubble
from typing import List
from gandy.utils.fancy_logger import logger
from gandy.tasks.task1.stitch_images_together import stack_vertically

def smart_vertical_merging(images: List[Image.Image], detect_in_chunk):
  stack_with_prev = [{ 'append_last': None, 'prepend_next': None, } for _ in images] # dict of { append_last, prepend_next FLOATS}
  for idx, img in enumerate(images):
    chunked_speech_bboxes: List[SpeechBubble] = detect_in_chunk(img)

    for box in chunked_speech_bboxes:
      if (box[1] <= (img.height * 0.06)) and idx > 0:
        # Is near the top of the tile.
        # Stack it with the previous image.

        # Get tops (Y1) of boxes that are BELOW this box.
        # E.g: If THIS box was at Y1 = 200, other "above" box was at Y1 = 100: This would return (100 - 200) = -100 which is FALSE.
        # E.g: If THIS was Y1 = 50, other "below" box was at Y1 = 75: This would return (75 - 50) = 25 which is TRUE.
        y1_asc = sorted(b[1] for b in chunked_speech_bboxes if (b[1] - box[1]) > 0)

        if len(y1_asc) > 0:
          y1_asc = y1_asc[0]
          portion = (box[3] + y1_asc) // 2 # Y2 (bottom) of this box plus half of the distance to the top of the next box below.
        else:
          portion = min(img.height - 1, box[3] + int(box[3] - box[1]))  

        cur_val = stack_with_prev[idx]['append_last']
        if cur_val is None:
          stack_with_prev[idx]['append_last'] = portion
        elif portion > cur_val:
          stack_with_prev[idx]['append_last'] = portion

      if (box[3] >= (img.height * 0.94)) and (idx + 1) < len(images):
        # Is near the bottom of the image.
        # Stack it with the next image.

        # Get bottoms (Y2) of boxes that are ABOVE this box.
        # E.g: If THIS was at Y2 = 100, other "above" was at Y2 = 50: Returns (50 - 100) = -50 which is TRUE.
        # E.g: If THIS was at Y2 = 20, other "below" was at Y2 = 25: Returns (25 - 20) = 5 which is FALSE.
        y2_asc = sorted(b[3] for b in chunked_speech_bboxes if (b[3] - box[3]) < 0)

        if len(y2_asc) > 0:
          y2_asc = y2_asc[-1] # [-1] maybe? use to be 0
          portion = (box[1] + y2_asc) // 2 # Y1 (top) of this box plus half of the distance to the bottom of the next box above.
        else:
          portion = max(1, box[1] - int(box[3] - box[1]))

        # We take the top part of this image and tell the next image to put it at the top of it.
        cur_val = stack_with_prev[idx]['prepend_next']
        if cur_val is None:
          stack_with_prev[idx]['prepend_next'] = portion
        elif portion < cur_val:
          stack_with_prev[idx]['prepend_next'] = portion

  new_images: List[Image.Image] = images
  for idx, (img, stk_portion) in enumerate(zip(images, stack_with_prev)):
    remaining_slice = img
    remaining_y1_crop = 0
    remaining_y2_crop = img.height

    if stk_portion['append_last'] is not None:
      top_slice = img.crop((0, 0, img.width, stk_portion['append_last']))
      new_images[idx - 1] = stack_vertically([new_images[idx - 1], top_slice])

      remaining_y1_crop = stk_portion['append_last']

    if stk_portion['prepend_next'] is not None:
      bottom_slice = img.crop((0, stk_portion['prepend_next'], img.width, img.height))
      new_images[idx + 1] = stack_vertically([bottom_slice, new_images[idx + 1]])

      remaining_y2_crop = stk_portion['prepend_next']

      stack_with_prev[idx + 1]['append_last'] = None

    remaining_slice = img.crop((0, remaining_y1_crop, img.width, remaining_y2_crop))
    new_images[idx] = remaining_slice

    #print(f'Old to new: {img.size} TO {remaining_slice.size}')
    logger.log_message(f'Mapped image', old_size=img.size, new_size=remaining_slice.size, **stk_portion)

  new_images = [im for im in new_images if im.height > 0]

  return new_images
