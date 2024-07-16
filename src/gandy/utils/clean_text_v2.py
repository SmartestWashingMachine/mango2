import unicodedata
import regex as re  # Important.
from sacremoses import MosesPunctNormalizer
from sys import maxunicode

# mpn = MosesPunctNormalizer("en", norm_quote_commas=False) # norm_quote_commas=True was on for training actually.
mpn = MosesPunctNormalizer("en")


def dedupe_punct(s: str):
    ri = r"([.?!]+[.?!])"
    ri_inner = r"[.?!]+([.?!])"
    split = re.split(ri, s)
    deduped = [re.sub(ri_inner, r"\1", x) if "..." not in x else x for x in split]
    return "".join(deduped)


def clean_text_v2(s: str, with_normalize=True):
    if with_normalize:
        sentence = mpn.normalize(s)
    else:
        sentence = s

    # deescape-special-chars
    new_sentence = re.sub(r"&bar;", "|", sentence)
    new_sentence = re.sub(r"&#124;", "|", new_sentence)
    new_sentence = re.sub(r"&lt;", "<", new_sentence)
    new_sentence = re.sub(r"&gt;", ">", new_sentence)
    new_sentence = re.sub(r"&bra;", "[", new_sentence)
    new_sentence = re.sub(r"&ket;", "]", new_sentence)
    new_sentence = re.sub(r"&quot;", '"', new_sentence)
    new_sentence = re.sub(r"&apos;", "'", new_sentence)
    new_sentence = re.sub(r"&#91;", "[", new_sentence)
    new_sentence = re.sub(r"&#93;", "]", new_sentence)
    new_sentence = re.sub(r"&amp;", "&", new_sentence)

    # remove-non-printing-char
    new_sentence = new_sentence.rstrip("\n")
    new_sentence = re.sub(r"\p{C}", " ", new_sentence)

    # replace-unicode-punctuation
    new_sentence = re.sub(r"，", ",", new_sentence)
    new_sentence = re.sub(r"。", ".", new_sentence)
    new_sentence = re.sub(r"、", ",", new_sentence)
    new_sentence = re.sub(r"”", '"', new_sentence)
    new_sentence = re.sub(r"“", '"', new_sentence)
    new_sentence = re.sub(r"∶", ":", new_sentence)
    new_sentence = re.sub(r"：", ":", new_sentence)
    new_sentence = re.sub(r"？", "?", new_sentence)
    new_sentence = re.sub(r"《", '"', new_sentence)
    new_sentence = re.sub(r"》", '"', new_sentence)
    new_sentence = re.sub(r"）", ")", new_sentence)
    new_sentence = re.sub(r"！", "!", new_sentence)
    new_sentence = re.sub(r"（", "(", new_sentence)
    new_sentence = re.sub(r"；", ";", new_sentence)
    new_sentence = re.sub(r"」", '"', new_sentence)
    new_sentence = re.sub(r"「", '"', new_sentence)
    new_sentence = re.sub(r"１", "1", new_sentence)
    new_sentence = re.sub(r"０", "0", new_sentence)
    new_sentence = re.sub(r"３", "3", new_sentence)
    new_sentence = re.sub(r"２", "2", new_sentence)
    new_sentence = re.sub(r"５", "5", new_sentence)
    new_sentence = re.sub(r"６", "6", new_sentence)
    new_sentence = re.sub(r"９", "9", new_sentence)
    new_sentence = re.sub(r"７", "7", new_sentence)
    new_sentence = re.sub(r"８", "8", new_sentence)
    new_sentence = re.sub(r"４", "4", new_sentence)
    new_sentence = re.sub(r"． *", ". ", new_sentence)
    new_sentence = re.sub(r"～", "~", new_sentence)
    new_sentence = re.sub(r"’", "'", new_sentence)
    new_sentence = re.sub(r"…", "...", new_sentence)
    new_sentence = re.sub(r"━", "-", new_sentence)
    new_sentence = re.sub(r"—", "-", new_sentence)
    new_sentence = re.sub(r"〈", "<", new_sentence)
    new_sentence = re.sub(r"〉", ">", new_sentence)
    new_sentence = re.sub(r"【", "[", new_sentence)
    new_sentence = re.sub(r"】", "]", new_sentence)
    new_sentence = re.sub(r"％", "%", new_sentence)

    new_sentence = new_sentence.replace("\u200b", "")
    new_sentence = new_sentence.replace("\ufeff", "")
    new_sentence = new_sentence.replace("\u2060", "")
    new_sentence = new_sentence.replace("\u3000", "")

    new_sentence = unicodedata.normalize("NFKC", new_sentence)

    # This section handles errors possibly generated during the OCR process.
    new_sentence = dedupe_punct(new_sentence)

    return new_sentence


mpn_vq = MosesPunctNormalizer(lang="en")
mpn_vq.substitutions = [(re.compile(r), sub) for r, sub in mpn.substitutions]


def get_non_printing_char_replacer(replace_by: str = " "):
    non_printable_map = {
        ord(c): replace_by
        for c in (chr(i) for i in range(maxunicode + 1))
        if unicodedata.category(c) in {"C", "Cc", "Cf", "Cs", "Co", "Cn"}
    }

    def replace_non_printing_char(line) -> str:
        return line.translate(non_printable_map)

    return replace_non_printing_char


replace_nonprint = get_non_printing_char_replacer(" ")


def clean_text_vq(s: str, with_v2=True):
    clean = mpn.normalize(s)
    clean = replace_nonprint(clean)
    if with_v2:
        clean = clean_text_v2(s, False)
    return clean
