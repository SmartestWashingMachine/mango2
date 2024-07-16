from typing import List
import re
import logging
from transformers import AutoTokenizer
import numpy as np
from gandy.onnx_models.base_onnx_model import BaseONNXModel
from gandy.utils.fancy_logger import logger


class BaseRerankerONNX(BaseONNXModel):
    def __init__(self, onnx_path, tokenizer_path, use_cuda):
        super().__init__(use_cuda=use_cuda)

        self.load_session(onnx_path)
        self.load_dataloader(tokenizer_path)

    def load_dataloader(self, tokenizer_path):
        self.tokenizer = AutoTokenizer.from_pretrained(
            tokenizer_path, truncation_side="left", padding_side="right"
        )

    def forward(self, source_text: str, candidates: List[str]):
        # TODO: Refactor. The clean() is duplicated from seq2seq and seq2seq big's strip_padding methods...
        text_candidates = [self.map_inp(source_text, self.clean(c)) for c in candidates]

        candidates = self.tokenizer(
            text_candidates,
            return_tensors="np",
            padding=True,
            truncation=True,
            max_length=512,
        )  # [bsz, seqlen]

        ort_inputs = {
            "input_ids": candidates["input_ids"].astype(np.int64),
            "attention_mask": candidates["attention_mask"].astype(np.int64),
        }
        ort_outs = self.ort_sess.run(None, ort_inputs)

        best_idx = ort_outs[0]

        logger.debug(f"Candidates to rerank: {' || '.join(text_candidates).strip()}")
        logger.debug(f"Reranking Best IDX == {best_idx}")

        return best_idx

    def clean(self, prediction):
        s = (
            prediction.replace("<pad>", "")
            .replace("</s>", "")
            .replace("<s>", "")
            .encode("ascii", "ignore")
            .decode("utf-8")
            .strip()
        )
        return s

    def cut_context(self, text: str):
        # Removes context from a text.
        return re.split(r"<SEP>|<TSOS>", text)[-1].strip()

    def reverse_context(self, original_s: str):
        # Reverses the sentence and context order.
        # E.G: "A <sep1> B <sep2> C" would become "C [unused2] B [unused3] A"
        # This method is not used for the listenergy_nocontext model variant.

        s = ""
        split = list(reversed(re.split(r"<SEP>|<TSOS>", original_s)))

        count = 2  # start at [unused2] (because [unused1] is used to separate the target and source string).
        for idx, segment in enumerate(split):
            s += f" {segment}"

            if (idx + 1) < len(split):
                s += f" [unused{count}]"

            count += 1

        return s.strip()

    def map_inp(self, source_text: str, target_text: str):
        target_text = self.cut_context(target_text)

        return self.merge_source_target(source_text, target_text)

    def merge_source_target(
        self, source_str_with_context: str, target_str_no_context: str
    ):
        raise RuntimeError("This method must be implemented.")


class ListEnergyRerankerONNX(BaseRerankerONNX):
    def __init__(self, onnx_path, tokenizer_path, use_cuda):
        """
        An implementation of a reranking model from "Energy-Based Reranking: Improving Neural Machine Translation Using Energy-Based Models".

        Given the source WITHOUT context (due to poor convergence), and a translation candidate WITHOUT context (due to length constraints), compute an energy score for it.
        A lower score for one candidate over another implies that the lower scoring candidate is "better" than the higher scoring candidate.

        ^^ However I've found their proposed energy loss function (max margin ranking loss) to fail horribly here, so I used a different loss from the paper
        "Improving abstractive summarization with energy-based reranking".

        Trained to find the best candidate with respect to chrf++, since chrf++ seems to perform better than BLEU. (see the WMT22 papers)
        """
        super().__init__(
            onnx_path=onnx_path, tokenizer_path=tokenizer_path, use_cuda=use_cuda
        )

    def merge_source_target(
        self, source_str_with_context: str, target_str_no_context: str
    ):
        logger.info("Mapping input for ListEnergyReranker...")
        source_str_no_context = self.cut_context(source_str_with_context)
        return f"{source_str_no_context} [unused4] {target_str_no_context}"


