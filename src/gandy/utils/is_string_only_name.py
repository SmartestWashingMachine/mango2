from gandy.utils.clean_text_v2 import clean_text_vq
from fugashi import Tagger
from gandy.utils.fancy_logger import logger

class NameChecker():
    def __init__(self):
        self.translation_table_for_cleaning_names = str.maketrans('', '', ':\"-[]<>() ')
        self.tagger = None

    def is_string_only_name(self, s: str, threshold = 0.95):
        with logger.begin_event('Checking for name.') as ctx:
            if self.tagger is None:
                self.tagger = Tagger()

            s = clean_text_vq(s)
            s = s.translate(self.translation_table_for_cleaning_names).strip() # We don't care for spaces.
            total_s_length = len(s)

            if total_s_length <= 0:
                return False # Don't wanna divide by 0.

            good_length = 0
            for word in self.tagger(s):
                pos_main = word.feature[0]
                pos_sub1 = word.feature[1] if len(word.feature) > 1 else ''

                ctx.log(f"Token: {word.surface:<10} POS1: {pos_main:<10} POS2: {pos_sub1:<10}")

                # If there's a verb, it's probably not a name.
                if pos_main == '動詞':
                    return {
                        'is_name': False,
                        'cleaned': s,
                    }

                surf = word.surface

                if pos_main == '名詞':
                    # Nouns (possibly common or proper).
                    good_length += len(surf)
                elif pos_sub1 == '名詞的':
                    # Noun-likes (e.g: from suffixes).
                    good_length += len(surf)
                elif pos_main == '記号':
                    # Generics.
                    good_length += len(surf)
                elif pos_main == '助詞':
                    # Particles.
                    good_length += len(surf)
            
            return {
                'is_name': (good_length / total_s_length) >= threshold,
                'cleaned': s,
            }
    
name_checker = NameChecker()