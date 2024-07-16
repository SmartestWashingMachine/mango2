from typing import List

SEP_TOKEN = "<SEP>"
TSOS_TOKEN = "<TSOS>"


def concat_text(text: str, context: List[str]):
    if len(context) == 0:
        return text
    return SEP_TOKEN.join(context) + TSOS_TOKEN + text


def pack_context(source_texts: List[str], n_context: int):
    new_sources: List[str] = []

    for idx, st in enumerate(source_texts):
        if idx == 0:
            new_sources.append(st)
            continue

        slice_idx = max(0, idx - max(n_context - 1, 0))
        others = source_texts[slice_idx:idx]
        concat = concat_text(st, others)

        new_sources.append(concat)

    return new_sources


def add_seps(texts: List[str]):
    # pack_context but assumes that the right amount of contextual sentences is already given, and the last sentence
    # is the current one.
    others = texts[:-1]
    cur = texts[-1]
    return concat_text(cur, others)


def merge_texts(source_texts: List[str], context_input: List[str]):
    source_texts = "".join(source_texts)
    return concat_text(source_texts, context_input)
