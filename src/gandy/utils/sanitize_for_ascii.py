from unidecode import unidecode
import regex as re

def sanitize_for_ascii(s: str):
    # unidecode transliterates these as the literal word "hearts". Not very user-friendly.
    s = re.sub(r'[♥♡❤]', ' ', s)

    return unidecode(s, replace_str=" ").replace("  ", " ").strip()
