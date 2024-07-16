from gandy.full_pipelines.base_pipeline import (
    BasePipeline,
)
from gandy.full_pipelines.switch_app import SwitchApp
from gandy.text_detection.base_image_detection import BaseImageDetection
from gandy.text_recognition.base_text_recognition import BaseTextRecognition
from gandy.translation.base_translation import BaseTranslation
from gandy.spell_correction.base_spell_correction import BaseSpellCorrection
from gandy.image_cleaning.base_image_clean import BaseImageClean
from gandy.image_redrawing.base_image_redraw import BaseImageRedraw
from gandy.reranking.generic_reranker import BaseRerankingApp


def nullable_app(app):
    return SwitchApp(apps=[app() if callable(app) else app], app_names=["default"])


class AdvancedPipeline(BasePipeline):
    def __init__(
        self,
        text_detection_app: SwitchApp = None,
        text_recognition_app: SwitchApp = None,
        translation_app: SwitchApp = None,
        spell_correction_app: SwitchApp = None,
        image_cleaning_app: SwitchApp = None,
        image_redrawing_app: SwitchApp = None,
        reranking_model_app: SwitchApp = None,
        text_line_model_app: SwitchApp = None,
    ):
        if text_detection_app is None:
            text_detection_app = nullable_app(BaseImageDetection)
        if text_recognition_app is None:
            text_recognition_app = nullable_app(BaseTextRecognition)
        if translation_app is None:
            translation_app = nullable_app(BaseTranslation)
        if spell_correction_app is None:
            spell_correction_app = nullable_app(BaseSpellCorrection)
        if image_cleaning_app is None:
            image_cleaning_app = nullable_app(BaseImageClean)
        if image_redrawing_app is None:
            image_redrawing_app = nullable_app(BaseImageRedraw)
        if reranking_model_app is None:
            reranking_model_app = nullable_app(BaseRerankingApp)
        if text_line_model_app is None:
            text_line_model_app = nullable_app(BaseImageDetection)

        super().__init__(
            text_detection_app=text_detection_app,
            text_recognition_app=text_recognition_app,
            translation_app=translation_app,
            spell_correction_app=spell_correction_app,
            image_cleaning_app=image_cleaning_app,
            image_redrawing_app=image_redrawing_app,
            reranking_app=reranking_model_app,
            text_line_model_app=text_line_model_app,
        )

    """ For Desktop App (Mango) """

    def switch_cleaning_app(self, app_name):
        self.image_cleaning_app.select_app(app_name)

    def switch_redrawing_app(self, app_name):
        self.image_redrawing_app.select_app(app_name)

    def switch_text_recognition_app(self, app_name):
        self.text_recognition_app.select_app(app_name)
