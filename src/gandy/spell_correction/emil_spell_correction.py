from gandy.full_pipelines.base_app import BaseApp
from typing import List
import re
from gandy.state.config_state import config_state
from gandy.utils.fancy_logger import logger
from gandy.translation.seq2seq_translation import BreakableORTModelForSeq2SeqLM
from onnxruntime import SessionOptions, ExecutionMode, GraphOptimizationLevel

try:
    import torch
except:
    pass

# A lot of the code here is borrowed from Seq2SeqTranslationApp.

class EmilSpellCorrectionApp(BaseApp):
    def __init__(self, tokenizer_cls, model_sub_path: str, target_decode_lang = None, on_source_encode = None, extra_preprocess = None, extra_postprocess = None):
        super().__init__()

        self.tokenizer_cls = tokenizer_cls
        self.model_sub_path = model_sub_path
        self.target_decode_lang = target_decode_lang

        self.on_source_encode = on_source_encode

        self.extra_preprocess = extra_preprocess
        self.extra_postprocess = extra_postprocess

    def can_load(self):
        s = "emilmt" + self.model_sub_path
        return super().can_load(f"models/{s}/model_cpu")

    def load_model(
        self,
    ):
        s = "emilmt" + self.model_sub_path

        logger.info("Loading translation model...")

        can_cuda = config_state.use_cuda and not config_state.force_translation_cpu

        if can_cuda:
            # model_path = f"models/{s}/model_gpu"
            model_path = f"models/{s}/model_cpu"  # Seems acceptable for now.

            provider = "CUDAExecutionProvider"
            self.translation_model = BreakableORTModelForSeq2SeqLM.from_pretrained(
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

            self.translation_model = BreakableORTModelForSeq2SeqLM.from_pretrained(
                model_path,
                provider=provider,
                use_io_binding=False,
                load_in_8bit=True,
                session_options=session_options,
            )

        self.tokenizer = self.tokenizer_cls.from_pretrained(
            f"models/{s}tokenizer_src",
            truncation_side="left",
        )

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

    def preprocess_str(self, cur_src: str, texts: str):
        cur_tgt = re.split(r"<SEP>|<TSOS>", texts)[
            -1
        ].strip()  # Only get last sentence.

        inp = f"{cur_src}<Q9>{cur_tgt}"

        if self.extra_preprocess is not None:
            inp = self.extra_preprocess(inp)

        return inp
    
    def source_encode(self, text: str):
        if self.on_source_encode is not None:
            self.on_source_encode(self.tokenizer)

        return self.tokenizer(text, max_length=200, truncation=True, padding=False, return_tensors="pt")

    def target_decode(self, output):
        return self.tokenizer.batch_decode(output)[0]
    
    def postprocess_str(self, prediction):
        prediction = (
            prediction.replace("</s>", "")
            .strip()
        )

        if self.extra_postprocess is not None:
            prediction = self.extra_postprocess(prediction)

        return prediction
    
    def do_generate(self, x_dict):
        extra_kwargs = {}
        if self.target_decode_lang is not None:
            extra_kwargs['forced_bos_token_id'] = self.tokenizer.lang_code_to_id[
                self.target_decode_lang
            ],

        gen_kwargs = {
            "max_length": 200,
            "early_stopping": True,
            "return_dict_in_generate": False,
            "output_attentions": False,
            "output_scores": False,
            "do_sample": config_state.decoding_mode != "beam",
            "num_beams": 3,
            **extra_kwargs,
        }

        generated = self.translation_model.generate(
            input_ids=x_dict["input_ids"],
            attention_mask=x_dict["attention_mask"],
            **gen_kwargs,
        )

        return generated

    def process(self, translation_input: List[str], texts: str, *args, **kwargs):
        outputs = []

        with logger.begin_event("Emil Spelling Correction") as ctx:
            for src_inp, tgt_inp in zip(
                [translation_input[-1]], [texts]
            ): # This model does not support context.
                mapped_inp = self.preprocess_str(src_inp, tgt_inp)

                ctx.log(f"Editing input", preprocessed=mapped_inp)

                tokenized_in = self.source_encode(mapped_inp)
                tokenized_out = self.do_generate(tokenized_in)

                output = self.target_decode(tokenized_out)
                output = self.postprocess_str(output)

                outputs.append(output)

                ctx.log("Done editing a section of text!", output=output)

            return outputs

    def clear_cache(self):
        pass

    def unload_model(self):
        super().unload_model()
