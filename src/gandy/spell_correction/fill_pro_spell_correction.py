from gandy.onnx_models.fill_pro import FillProONNX
from gandy.spell_correction.base_spell_correction import BaseSpellCorrection
import re
from gandy.state.config_state import config_state
from gandy.utils.fancy_logger import logger

pronoun_words = [
    "I",
    "ĠI",
    "you",
    "You",
    "Ġyou",
    "ĠYou",
    "he",
    "He",
    "Ġhe",
    "ĠHe",
    "she",
    "She",
    "Ġshe",
    "ĠShe",
    "it",
    "It",
    "Ġit",
    "ĠIt",
    "we",
    "We",
    "Ġwe",
    "ĠWe",
    "they",
    "They",
    "Ġthey",
    "ĠThey",
    "my",
    "My",
    "Ġmy",
    "ĠMy",
    "your",
    "Your",
    "Ġyour",
    "ĠYour",
    "his",
    "His",
    "Ġhis",
    "ĠHis",
    "her",
    "Her",
    "Ġher",
    "ĠHer",
    "its",
    "Its",
    "Ġits",
    "ĠIts",
    "our",
    "Our",
    "Ġour",
    "ĠOur",
    "their",
    "Their",
    "Ġtheir",
    "ĠTheir",
    "mine",
    "Mine",
    "Ġmine",
    "ĠMine",
    "yours",
    "Yours",
    "Ġyours",
    "ĠYours",
    "hers",
    "Hers",
    "Ġhers",
    "ĠHers",
    "ours",
    "Ours",
    "Ġours",
    "ĠOurs",
    "theirs",
    "Theirs",
    "Ġtheirs",
    "ĠTheirs",
]

dot_patt = r"^\.+"


class FillProApp(BaseSpellCorrection):
    def __init__(self):
        super().__init__()

        self.sep_char = "......."

        # This app keeps an internal list of prior context, only reset whenever a new image is being translated.
        # A bit band-aidy, but it works for now.
        self.texts = []

    def clear_cache(self):
        logger.debug("FillPro cache cleared.")

        self.texts = []

    def can_load(self):
        return super().can_load(path_exists=f"models/fill_pro/robhf.onnx")

    def load_model(self):
        logger.info("Loading fill pro model...")
        self.translation_model = FillProONNX(
            f"models/fill_pro/robhf.onnx",
            f"models/fill_pro/robhf_tokenizer",
            use_cuda=config_state.use_cuda,
        )
        logger.info("Done loading fill pro model!")

        return super().load_model()

    def unload_model(self):
        try:
            del self.translation_model
            logger.info("Unloading reranking model...")
        except:
            pass
        self.translation_model = None

        return super().unload_model()

    # TODO: Make this obsolete.
    def mask_text(self, s: str):
        words = s.split(" ")

        new_words = []
        for w in words:
            w_no_apost = w.split("'")
            is_split_word = len(w_no_apost) <= 2

            is_ext_word = len(w) > 0 and w[-1] == "s"
            w_no_s = w[:-1]

            # No punct support yet. ends_in_punct = len(w) > 0 and w[-1] in ['.', '!', ',', '?', '-']

            if w in pronoun_words:
                new_words.append("<mask>")
            elif is_split_word and w_no_apost[0] in pronoun_words:
                new_words.append(f"<mask>'{w_no_apost[1]}")
            elif is_ext_word and (w_no_s in pronoun_words):
                new_words.append(f"<mask>{w[-1]}")
            else:
                new_words.append(w)

        return " ".join(new_words).strip()

    def map_input(self, input_text):
        # If using a transformer model, the input texts will probably contain <SEP> tokens.
        # But FillPro gets wonky with SEP tokens. We just remove them.
        last_not_masked = re.split(r"<SEP>|<TSOS>", input_text)[
            -1
        ].strip()  # Only get last sentence.

        last_masked = self.mask_text(last_not_masked)  # Only mask the current sentence.

        joined_context = " ".join(self.texts)
        split = f"{joined_context}{self.sep_char}{last_masked}"

        self.texts.append(last_not_masked)
        # In theory, this model can support an indefinite amount of context. But we'll see in time...
        if len(self.texts) > 8:
            self.texts = self.texts[1:]

        return {
            "text": split,
        }

    def process(self, translation_input, texts, *args, **kwargs):
        output = []

        logger.debug("Editing a section of text......")

        mapped_inp = self.map_input(texts)
        logger.debug(f"Editing input: {mapped_inp['text']}")

        predictions: str = self.translation_model.full_pipe(mapped_inp)
        predictions = predictions.split(self.sep_char)[-1].strip()

        # A little hack, removes any lingering ... (this may be detrimental for some text) if it contains other character types too.
        if not (predictions == len(predictions) * predictions[0]):
            predictions = re.sub(dot_patt, "", predictions)

        output.append(predictions)

        logger.debug("Done editing a section of text!")

        return output
