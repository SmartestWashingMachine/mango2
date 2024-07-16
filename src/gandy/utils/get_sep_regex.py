import re

sep_splitter = re.compile(r"<SEP>|<TSOS>")


def get_last_sentence(s: str):
    return re.split(sep_splitter, s)[-1].strip()
