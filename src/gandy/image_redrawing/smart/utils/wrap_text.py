import textwrap


def wrap_text(text, max_chars_per_line):
    """
    Given a piece of text, breaks it according to the max_chars_per_line for use in PIL.
    """
    w = textwrap.TextWrapper(
        width=max_chars_per_line, break_long_words=False, break_on_hyphens=False
    )
    wrapped_text = w.fill(text)

    return wrapped_text
