from transformers import AutoTokenizer
from gandy.onnx_models.base_onnx_model import BaseONNXModel
from scipy.special import softmax
import numpy as np
from gandy.utils.fancy_logger import logger

pronoun_tokens = {
    100: 0,
    38: 1,
    6968: 2,
    1185: 3,
    47: 4,
    370: 5,
    700: 6,
    894: 7,
    37: 8,
    91: 9,
    8877: 10,
    2515: 11,
    79: 12,
    264: 13,
    405: 14,
    243: 15,
    24: 16,
    85: 17,
    1694: 18,
    170: 19,
    52: 20,
    166: 21,
    10010: 22,
    1213: 23,
    51: 24,
    252: 25,
    4783: 26,
    2387: 27,
    127: 28,
    1308: 29,
    16625: 30,
    12861: 31,
    110: 32,
    2486: 33,
    12724: 34,
    9962: 35,
    39: 36,
    832: 37,
    1843: 38,
    13584: 39,
    69: 40,
    1405: 41,
    2629: 42,
    30872: 43,
    63: 44,
    3139: 45,
    2126: 46,
    2522: 47,
    84: 48,
    1541: 49,
    25017: 50,
    16837: 51,
    49: 52,
    2667: 53,
    13523: 54,
    38540: 55,
    4318: 56,
    16417: 57,
    14314: 59,
    10705: 60,
    23367: 61,
    17346: 62,
    5634: 63,
    15157: 64,
    20343: 65,
}
# Now keys=predicted classes, and values=true tokens
pronoun_tokens_switched = {y: x for x, y in pronoun_tokens.items()}


class LangsumeONNX(BaseONNXModel):
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
        x_dict["any_changed"] = False

        did_encounter_sep = False

        for si in range(len(x_dict["input_ids"])):
            token = x_dict["input_ids"][0, si]

            # SEP_TOKEN_ID = 50265
            if not did_encounter_sep and token == 50265:
                did_encounter_sep = True
                continue

            if did_encounter_sep and token in pronoun_tokens:
                x_dict["input_ids"][si] = self.tokenizer.convert_tokens_to_ids(
                    self.tokenizer.mask_token
                )
                x_dict["any_changed"] = True

        return x_dict

    def forward(self, x):
        if not x["any_changed"]:
            return x["input_ids"], None, False

        ort_inputs = {
            "input_ids": x["input_ids"].astype(np.int64),
            "attention_mask": x["attention_mask"].astype(np.int64),
        }

        ort_outs = self.ort_sess.run(None, ort_inputs)

        y_hat = ort_outs[0]
        return x["input_ids"], y_hat, True

    def postprocess(self, outp) -> str:
        input_ids, y_hat, any_changed = outp
        if not any_changed:
            return self.tokenizer.batch_decode(input_ids, skip_special_tokens=False)[0]

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

            input_ids[0, masked_indices[i]] = pronoun_tokens_switched[
                top_tokens_per_mask[i]
            ]

        return self.tokenizer.batch_decode(input_ids, skip_special_tokens=False)[0]
