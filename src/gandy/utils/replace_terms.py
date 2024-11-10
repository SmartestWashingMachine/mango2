from typing import List, Dict
import regex as re
from gandy.utils.fancy_logger import logger

def replace_from(t, s: str):
    # t = term dict. s = string to replace
    return re.sub(rf'{t["original"]}', rf'{t["replacement"]}', s)

def replace_many(s: str, terms: List[Dict], ctx, split_context = False):
    if ctx is not None:
        if len(terms) > 0:
            ctx.log("Mapping text", pre_text=s, n_terms=len(terms))
        else:
            ctx.log("No terms - skipping")

    for t in terms:
        if split_context:
            # Keep the SEP characters in the split.
            # See: https://stackoverflow.com/questions/2136556/in-python-how-do-i-split-a-string-and-keep-the-separators
            all_s: List[str] = re.split(r"(<SEP>|<TSOS>)", s)
            s = ""

            # Replace the sentence and the contexts separately.
            for s_piece in all_s:
                if not (s_piece == '<SEP>' or s_piece == '<TSOS>'):
                    s_piece = replace_from(t, s_piece)

                s += s_piece         
        else:
            s = replace_from(t, s)
    return s

def replace_terms(sentences: List[str], terms: List[Dict], on_side: str, split_context = False):
    # on_side here is just for logging.

    with logger.begin_event("Replacing terms", on_side=on_side) as ctx:
        new_texts = [replace_many(s, terms, ctx, split_context=split_context) for s in sentences]
    return new_texts
