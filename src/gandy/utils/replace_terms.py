from typing import List, Dict
import regex as re
from gandy.utils.fancy_logger import logger


def replace_many(s: str, terms: List[Dict], on_side: str, ctx):
    ctx.log("Mapping text", pre_text=s, n_terms=len(terms))

    for t in terms:
        if t.get("enabled", False) and t["onSide"] == on_side:
            s = re.sub(rf'{t["original"]}', rf'{t["replacement"]}', s)
    return s


# on_side == "source" || "target"
def replace_terms(sentences: List[str], terms: List[Dict], on_side: str):
    with logger.begin_event("Replacing terms", on_side=on_side) as ctx:
        new_texts = [replace_many(s, terms, on_side, ctx) for s in sentences]
    return new_texts
