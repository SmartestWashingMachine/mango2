from gandy.utils.clean_text_v2 import clean_text_vq


def set_lang_as_j(tokenizer):
    tokenizer.src_lang = "jpn_Jpan"


def set_lang_as_k(tokenizer):
    tokenizer.src_lang = "kor_Hang"

def set_lang_as_c(tokenizer):
    tokenizer.src_lang = "zho_Hans"


def prepend_qual(s: str):
    # A little history: On older models, two Q9 tags worked better than one.
    # Why two Q9? I have no idea why, but it somehow improved the quality further! (3 no effect?)
    # No - there is no training data with two Q9s. So WTF is going on?
    # It must be something in the water.

    return f"<Q9>{clean_text_vq(s)}"

def prepend_qual_mad(s: str):
    return f"<Q9>{clean_text_vq(s)}"

honorifics = { '君', 'はん', '様', 'さま', 'さん', 'ちゃん', 'たん', 'くん', '先生', 'せんせい', '先輩', 'せんぱい', }
def prepend_mad_qual_ja(s: str):
    if any(h in s for h in honorifics):
        # <AH> is only used for J-Mad. It encourages the model to use more "anime" honorifics.
        return f"<2en> <AH>{prepend_qual_mad(s)}"

    return f"<2en> {prepend_qual_mad(s)}"

def prepend_mad_qual_generic(s: str):
    return f"<2en> {prepend_qual_mad(s)}"

def fix_quotes(s: str):
    if s.startswith('"') and s.count('"') == 1:
        s = s + '"'
    return s

def remove_unnecessary_eng_tokens(s: str):
    s = s.replace("eng_Latn", "").replace(
        "<TSOS>",
        "",
    )

    # Had to do this due to a data clean/filter error in our new dataset.
    s = s.replace('$1', '...')

    # MT model sometimes misplaces quotes.
    s = fix_quotes(s.strip())

    return s

def remove_unnecessary_eng_tokens_mad(s: str):
    return s.replace("<unk>", "").replace(
        "<TSOS>",
        "",
    ).strip()
