from typing import List
from gandy.translation.base_translation import BaseTranslation

class BaseRerankingApp(BaseTranslation):
    def process(self, source_text: str, candidates: List[str], *args, **kwargs):
        # No reranking, just select the first best hypothesis (according to the MT model).
        return candidates[0]
