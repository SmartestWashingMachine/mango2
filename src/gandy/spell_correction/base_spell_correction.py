from gandy.full_pipelines.base_app import BaseApp
from typing import List


class BaseSpellCorrection(BaseApp):
    def __init__(self):
        super().__init__()

    # Similar signature to Translation app - except here it takes an additional "target" string (the output string from the Translation app).
    def process(
        self,
        text: str,
        target: str,
        use_stream=None,
        *args,
        **kwargs,
    ):
        return target  # Returns the best hypothesis.

    def unload_model(self):
        super().unload_model()
