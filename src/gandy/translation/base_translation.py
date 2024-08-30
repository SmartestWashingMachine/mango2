from gandy.full_pipelines.base_app import BaseApp


class BaseTranslation(BaseApp):
    def __init__(self):
        super().__init__()

    def process(
        self,
        text: str,
        use_stream=None,
        return_candidates=False,
        *args,
        **kwargs,
    ):
        if return_candidates:
            return [text]
        return text  # Returns the best hypothesis.

    def unload_model(self):
        super().unload_model()
