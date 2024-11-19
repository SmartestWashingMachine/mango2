from PIL import Image
from gandy.utils.filter_out_overlapping_bboxes import box_b_in_box_a_thr
from gandy.utils.speech_bubble import SpeechBubble
from gandy.state.debug_state import debug_state
from typing import List
from math import ceil
import os
from uuid import uuid4
from gandy.utils.fancy_logger import logger

class TiledBubble():
  bubble: SpeechBubble

def boxes_near_edges(b, o):
  b_tmp = b[-1]
  o_tmp = o[-1]

  if b_tmp['merged_once'] or o_tmp['merged_once']:
    return False

  return (b_tmp['is_near_x'] + o_tmp['is_near_x'] == 0) or (o_tmp['is_near_y'] + o_tmp['is_near_y'] == 0)

def _midp(box: SpeechBubble):
  return (box[2] - box[0], box[3] - box[1])

def boxes_close(b, o, chunk_x, chunk_y):
  b_midp = _midp(b)
  o_midp = _midp(o)

  x_thr = y_thr = 0.2

  return (abs(b_midp[0] - o_midp[0]) <= (chunk_x * x_thr)) and (abs(b_midp[1] - o_midp[1]) <= (chunk_y * y_thr))

def box_area(b: SpeechBubble):
  return (b[3] - b[1]) * (b[2] - b[0])

def merge_and_validate(speech_bboxes: List[SpeechBubble], idx: int, condition):
  # Merge a box and return True if a box was merged.

  b = speech_bboxes[idx]

  for other_idx in range(len(speech_bboxes)):
    if idx == other_idx:
      continue

    o = speech_bboxes[other_idx]

    # Merge!
    if condition(b, o):
      # Merge this box...
      speech_bboxes[idx] = [min(b[0], o[0]), min(b[1], o[1]), max(b[2], o[2]), max(b[3], o[3]), { 'merged_once': True, }]
      # Then delete the other...
      speech_bboxes = speech_bboxes[:other_idx] + speech_bboxes[(other_idx + 1):]

      return speech_bboxes, True # A box was merged.
    
  return speech_bboxes, False

def detect_image_chunks(img: Image.Image, tile_width: int, tile_height: int, detect_in_chunk):
  # tile_width/tile_height = int from [0, 100]. 50 would mean 50%.
  # Returns a list of split image chunks.
  # NOTE: Ensure this does NOT run on tile width 100 and height 100.

  chunk_x = ceil(img.width * (tile_width / 100))
  chunk_y = ceil(img.height * (tile_height / 100))

  overlap_frac = 0.2
  overlap_x = ceil(chunk_x * overlap_frac)
  overlap_y = ceil(chunk_y * overlap_frac)

  speech_bboxes: List[SpeechBubble] = []

  if debug_state.debug:
    os.makedirs('./debugdumps/tiles', exist_ok=True)
    debug_id = uuid4().hex
    logger.debug_message('Dumping tiles', tiles_parent_id=debug_id, category='tiles_dump')

  # How do we overlap?
  for y in range(0, img.height, chunk_y):
    for x in range(0, img.width, chunk_x):
      # No overlap?: img_tile = img.crop((x, y, x + chunk_x, y + chunk_y))
      # Hmm, not future proof: img_tile = img.crop((x, y, x + chunk_x + overlap_x, y + chunk_y + overlap_y))

      # Safe guard. If the tile would be too small don't even bother.
      if (img.height - y) <= 32 or (img.width - x) <= 32:
        continue

      start_x = x - overlap_x
      start_y = y - overlap_y
      end_x = x + chunk_x + overlap_x
      end_y = y + chunk_y + overlap_y

      crop_x1 = max(start_x, 0)
      crop_y1 = max(start_y, 0)
      crop_x2 = min(end_x, img.width)
      crop_y2 = min(end_y, img.height)
      img_tile = img.crop((crop_x1, crop_y1, crop_x2, crop_y2))

      if debug_state.debug:
        img_tile.save(f'./debugdumps/tiles/{debug_id}__{x}_{y}.png')

      chunked_speech_bboxes: List[SpeechBubble] = detect_in_chunk(img_tile)

      # Offset.
      # chunked_speech_bboxes = [[s[0] + start_x, s[1] + start_y, s[2] + start_x, s[3] + start_y] for s in chunked_speech_bboxes]
      chunked_speech_bboxes = [[s[0] + crop_x1, s[1] + crop_y1, s[2] + crop_x1, s[3] + crop_y1] for s in chunked_speech_bboxes]
      speech_bboxes.extend(chunked_speech_bboxes)

      # Process each img; get speech_bboxes.


  # Iterate over every box.
  # If one box is touching the edge of a tile, and is near another box, merge them.
  failsafe_max_n = 0
  while failsafe_max_n < 4000:
    failsafe_max_n += 1
    can_break = True

    for idx in range(len(speech_bboxes)):
      b = speech_bboxes[idx]

      is_near_x = -2
      is_near_y = -2

      if ((b[1] / (chunk_y + overlap_y)) % 1) <= 0.1:
        # Is near the top of the tile.
        is_near_y = 1
      elif ((b[3] / (chunk_y + overlap_y)) % 1) >= 0.9:
        # Is near the bottom of the tile.
        is_near_y = -1

      if ((b[0] / (chunk_x + overlap_x)) % 1) <= 0.1:
        # Is near the left of the tile.
        is_near_x = 1
      elif ((b[2] / (chunk_x + overlap_x)) % 1) >= 0.9:
        is_near_x = -1

      #Each tmp_data item is a dict of { is_near_x STR|NONE and is_near_y STR|NONE }
      tmp_data = { 'is_near_x': is_near_x, 'is_near_y': is_near_y, 'merged_once': False, }
      speech_bboxes = [[*s[0:4], tmp_data] for s in speech_bboxes]

    for idx in range(len(speech_bboxes)):
      b = speech_bboxes[idx]

      # If the box is near the top/bottom, find a box nearby in the Y dimension.
      # If the box is near the left/right, find a box nearby in the X dimension.
      # Actually, for now: If a box is near an edge, just find a nearby box that's also near the edge.
      speech_bboxes, did_merge = merge_and_validate(
        speech_bboxes, idx,
        condition=lambda b, o: boxes_near_edges(b, o) and boxes_close(b, o, chunk_x, chunk_y)
      )
      if did_merge:
        can_break = False
        break

    if can_break:
      break

  # iterate over every box.
  # if box overlaps another, merge it, removing it from the list before repeating.
  failsafe_max_n = 0
  while failsafe_max_n < 4000:
    failsafe_max_n += 1
    can_break = True

    for idx in range(len(speech_bboxes)):
      speech_bboxes, did_merge = merge_and_validate(speech_bboxes, idx, condition=lambda b, o: box_b_in_box_a_thr(box_a=b, box_b=o) >= 0.3)
      if did_merge:
        can_break = False
        break

    if can_break:
      break


  speech_bboxes = [s[:-1] for s in speech_bboxes] # Remove tmp_data.

  return speech_bboxes
  
