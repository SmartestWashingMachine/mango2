from gandy.translation.base_translation import BaseTranslation
from gandy.utils.fancy_logger import logger
from optimum.onnxruntime import ORTModelForSeq2SeqLM
from gandy.state.config_state import config_state
from onnxruntime import SessionOptions, ExecutionMode, GraphOptimizationLevel
import torch


class Seq2SeqTranslationApp(BaseTranslation):
    def __init__(
        self,
        model_sub_path="/",
        encoder_tokenizer_cls=None,
        decoder_tokenizer_cls=None,
        extra_preprocess=None,
        extra_postprocess=None,
        on_source_encode=None,
        target_decode_lang=None,
    ):
        super().__init__()

        self.encoder_tokenizer_cls = encoder_tokenizer_cls
        self.decoder_tokenizer_cls = decoder_tokenizer_cls

        self.extra_preprocess = extra_preprocess
        self.extra_postprocess = extra_postprocess

        self.on_source_encode = on_source_encode
        self.target_decode_lang = target_decode_lang

        # '/' = j. '/zh/' = c. '/ko/' = k.
        self.model_sub_path = model_sub_path

    def can_load(self):
        s = "titanmt" + self.model_sub_path
        return super().can_load(f"models/{s}/model_cpu")

    def load_model(
        self,
    ):
        s = "titanmt" + self.model_sub_path

        logger.info("Loading translation model...")

        can_cuda = config_state.use_cuda and not config_state.force_translation_cpu

        if can_cuda:
            # model_path = f"models/{s}/model_gpu"
            model_path = f"models/{s}/model_cpu"  # Seems acceptable for now.

            provider = "CUDAExecutionProvider"
            self.translation_model = ORTModelForSeq2SeqLM.from_pretrained(
                model_path, provider=provider, use_io_binding=can_cuda
            )
        else:
            session_options = SessionOptions()
            session_options.intra_op_num_threads = torch.get_num_threads()
            session_options.execution_mode = ExecutionMode.ORT_SEQUENTIAL
            session_options.graph_optimization_level = (
                GraphOptimizationLevel.ORT_ENABLE_ALL
            )
            session_options.add_session_config_entry(
                "session.intra_op.allow_spinning", "1"
            )

            logger.log(
                f"Loading MT model with threads N={session_options.intra_op_num_threads}"
            )

            model_path = f"models/{s}/model_cpu"
            provider = "CPUExecutionProvider"
            # load_in_8bit needed even? I thought not but it makes a difference in tests according to one end user (not me)...

            self.translation_model = ORTModelForSeq2SeqLM.from_pretrained(
                model_path,
                provider=provider,
                use_io_binding=False,
                load_in_8bit=True,
                session_options=session_options,
            )

        self.source_tokenizer = self.encoder_tokenizer_cls.from_pretrained(
            f"models/{s}tokenizer_src",
            truncation_side="left",
        )

        if self.decoder_tokenizer_cls is not None:
            self.target_tokenizer = self.decoder_tokenizer_cls.from_pretrained(
                f"models/{s}tokenizer_en"
            )
        else:
            self.target_tokenizer = self.source_tokenizer

        logger.info("Done loading translation model!")

        self.loaded = True

    def unload_model(self):
        try:
            del self.translation_model
            logger.info("Unloading translation model...")
        except:
            pass
        self.translation_model = None

        return super().unload_model()

    def source_encode(self, text: str):
        if self.on_source_encode is not None:
            self.on_source_encode(self.source_tokenizer)

        return self.source_tokenizer(text, max_length=476, truncation=True, padding=False, return_tensors="pt")

    def target_decode(self, output):
        if config_state.decoding_mode == "beam":
            return [self.target_tokenizer.batch_decode(output)[0]]

        return self.target_tokenizer.batch_decode(output)

    def strip_padding(self, prediction):
        return (
            prediction.replace("</s>", "")
            .encode("ascii", "ignore")
            .decode("utf-8")
            .strip()
        )

    def do_generate(self, x_dict, extra_kwargs):
        true_beams = (
            1 if config_state.decoding_mode == "mbr_gsample" else config_state.num_beams
        )
        true_num_return_sequences = (
            config_state.num_beams if config_state.decoding_mode != "beam" else 1
        )

        """
        Due to how beam search works, this can cause cascading errors in long text generation.

        if self.target_decode_lang is not None:

            pref = [[
                self.source_tokenizer.convert_tokens_to_ids('</s>'),
                self.source_tokenizer.lang_code_to_id[self.target_decode_lang],
                self.source_tokenizer.convert_tokens_to_ids('<TSOS>'),
            ] for _ in range(1)]
            pref = torch.tensor(pref, dtype=torch.int64).to(x_dict["input_ids"].device)
        """

        gen_kwargs = {
            "max_length": 476
            if config_state.max_length_a == 0
            else (x_dict["input_ids"].shape[1] * config_state.max_length_a),
            # Helps with computation time with beam search.
            "early_stopping": True,
            # This is so-so. Use to be a critical parameter for doc2doc models, but for doc2sent models 0.6 to 1.0 works fine.
            "length_penalty": config_state.length_penalty,
            # Modifies the higher order structure. Helps prevent repeating sentences. May not actually be needed anymore, since the model appears to be decently tuned.
            "no_repeat_ngram_size": config_state.no_repeat_ngram_size,
            # Following the "Diverse Beam Search" paper, tried setting the number of groups to the number of beams.
            # This will attempt to encourage each beam to have diverse outcomes, by accounting for similarity of the beam groups at each step.
            # However, this had a poor effect on quality even after tuning the diversity penalty.
            # num_beam_groups=5 if force_word_ids is None else 1,
            # Following the "CRTL" paper, we initially set the repetition penalty to 1.2. It was just okay.
            # This will attempt to further discourage repetition of previously used tokens.
            "repetition_penalty": config_state.repetition_penalty,
            # Actually hacked in a beam search patience parameter earlier and experimented from t=[1, 5, 20]. Little to no effect.
            # Attention (again) coming... SOON!
            "return_dict_in_generate": False,
            "output_attentions": False,
            "output_scores": False,
            # Decoding mode params. (can be "beam" | "mbr_gsample" | "mbr_bsample")
            "do_sample": config_state.decoding_mode != "beam",
            "num_beams": true_beams if "streamer" not in extra_kwargs else 1,
            "num_return_sequences": true_num_return_sequences,
            "top_k": config_state.top_k,
            "top_p": config_state.top_p,
            "temperature": config_state.temperature,
            "renormalize_logits": config_state.decoding_mode != "beam",
            "epsilon_cutoff": config_state.epsilon_cutoff,
            "forced_bos_token_id": self.source_tokenizer.lang_code_to_id[
                self.target_decode_lang
            ],
            **extra_kwargs,
        }

        if gen_kwargs["top_p"] <= 0:
            gen_kwargs.pop("top_p")  # This actually affects the behavior.

        if config_state.decoding_mode == "beam":
            gen_kwargs.pop("top_k")  # This just suppresses a warning.

        # logger.debug(f"Translating with GenArgs: {gen_kwargs}")

        generated = self.translation_model.generate(
            input_ids=x_dict["input_ids"],
            attention_mask=x_dict["attention_mask"],
            **gen_kwargs,
        )

        return self.target_decode(generated)

    def translate_string(self, inp: str, use_stream=None):
        if self.extra_preprocess is not None:
            inp = self.extra_preprocess(inp)

        extra_kwargs = {}
        if use_stream is not None:
            use_stream.tokenizer = self.target_tokenizer
            extra_kwargs["streamer"] = use_stream

        x_dict = self.source_encode(inp)

        predictions = self.do_generate(x_dict, extra_kwargs)
        predictions = [self.strip_padding(p) for p in predictions]

        if self.extra_postprocess is not None:
            predictions = [self.extra_postprocess(p).strip() for p in predictions]

        return predictions, inp

    def process(
        self,
        text: str = None,
        use_stream=None,
    ):
        with logger.begin_event("Translation") as ctx:
            if len(text) > 0 and not text.endswith("<TSOS>"):
                output = self.translate_string(
                    text, use_stream=use_stream
                )  # [target strings], [source strings]
                ctx.log(
                    f"Translated",
                    input_text=text,
                    normalized=output[1],
                    output_text=output[0],
                )
            else:
                output = [[""], [""]]  # [target strings], [source strings]
                ctx.log(f"Poor text found - returning empty string")

        return output[0]
