from transformers import AutoTokenizer
from gandy.onnx_models.base_onnx_model import BaseONNXModel
from scipy.special import softmax
import numpy as np
import logging
from gandy.utils.fancy_logger import logger


class FillProONNX(BaseONNXModel):
    def __init__(self, onnx_path, tokenizer_path, use_cuda):
        super().__init__(use_cuda=use_cuda)

        self.load_session(onnx_path)
        self.load_dataloader(tokenizer_path)

    def load_dataloader(self, t_path):
        self.tokenizer = AutoTokenizer.from_pretrained(
            t_path, truncation_side="left", padding_side="right"
        )

    def preprocess(self, inp):
        inp_text = inp["text"]

        x_dict = self.tokenizer(
            [inp_text],
            return_tensors="np",
            max_length=512,
            truncation=True,
        )

        return x_dict

    def forward(self, x):
        ort_inputs = {
            "input_ids": x["input_ids"].astype(np.int64),
            "attention_mask": x["attention_mask"].astype(np.int64),
        }

        ort_outs = self.ort_sess.run(None, ort_inputs)

        y_hat = ort_outs[0]
        return x["input_ids"], y_hat

    def postprocess(self, outp) -> str:
        input_ids, y_hat = outp

        # NOTE: Assumes bsz=1
        # Some code from: https://github.com/huggingface/transformers/blob/main/src/transformers/pipelines/fill_mask.py

        masked_indices = np.argwhere(
            input_ids[0, ...] == self.tokenizer.mask_token_id
        )  # [seqlen]

        logits = y_hat[0, masked_indices, :]
        probs = softmax(logits, axis=-1)  # [seqlen, vocab]

        top_tokens_per_mask = np.argmax(probs, axis=-1)  # [seqlen]

        for i in range(masked_indices.shape[0]):
            replaced_pronoun = self.tokenizer.convert_ids_to_tokens(
                [top_tokens_per_mask[i]]
            )
            logger.debug(f'Replacing pronoun with "{replaced_pronoun}"')

            input_ids[0, masked_indices[i]] = top_tokens_per_mask[i]

        return self.tokenizer.batch_decode(input_ids, skip_special_tokens=True)[0]
