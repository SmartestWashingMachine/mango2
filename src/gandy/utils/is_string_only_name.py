from gandy.utils.clean_text_v2 import clean_text_vq
from fugashi import Tagger
from gandy.utils.fancy_logger import logger
from gandy.utils.try_print import try_print

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

            if total_s_length <= 0 or total_s_length >= 10:
                return False # Don't wanna divide by 0 if total_s_length == 0. And long strings are probably not names.

            good_length = 0
            for word in self.tagger(s):
                pos_main = word.feature[0]
                pos_sub1 = word.feature[1] if len(word.feature) > 1 else ''

                # Fudging Eliot can't log special unicode characters because OF COURSE IT CAN'T. WHY DOES A LOGGER HAVE LOGGING BUGS.
                # IT'S LIKE THEY DON'T WANT ME TO LOG THINGS.
                # IT'S LIKE A VILLAGE THAT LIVES IN AN AREA PRONE TO FIRES - THEY BUILT THEIR HOUSES OUT OF WOOD WITHOUT THINKING...
                # SO THE VILLAGE ELDER IS LIKE: "OH. IT'S OK - WE'LL BUILD AND STAFF A FIRE STATION!"
                # "AND WHENEVER OUR LOOKOUTS SPOT A FIRE, EVERYONE IN THE VILLAGE WILL STOP WHATEVER THEY ARE DOING AND ESCAPE TO THE TOWN SQUARE WHILE THE FIRE IS BEING PUT OUT!"
                # UNTIL YOU FIND OUT THE FUDGING FIRE STATION IS ALSO MADE OUT OF WOOD AND THE FIRE STATION IS THE ONLY ONE THAT KEEPS GETTING BURNED DOWN.

                # DID YOU KNOW YOU CAN'T EVEN *READ* THE ELIOT LOGS WITH THE TREE UTILITY BY DEFAULT? I HAD TO WRITE MY OWN UTILITY TO PARSE UNICODE.
                # AND WHY DOES ELIOT CATCH EXCEPTIONS WITHIN EVENTS WITHOUT RE-PROPAGATING IT? IN WHAT WORLD DOES A LOGGER HAVE THE RIGHT TO AFFECT THE SYSTEM???
                # I CAN'T EVEN PROPERLY STITCH THE TRACES ACROSS DIFFERENT MACHINES - THE TIMESTAMPS ARE ALL MESSED UP?????
                # WHY DO THEY EVEN NEED TEN THOUSAND DIFFERENT CODE FILES IN THEIR LIBRARY? WHY???
                # THE LESSON HERE IS: FIND A DIFFERENT LOGGER.

                # ctx.log(f"Token: {word.surface:<10} POS1: {pos_main:<10} POS2: {pos_sub1:<10}")
                try_print(f"Token: {word.surface:<10} POS1: {pos_main:<10} POS2: {pos_sub1:<10}")

                # If there's a verb, it's probably not a name.
                if pos_main == '動詞' or pos_main == '助動詞':
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
