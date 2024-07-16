"""
Algorithm details:

(-1) Check to see if the total area of all of the text boxes is large compared to the image area. If so, cut down the font size even further.
    This helps pages with lots of text. Less clutter. Note that we ignore any potential overlap between text boxes when computing area - keep it simple!

(0) Aspect ratio less than 1? Expand it. REJECT IF: overflowing image (any direction) OR text overflows. ELSE repeat if text overlaps box.
(Step 0 success MAY stop step 1 from activating - see box_is_bad)


(When each step is done, one last sanity check is performed to ensure the text does not overflow the image on ANY direction. Failures are treated as normal REJECT cases)

(1) Expand to right. REJECT IF: overflowing right of image OR overlaps box on right. ELSE IF: Overlap another OR text overflows?
    (2) Expand to left. REJECT IF: overflowing left of image OR overlaps box on left. ELSE IF: Overlap another OR text flows?
        (3) Expand to right and push any offending. REJECT IF: overflowing right of image. ELSE IF: Overlap another that's on the right OR text overflows?
            (4) Expand to left and push any offending - left or right alike. REJECT IF: text overflows

(5) Expand down. REJECT IF: overflowing down of image OR overlaps box on down. ELSE IF: Overlapping another OR textoverflows?
    (6) Expand up. REJECT IF: overflowing up of image OR overlaps box on up. ELSE IF: overlapping another OR textoverflows?
        (7) !!! NOT IMPLEMENTED !!!: Expand DOWN and push any offending. Overlapping another that's below? R.I.P

(8) Still bad? OH NO! This can happen when overlapping/overflowing in the x AND y axis. As a last ditch effort, try to cut the font size for THIS BOX ONLY by 40% and repeat. Can not repeat again. 

Each branch can repeat itself. So if (1) fails but (2) does not, repeat (2). If (3) does not fail, then repeat from (3).
A branch is FULLY complete when it no longer overlaps any other boxes or overflows the image.

NOTE: We also consider a box to overlap another box if it's "too close" to another box. (See CLOSE_FACTOR)
NOTE: This algo is poorly optimized.


"""

# If True, expansion uses the bounding box size. If False, expansion uses the image size.
# This profile was pretty good, but slow.
# EXPAND_RELATIVE = True
# EXPAND_FACTOR = 0.02

EXPAND_RELATIVE = False
EXPAND_FACTOR = 0.015

# NEAR_FACTOR is used if the two speech boxes were originally close to each other. Otherwise CLOSE_FACTOR is used.
# TODO: Near_factor is not implemented yet.
# NEAR_FACTOR = 0.001

CLOSE_FACTOR = 0.001  # If another box is within 3% of the img's width to another box.

CLUTTER_THRESHOLD = 0.18  # If the text area is 65% of the image area, chop down the font size even further!
