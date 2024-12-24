from typing import List

SEP_TOKEN = "<SEP>"
TSOS_TOKEN = "<TSOS>"


def concat_text(text: str, context: List[str]):
    if len(context) == 0:
        return text
    return SEP_TOKEN.join(context) + TSOS_TOKEN + text


# If ignore_single_words_in_context is on (from image translations):
# texts with only one word are not used as context for other texts.
# texts with only one word can still use context (that have more than one word still).
def pack_context(source_texts: List[str], n_context: int, ignore_single_words_in_context = False):
    new_sources: List[str] = []

    contexts_to_use: List[str] = []
    for idx, st in enumerate(source_texts):
        if len(contexts_to_use) > 0:
            concat = concat_text(st, contexts_to_use)
        else:
            concat = st

        new_sources.append(concat)

        if ignore_single_words_in_context:
            if len(st.split(' ')) > 1:
                contexts_to_use.append(st)
        else:
            contexts_to_use.append(st)

        if len(contexts_to_use) > 0 and len(contexts_to_use) > (n_context - 1):
            contexts_to_use = contexts_to_use[1:]

    return new_sources

# Similar to pack_context but for exclusive use in task5 (video translations).
# It takes into account "duplicate" texts on neighboring frames before adding context.
def pack_context_dedupe(source_texts: List[str], n_context: int, ignore_single_words_in_context = False):
    new_sources: List[str] = []

    prev_source = ""
    concat = None

    contexts_to_use: List[str] = []
    for st in source_texts:
        if prev_source == st and concat is not None:
            new_sources.append(concat)
            continue # Don't push further to context as we're just reusing the previously formed concatenated text.

        if len(contexts_to_use) > 0:
            concat = concat_text(st, contexts_to_use)
        else:
            concat = st

        new_sources.append(concat)

        if ignore_single_words_in_context:
            if len(st.split(' ')) > 1:
                contexts_to_use.append(st)
        else:
            contexts_to_use.append(st)

        if len(contexts_to_use) > 0 and len(contexts_to_use) > (n_context - 1):
            contexts_to_use = contexts_to_use[1:]

        # No ctx here.
        prev_source = st

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
