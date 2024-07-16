from string import ascii_letters


def compute_max_chars_per_line(font, box_width: float):
    """
    Calculate the max number of characters that can fit in a single line for a speech bubble.
    """
    avg_char_width = sum((font.getsize(char)[0]) for char in ascii_letters) / len(
        ascii_letters
    )

    candidate_max_char_count = max(
        1, int(box_width / avg_char_width)
    )  # Max true chars before it overflows the width. AKA chars per line.

    return candidate_max_char_count
