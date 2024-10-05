from PIL import Image
from typing import List
from gandy.image_redrawing.smarter.checks import text_intersects_on_direction, text_overflows
from gandy.image_redrawing.smarter.text_box import TextBox
from gandy.image_redrawing.smarter.image_fonts import print_spam

# TODO: Refactor.
def _midp(x: TextBox):
    return ((x.x1 + x.x2) / 2, (x.y1 + x.y2) / 2)

def _dist_1d(a, b):
    return abs(a - b)

def _boxes_nearby(tb: TextBox, cb: TextBox, image: Image.Image):

    tb_mid = _midp(tb)
    cb_mid = _midp(cb)
    dist_thr = 0.2
    return _dist_1d(tb_mid[0], cb_mid[0]) <= (image.width * dist_thr) and _dist_1d(tb_mid[1], cb_mid[1]) <= (image.height * dist_thr)

def generate_and_check_centered_box(tb: TextBox, others: List[TextBox], opt: List[float], image: Image.Image, x_mult = 1.0, y_mult = 1.0, mult_mult = 0.9, iterations_left = 5):
    centered_box = TextBox.shift_from(tb, offset_pct=opt, is_abs=True)

    if text_overflows(centered_box, image, direction="lrud"):
        # Sad. Continue to next centered box candidate.
        return {
            "box": None,
            "error": "overflows LRUD",
        }

    intersecting_directions = text_intersects_on_direction(centered_box, others, image, direction_to_check="lrud", only_check=True, with_margin=False)
    if intersecting_directions == "":
        # Success case!
        return {
            "box": centered_box,
            "error": None,
        }

    if ("l" in intersecting_directions and "r" in intersecting_directions) or ("d" in intersecting_directions and "u" in intersecting_directions):
        return {
            "box": None,
            "error": f"intersects {intersecting_directions}",
        }

    time_left = (iterations_left - 1)

    if time_left <= 0:
        return {
            "box": None,
            "error": f"no time left",
        }

    if "l" in intersecting_directions or "r" in intersecting_directions:
        print_spam('REDUCING X-ADD')
        x_mult *= mult_mult

    if "u" in intersecting_directions or "d" in intersecting_directions:
        print_spam('REDUCING Y-ADD')
        y_mult *= mult_mult

    new_opt = [opt[0] * x_mult, opt[1] * y_mult, opt[2] * x_mult, opt[3] * y_mult]

    return generate_and_check_centered_box(tb, others, new_opt, image, x_mult, y_mult, mult_mult, iterations_left=time_left)

def try_center_boxes(image: Image.Image, text_boxes: List[TextBox]):

    new_boxes: List[TextBox] = []
    for idx in range(len(text_boxes)):
        tb = text_boxes[idx]

        tb_container_text_box = tb.metadata['container_text_box']
        tb_container_box = tb.metadata['container_box']

        ### others = text_boxes[:idx] + text_boxes[idx + 1:]
        others = new_boxes + text_boxes[idx + 1:]

        # If the box wasn't moved too far from its original location, try to vertically center it.
        # We use container_text_boxes to determine if they are nearby, as the drawn text area will usually be smaller than the entire detected text area.
        if _boxes_nearby(tb, tb_container_text_box, image) and not tb.metadata.get('was_centered', False):
            print_spam(f'Centering box: {tb}')

            x_add = _midp(tb_container_box)[0] - _midp(tb)[0]
            y_add = _midp(tb_container_box)[1] - _midp(tb)[1]

            possible_options = [
                [x_add, y_add, 0, 0],
                [0, y_add, 0, 0],
                [x_add, 0, 0, 0],
            ]

            opt_chosen = False
            for opt in possible_options:
                result = generate_and_check_centered_box(tb, others, opt, image, iterations_left=5)

                if result['error'] is None:
                    # In Smarter redraw, we call try_center_boxes twice.
                    # But we don't want to re-center boxes twice, that makes things weird(er).
                    # So we mark successfully processed boxes here so that they don't get re-processed.
                    result['box'].metadata['was_centered'] = True

                    new_boxes.append(result['box'])
                    opt_chosen = True
                    print_spam(f'Centered box initial / success:')
                    print_spam(tb)
                    print_spam(result["box"])

                    break # Success!
                else:
                    print_spam(f'Going to next possible option because of failure with reason "{result["error"]}"')

            if not opt_chosen:
                new_boxes.append(tb)
        else:
            new_boxes.append(tb)

    return new_boxes