from gandy.utils.clean_text_v2 import clean_text_vq


def set_lang_as_j(tokenizer):
    tokenizer.src_lang = "jpn_Jpan"


def set_lang_as_k(tokenizer):
    tokenizer.src_lang = "kor_Hang"

def set_lang_as_c(tokenizer):
    tokenizer.src_lang = "zho_Hans"


def prepend_qual(s: str):
    return f"<Q9>{clean_text_vq(s)}"

def prepend_mad_qual(s: str):
    return f"<2en> {prepend_qual(s)}"


def remove_unnecessary_eng_tokens(s: str):
    return s.replace("eng_Latn", "").replace(
        "<TSOS>",
        "",
    )

def remove_unnecessary_eng_tokens_mad(s: str):
    return s.replace("<unk>", "").replace(
        "<TSOS>",
        "",
    ).strip()
