from math import floor
import regex as re

punctuation_chars = [
    "，",
    "。",
    "、",
    "”",
    "．",
    "」",
    "）",
    "？",
    "！",
    "】",
    '"',
    ".",
    "!",
    "?",
    ",",
    ")",
]
norm_regex = r"，|。|、|”|．|」|）|？|！|】|\"|\.|!|\?|,|\)"


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


def a_is_close_substring_of_b(a: str, b: str, matching_threshold=0.7):
    """
    Returns True if A is a substring or relatively close to being a substring of the beginning of B.
    """
    if len(a) >= len(b) or len(a) == 0:
        # A cannot be a substring of B if A is longer than B or A is empty!
        return False

    if any(a.endswith(p) for p in punctuation_chars):
        # If A ends with a punctuation character, we assume that A is not a substring of B.
        return False

    a_norm = re.sub(norm_regex, "", a)
    if len(a_norm) == 0:
        return False

    threshold_chars = max(1, floor(len(a_norm) * matching_threshold))
    x = 1.75
    b_beginning = slice_b(
        b, floor(len(a_norm) * x)
    )  # We look in X times the length of A's characters in the beginning of B for similarities.

    return chars_in_b(a_norm, b_beginning) >= threshold_chars
