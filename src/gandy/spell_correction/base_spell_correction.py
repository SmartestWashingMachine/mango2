from gandy.full_pipelines.base_app import BaseApp
from typing import List


class BaseSpellCorrection(BaseApp):
    def __init__(self):
        super().__init__()

    def process(self, translation_input: List[str], texts: str, *args, **kwargs):
        return texts

    def clear_cache(self):
        pass

    def unload_model(self):
        super().unload_model()
