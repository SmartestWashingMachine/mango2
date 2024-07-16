from gandy.onnx_models.ebr import BaseRerankerONNX
from gandy.translation.base_translation import BaseTranslation
from gandy.state.config_state import config_state
from typing import List
from gandy.utils.fancy_logger import logger


class GenericRerankerApp(BaseTranslation):
    def __init__(
        self,
        model_name: str,
        reranker_cls: BaseRerankerONNX,
        tokenizer_name="db_tokenizer_fixed",
    ):
        super().__init__()

        self.model_name = model_name
        self.reranker_cls = reranker_cls

        self.tokenizer_name = tokenizer_name

    def can_load(self):
        return super().can_load(
            path_exists=f"models/energy_rerankers_j/{self.model_name}.onnx"
        )

    def load_model(self):
        logger.info("Loading reranker model...")
        self.reranking_model = self.reranker_cls(
            f"models/energy_rerankers_j/{self.model_name}.onnx",
            f"models/energy_rerankers_j/{self.tokenizer_name}",
            use_cuda=config_state.use_cuda,
        )
        logger.info("Done loading reranker model!")

        return super().load_model()

    def process(self, source_text: str, candidates: List[str], *args, **kwargs):
        best_text = self.reranking_model.full_pipe(
            *args, source_text=source_text, candidates=candidates, **kwargs
        )

        return best_text


class BaseRerankingApp(BaseTranslation):
    def process(self, source_text: str, candidates: List[str], *args, **kwargs):
        # No reranking, just select the first best hypothesis (according to the MT model).
        return candidates[0]
