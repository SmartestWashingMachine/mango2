from typing import List, Dict
import regex as re
from gandy.utils.fancy_logger import logger


def replace_many(s: str, terms: List[Dict], ctx):
    if ctx is not None:
        if len(terms) > 0:
            ctx.log("Mapping text", pre_text=s, n_terms=len(terms))
        else:
            ctx.log("No terms - skipping")

    for t in terms:
        s = re.sub(rf'{t["original"]}', rf'{t["replacement"]}', s)
    return s

def replace_terms(sentences: List[str], terms: List[Dict], on_side: str):
    # on_side here is just for logging.

    with logger.begin_event("Replacing terms", on_side=on_side) as ctx:
        new_texts = [replace_many(s, terms, ctx) for s in sentences]
    return new_texts
