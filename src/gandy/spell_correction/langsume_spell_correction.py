from gandy.onnx_models.langsume import LangsumeONNX
from gandy.spell_correction.base_spell_correction import BaseSpellCorrection
import re
from gandy.state.config_state import config_state
from gandy.utils.fancy_logger import logger


class LangsumeApp(BaseSpellCorrection):
    def __init__(self):
        super().__init__()

        self.sep_char = "<SEP>"
        self.ctx_sep_char = "<CTXSEP>"

        # This app keeps an internal list of prior source-side context, only reset whenever a new image is being translated.
        # A bit band-aidy, but it works for now.
        self.texts = []

    def clear_cache(self):
        logger.debug("Langsume cache cleared.")

        self.texts = []

    def can_load(self):
        return super().can_load(path_exists=f"models/fill_pro/langsume.onnx")

    def load_model(self):
        logger.info("Loading langsume model...")
        self.translation_model = LangsumeONNX(
            f"models/fill_pro/langsume.onnx",
            f"models/fill_pro/langsume_tokenizer",
            use_cuda=config_state.use_cuda,
        )
        logger.info("Done loading langsume model!")

        return super().load_model()

    def unload_model(self):
        try:
            del self.translation_model
            logger.info("Unloading reranking model...")
        except:
            pass
        self.translation_model = None

        return super().unload_model()

    def map_input(self, tgt_text):
        # If using a ptransformer model, the input texts will probably contain <SEP1> <SEP2> <SEP3> tokens.
        last_not_masked = re.split(r"<SEP>|<TSOS>", tgt_text)[
            -1
        ].strip()  # Only get last sentence.
        # Masking is done in the OnnxModel.

        if len(self.texts) <= 1:
            joined_context = " ".join(self.texts)
        else:
            joined_context = (
                " ".join(self.texts[:-1]) + f" {self.ctx_sep_char} {self.texts[-1]}"
            )

        split = f"{joined_context} {self.sep_char} {last_not_masked}"

        return {
            "text": split,
        }

    def process(self, translation_input, texts, *args, **kwargs):
        output = []

        for src_inp, tgt_inp in zip(
            [translation_input[-1]], [texts]
        ):  # FOR NOW ONLY TAKE THE LAST ONE... DOH TODO
            logger.debug("Editing a section of text......")

            last_not_masked = re.split(r"<SEP>|<TSOS>", src_inp)[-1].strip()
            self.texts.append(last_not_masked)
            if len(self.texts) > 8:
                self.texts = self.texts[1:]

            mapped_inp = self.map_input(tgt_inp)
            logger.debug(f"Editing input: {mapped_inp['text']}")

            predictions: str = self.translation_model.full_pipe(mapped_inp)
            predictions = (
                predictions.split(self.sep_char)[-1].strip().replace("</s>", "")
            )
            output.append(predictions)

            logger.debug("Done editing a section of text!")

        return output
