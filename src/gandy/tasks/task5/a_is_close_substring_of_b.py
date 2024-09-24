from math import floor
import regex as re

# Since source texts passed here are first cleaned with clean_text_vq, we only care about the cleaned characters.
punctuation_chars = [
    "]",
    '"',
    ".",
    "!",
    "?",
    ",",
    ")",
    "(", # Hmmmm do we need this one?
]

norm_regex = r"]|\"|\.|!|\?|,|\)|ー|-|,|\.|\"|'"


def slice_b(b: str, end: int):
    if end >= len(b):
        return b
    else:
        return b[:end]


def char_count(t: str):
    data = {}  # key = character string. value = number of times it's in the string.
    for char in t:
        if char not in data:
            data[char] = 0

        data[char] += 1

    return data


def chars_in_b(a: str, b: str):
    """
    aaab
    aabbc

    it should be 2a, 1b == 3

    aabb
    aaaabbb

    it should be 2a, 2b == 4
    """

    matching_count = 0

    # a_char_cnt = char_count(a)
    b_char_cnt = char_count(b)

    for a_char in a:
        if a_char in b_char_cnt:
            matching_count += 1

            # Update counter.
            b_char_cnt[a_char] -= 1
            if b_char_cnt[a_char] <= 0:
                del b_char_cnt[a_char]

    return matching_count

def a_is_close_in_len_to_b(a: str, b: str, tol = 1.3):
    return int(len(a) * tol) >= len(b)

def a_is_close_substring_of_b(a: str, b: str, matching_threshold=0.7, a_after_b = False):
    """
    Returns True if A is a substring or relatively close to being a substring of the beginning of B.
    """
    a_norm = re.sub(norm_regex, "", a)
    b_norm = re.sub(norm_regex, "", b)

    if a_after_b:
        if not a_is_close_in_len_to_b(a_norm, b_norm):
            return False

    if len(a_norm) > len(b_norm) or len(a) == 0:
        # A cannot be a substring of B if A is longer than B or A is empty!
        return False

    if (
        (a.replace(')', '"')[-1] != b.replace(')', '"')[-1]) # Sometimes the OCR model confuses ending quotation marks with parenthesis.
        and (a.replace('"', '')[-1] != b.replace('"', '')[-1]) # Rarely the OCR model adds an additional unnecessary quotation mark at the end. NOTE: Do we still need this check?
        and any(a.endswith(p) for p in punctuation_chars)):
        # Ultimately: If A ends with a punctuation character, and it is not the same as B, we assume that A is not a substring of B.
        return False

    if len(a_norm) == 0:
        return False

    threshold_chars = max(1, floor(len(a_norm) * matching_threshold))
    x = 1.75
    b_beginning = slice_b(
        b, floor(len(a_norm) * x)
    )  # We look in X times the length of A's characters in the beginning of B for similarities.

    return chars_in_b(a_norm, b_beginning) >= threshold_chars
