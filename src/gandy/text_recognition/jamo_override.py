# I've had great trouble making an accurate Korean OCR model - I suspect one issue being the rare tokens (rarely seen Hangul).
# This paper has an interesting way to fix that rare token issue (https://vip.snu.ac.kr/viplab/courses/mlvu_2025_1/projects/01.pdf)
# If the link is down, the title is "Jamo Is All You Need: Enhancing Korean OCR with Style Tags" - yeah yeah I know the "X is all you need" title makes it sound shady as sheep. Ignore the part about the style tags - we only care about the decomposition part.
# In theory, similar-ish decomposition logic could be applied to other languages too, 
# but my experiences fine-tuning Chinese & Japanese models went smoothly, perhaps because VLLM's already have a lot of pretrained knowledge regarding those two languages (especially Chinese).

# The jamo logic here is not mine. See: https://github.com/jonghwanhyeon/hangul-jamo
# Had trouble pip installing, so just using the code instead.

# Reference: http://www.unicode.org/versions/Unicode8.0.0/ch03.pdf#G24646

BASE_OF_SYLLABLES = 0xAC00

BASE_OF_LEADING_CONSONANTS = 0x1100
BASE_OF_VOWELS = 0x1161
BASE_OF_TRAILING_CONSONANTS = 0x11A7 #  one less than the beginning of the range of trailing consonants (0x11A8)

NUMBER_OF_LEADING_CONSONANTS = 19
NUMBER_OF_VOWELS = 21
NUMBER_OF_TRAILING_CONSONANTS = 28 # one more than the number of trailing consonants

NUMBER_OF_SYLLABLES_FOR_EACH_LEADING_CONSONANT = NUMBER_OF_VOWELS * NUMBER_OF_TRAILING_CONSONANTS # 가-깋 + 1
NUMBER_OF_SYLLABLES = NUMBER_OF_LEADING_CONSONANTS * NUMBER_OF_SYLLABLES_FOR_EACH_LEADING_CONSONANT

LEADING_CONSONANTS = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
INDEX_BY_LEADING_CONSONANT = { leading_consonant: index for index, leading_consonant in enumerate(LEADING_CONSONANTS) }

VOWELS = ['ㅏ', 'ㅐ', 'ㅑ', 'ㅒ', 'ㅓ', 'ㅔ', 'ㅕ', 'ㅖ', 'ㅗ', 'ㅘ', 'ㅙ', 'ㅚ', 'ㅛ', 'ㅜ', 'ㅝ', 'ㅞ', 'ㅟ', 'ㅠ', 'ㅡ', 'ㅢ', 'ㅣ']
INDEX_BY_VOWEL = { vowel: index for index, vowel in enumerate(VOWELS) }

TRAILING_CONSONANTS = [None, 'ㄱ', 'ㄲ', 'ㄳ', 'ㄴ', 'ㄵ', 'ㄶ', 'ㄷ', 'ㄹ', 'ㄺ', 'ㄻ', 'ㄼ', 'ㄽ', 'ㄾ', 'ㄿ', 'ㅀ', 'ㅁ', 'ㅂ', 'ㅄ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
INDEX_BY_TRAILING_CONSONANT = { trailing_consonant: index for index, trailing_consonant in enumerate(TRAILING_CONSONANTS) }

from itertools import chain, tee
from typing import Any, Iterator, Optional, Tuple


def consume(iterator: Iterator, n: int, default: Optional[Any] = None) -> Iterator:
    for _ in range(n):
        next(iterator, default)

def ngram(text: str, n: int, pad_left: bool = False, pad_right: bool = False) -> Iterator[Tuple[Optional[str], ...]]:
    if pad_left:
        text = chain([None] * (n - 1), text)
    if pad_right:
        text = chain(text, [None] * (n - 1))

    iterators = tee(text, n)
    for index, iterator in enumerate(iterators):
        consume(iterator, index, default=None)

    return zip(*iterators)

# Reference: http://www.unicode.org/versions/Unicode8.0.0/ch03.pdf#G24646

from typing import NamedTuple, Optional


class Syllable(NamedTuple):
    leading_consonant: str
    vowel: str
    trailing_consonant: Optional[str]


def is_syllable(syllable: str) -> bool:
    index_of_syllable = ord(syllable) - BASE_OF_SYLLABLES
    return 0 <= index_of_syllable < NUMBER_OF_SYLLABLES

def is_jamo_character(character: str) -> bool:
    return (character in LEADING_CONSONANTS) or (character in VOWELS) or (character in TRAILING_CONSONANTS)

def compose_jamo_characters(leading_consonant: str, vowel: str, trailing_consonant: Optional[str] = None) -> str:
    try:
        index_of_leading_consonant_and_vowel = (INDEX_BY_LEADING_CONSONANT[leading_consonant] * NUMBER_OF_SYLLABLES_FOR_EACH_LEADING_CONSONANT) \
                                               + (INDEX_BY_VOWEL[vowel] * NUMBER_OF_TRAILING_CONSONANTS)
        index_of_syllable = index_of_leading_consonant_and_vowel + INDEX_BY_TRAILING_CONSONANT[trailing_consonant]
    except KeyError:
        raise ValueError('given jamo character contains invalid Hangul jamo character') from None

    return chr(BASE_OF_SYLLABLES + index_of_syllable)

def decompose_syllable(syllable: str) -> Syllable:
    if not is_syllable(syllable):
        raise ValueError('`syllable` is not a Hangul syllable')

    index_of_syllable = ord(syllable) - BASE_OF_SYLLABLES

    index_of_leading_consonant = index_of_syllable // NUMBER_OF_SYLLABLES_FOR_EACH_LEADING_CONSONANT
    index_of_vowel = (index_of_syllable % NUMBER_OF_SYLLABLES_FOR_EACH_LEADING_CONSONANT) // NUMBER_OF_TRAILING_CONSONANTS
    index_of_trailing_consonant = index_of_syllable % NUMBER_OF_TRAILING_CONSONANTS

    return (
        LEADING_CONSONANTS[index_of_leading_consonant],
        VOWELS[index_of_vowel],
        TRAILING_CONSONANTS[index_of_trailing_consonant]
    )

def compose(text: str) -> str:
    output = ''

    iterator = ngram(text, n=4, pad_right=True)
    for first, second, third, fourth in iterator:
        if (first in LEADING_CONSONANTS) and (second in VOWELS) and (third in LEADING_CONSONANTS) and (fourth in VOWELS):
            output += compose_jamo_characters(first, second)
            consume(iterator, 1)
        elif (first in LEADING_CONSONANTS) and (second in VOWELS) and (third in TRAILING_CONSONANTS):
            output += compose_jamo_characters(first, second, third)
            consume(iterator, 2)
        elif (first in LEADING_CONSONANTS) and (second in VOWELS):
            output += compose_jamo_characters(first, second)
            consume(iterator, 1)
        else:
            output += first

    return output

def decompose(text: str) -> str:
    output = ''

    for character in text:
        if is_syllable(character):
            leading_consonant, vowel, trailing_consonant = decompose_syllable(character)
            output += leading_consonant
            output += vowel
            output += trailing_consonant if trailing_consonant is not None else ''
        else:
            output += character

    return output

class JamoOverride():
    @staticmethod
    def postprocess(text: str):
        return compose(text)