class DiscriminativeRerankerONNX(BaseRerankerONNX):
    def __init__(self, onnx_path, tokenizer_path, use_cuda):
        """
        An implementation of a reranking model from "Discriminative Reranking for Machine Translation". Attempts to find the best candidate with respect to chrf++.

        Given the source WITH context, and a translation candidate WITHOUT context (due to length constraints), compute a scalar score for it.
        A higher score for one candidate over another implies that the higher scoring candidate is "better" than the lower scoring candidate.
        """
        super().__init__(
            onnx_path=onnx_path, tokenizer_path=tokenizer_path, use_cuda=use_cuda
        )

    def merge_source_target(
        self, source_str_with_context: str, target_str_no_context: str
    ):
        logger.info("Mapping input for DiscriminativeReranker...")
        return f"{target_str_no_context} [unused1] {self.reverse_context(source_str_with_context)}"


class HumanRerankerONNX(BaseRerankerONNX):
    def __init__(self, onnx_path, tokenizer_path, use_cuda):
        """
        A simple classification model. Attempts to find the most "human-like" translation.

        Given the source WITH context, and a translation candidate WITHOUT context (due to length constraints), compute the probability of the candidate
        being a human translation.
        A higher probability for one candidate over another implies that the higher scoring candidate is "more human" (according to the model)
        than the lower probability candidate.

        Preprocess is just like DiscriminativeReranker. This reranker has lower correlation with respect to chrf++ than the other two.
        """
        super().__init__(
            onnx_path=onnx_path, tokenizer_path=tokenizer_path, use_cuda=use_cuda
        )

    def merge_source_target(
        self, source_str_with_context: str, target_str_no_context: str
    ):
        logger.info("Mapping input for HumanReranker...")
        return f"{target_str_no_context} [unused1] {self.reverse_context(source_str_with_context)}"


class QualityRerankerONNX(BaseRerankerONNX):
    def __init__(self, onnx_path, tokenizer_path, use_cuda):
        """
        An implementation of a model very similar to COMET-QE mainly from "Searching for Cometinho: The Little Metric That Could".

        Uses a MiniLM v2 encoder backbone and encodes the source and candidates separately before concatenating them and creating a
        few extra features to pass into the pooler and regressor head.

        Given the source WITHOUT context (due to data constraints), and a translation candidate WITHOUT context (due to data constraints), compute a quality score for it.
        A higher score for one candidate over another may imply that the higher scoring candidate is "better" than the lower scoring candidate.
        """
        super().__init__(
            onnx_path=onnx_path, tokenizer_path=tokenizer_path, use_cuda=use_cuda
        )

    def forward(self, source_text: str, candidates: List[str]):
        logger.info("Mapping inputs for QualityReranker...")

        text_candidates = [self.clean(self.cut_context(c)) for c in candidates]
        source_text = self.clean(self.cut_context(source_text))

        source = self.tokenizer(
            [source_text] * len(text_candidates),  # Need to dupe this candidate times.
            return_tensors="np",
            padding=True,
            truncation=True,
            max_length=512,
        )
        candidates = self.tokenizer(
            text_candidates,
            return_tensors="np",
            padding=True,
            truncation=True,
            max_length=512,
        )

        ort_inputs = {
            "src_input_ids": source["input_ids"].astype(np.int64),
            "src_attention_mask": source["attention_mask"].astype(np.int64),
            "mt_input_ids": candidates["input_ids"].astype(np.int64),
            "mt_attention_mask": candidates["attention_mask"].astype(np.int64),
        }
        ort_outs = self.ort_sess.run(None, ort_inputs)

        best_idx = ort_outs[0]

        logger.debug(f"Candidates to rerank: {' || '.join(text_candidates).strip()}")
        logger.debug(f"Reranking Best IDX == {best_idx}")

        return best_idx
