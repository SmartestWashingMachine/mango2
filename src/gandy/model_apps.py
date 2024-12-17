from gandy.full_pipelines.base_pipeline import (
    BasePipeline,
    DefaultSpellCorrectionApp,
)
from gandy.full_pipelines.switch_app import SwitchApp
from gandy.image_cleaning.no_image_clean import NoImageCleanApp
from gandy.image_cleaning.simple_image_clean import SimpleImageCleanApp
from gandy.image_cleaning.telea_image_clean import TeleaImageCleanApp
from gandy.image_cleaning.tnet_image_clean import TNetImageClean
from gandy.image_cleaning.tnet_edge_image_clean import TNetEdgeImageClean
from gandy.image_cleaning.blur_image_clean import BlurImageCleanApp
from gandy.image_cleaning.blur_and_mask_image_clean import BlurMaskImageCleanApp
from gandy.image_cleaning.text_fill_clean import TextFillCleanApp
from gandy.image_cleaning.adaptive_image_clean import AdaptiveImageCleanApp
from gandy.image_redrawing.amg_convert import AMGConvertApp
from gandy.image_redrawing.image_redraw_v2 import ImageRedrawV2App
from gandy.image_redrawing.neighbor_redraw import NeighborRedrawApp
from gandy.image_redrawing.image_redraw_global import ImageRedrawGlobalApp
# from gandy.image_redrawing.image_redraw_global_smart import ImageRedrawGlobalSmartApp
from gandy.image_redrawing.image_redraw_global_smarter import ImageRedrawGlobalSmarter
from gandy.image_redrawing.smarter.policy import ACTIONS, ACTIONS_SMART_TOON
from gandy.image_redrawing.image_redraw_global_smart_bg import (
    ImageRedrawGlobalSmartBackgroundApp,
)
from gandy.image_redrawing.image_redraw_big_global import ImageRedrawBigGlobalApp
from gandy.image_redrawing.image_redraw_big_global_amg import ImageRedrawBigGlobalAMGApp
from gandy.text_detection.yolo_image_detection import (
    YOLOTDImageDetectionApp,
    YOLOLineImageDetectionApp,
    YOLOLineExtendedImageDetectionApp,
    YOLOLineExtendedImageDetectionApp640
)
from gandy.text_detection.rtdetr_image_detection import (
    RTDetrImageDetectionApp,
    RTDetrLineImageDetectionApp,
    RTDetrExpandedLineImageDetectionApp,
)
from gandy.text_detection.none_image_detection import NoneImageDetectionApp
from gandy.text_detection.union_image_detection import UnionImageDetectionApp
from gandy.text_recognition.tr_recognition import TrOCRTextRecognitionApp, MagnusTextRecognitionApp
from gandy.translation.seq2seq_translation import (
    Seq2SeqTranslationApp,
)
from gandy.spell_correction.fill_pro_spell_correction import FillProApp
from gandy.spell_correction.langsume_spell_correction import LangsumeApp
from gandy.spell_correction.prepend_source_spell_correction import (
    PrependSourceApp,
    PrependSourceNoContextApp,
)
from gandy.onnx_models.ebr import (
    ListEnergyRerankerONNX,
    DiscriminativeRerankerONNX,
    HumanRerankerONNX,
    QualityRerankerONNX,
)
from gandy.reranking.generic_reranker import GenericRerankerApp, BaseRerankingApp
from gandy.spell_correction.emil_spell_correction import EmilSpellCorrectionApp
from transformers import NllbTokenizer, T5Tokenizer
from gandy.utils.set_tokenizer_langs import (
    set_lang_as_j,
    set_lang_as_k,
    set_lang_as_c,
    prepend_qual,
    prepend_mad_qual,
    remove_unnecessary_eng_tokens,
    remove_unnecessary_eng_tokens_mad,
)
from gandy.full_pipelines.advanced_pipeline import AdvancedPipeline

yolo_xl = YOLOTDImageDetectionApp(
    model_name="yolo_xl", confidence_threshold=0.4, iou_thr=0.3
)

detr_xl = RTDetrImageDetectionApp(
    model_name="detr_xl", confidence_threshold=0.25, iou_thr=0.5, image_size=1024, filter_out_overlapping_bboxes=True,
)

detr_xl_xxx = RTDetrImageDetectionApp(
    # NOTE: Maybe conf=0.35 is better?
    model_name="detr_xl_xxx", confidence_threshold=0.35, iou_thr=0.5, image_size=1024, filter_out_overlapping_bboxes=False,
)

yolo_line_e = RTDetrLineImageDetectionApp(
    model_name="yolo_line_e", confidence_threshold=0.38, iou_thr=0.15,
)

yolo_line_emassive = RTDetrExpandedLineImageDetectionApp(
    model_name="yolo_line_emassive", confidence_threshold=0.4, iou_thr=0.15, image_size=1024,
)

# Better LTR sorting.
yolo_line_emassive_calibrated = RTDetrExpandedLineImageDetectionApp(
    model_name="yolo_line_emassive", confidence_threshold=0.6, iou_thr=0.15, image_size=1024,
)

yolo_line_light = YOLOLineExtendedImageDetectionApp640(
    model_name="yolo_line_light", confidence_threshold=0.52, iou_thr=0.15,
)


TEXT_DETECTION_APP = SwitchApp(
    apps=[
        YOLOTDImageDetectionApp(),
        yolo_xl,
        detr_xl,
        detr_xl_xxx,
        UnionImageDetectionApp(
            td_model_app=yolo_xl,
            line_model_app=yolo_line_e,
        ),
        UnionImageDetectionApp(
            td_model_app=detr_xl,
            line_model_app=yolo_line_e,
        ),
        UnionImageDetectionApp(
            td_model_app=yolo_xl,
            line_model_app=yolo_line_emassive,
        ),
        UnionImageDetectionApp(
            td_model_app=detr_xl,
            line_model_app=yolo_line_emassive,
        ),
        UnionImageDetectionApp(
            td_model_app=detr_xl_xxx,
            line_model_app=yolo_line_emassive_calibrated,
        ),
        NoneImageDetectionApp(),
        yolo_line_emassive,
        yolo_line_light,
    ],
    app_names=[
        "yolo_td",
        "yolo_xl",
        "detr_xl",
        "detr_xl_xxx",
        "union",
        "union_detr",
        "union_massive",
        "union_massive_detr",
        "union_massive_detr_xxx",
        "none",
        "debug_yolo_line_emassive",
        "debug_yolo_line_light",
    ],
)

j_ocr_postprocess = lambda s: s.replace(" ", "")

TEXT_RECOGNITION_APP = SwitchApp(
    apps=[
        TrOCRTextRecognitionApp(model_sub_path="_j/", extra_postprocess=j_ocr_postprocess),
        TrOCRTextRecognitionApp(
            model_sub_path="_jbig/",
            gen_kwargs={
                "num_beams": 5,
                "no_repeat_ngram_size": 7,  # Use to be None
            }, 
            extra_postprocess=j_ocr_postprocess
        ),
        TrOCRTextRecognitionApp(
          model_sub_path="_ko/",
            gen_kwargs={
                "num_beams": 5,
            },
        ),
        TrOCRTextRecognitionApp(
            model_sub_path="_komassive/",
            do_resize=False,
            gen_kwargs={
                "num_beams": 5,
                "no_repeat_ngram_size": 7,
            },
        ),
        TrOCRTextRecognitionApp(
          model_sub_path="_zh/",
            gen_kwargs={
                "num_beams": 5,
            },
        ),
        MagnusTextRecognitionApp(
            model_sub_path="_zhmassive/",
            do_resize=False,
            gen_kwargs={
                "num_beams": 5,
                "no_repeat_ngram_size": 7,
            },
        ),
        MagnusTextRecognitionApp(
            model_sub_path="_jmassive/",
            do_resize=False,
            gen_kwargs={
                "num_beams": 5,
                "no_repeat_ngram_size": 7,
            },
            extra_postprocess=j_ocr_postprocess,
        ),
        MagnusTextRecognitionApp(
            model_sub_path="_jmagnus/",
            do_resize=False,
            gen_kwargs={
                "num_beams": 5,
                "no_repeat_ngram_size": 7,
            },
            extra_postprocess=j_ocr_postprocess,
        ),
        TrOCRTextRecognitionApp(
            model_sub_path="_jcomics/",
            do_resize=False,
            do_stretch=True,
            gen_kwargs={
                "num_beams": 5,
                "no_repeat_ngram_size": 7,
            }, 
            extra_postprocess=j_ocr_postprocess
        ),
    ],
    app_names=["trocr", "trocr_jbig", "k_trocr", "k_trocr_massive", "zh_trocr", "zh_trocr_massive", "trocr_jmassive", "trocr_jmagnus", "trocr_jcomics",],
)

TRANSLATION_APP = SwitchApp(
    apps=[
        Seq2SeqTranslationApp(
            model_sub_path="_jq/",
            encoder_tokenizer_cls=NllbTokenizer,
            extra_preprocess=prepend_qual,
            extra_postprocess=remove_unnecessary_eng_tokens,
            on_source_encode=set_lang_as_j,
            target_decode_lang="eng_Latn",
        ),
        Seq2SeqTranslationApp(
            model_sub_path="_kq/",
            encoder_tokenizer_cls=NllbTokenizer,
            extra_preprocess=prepend_qual,
            extra_postprocess=remove_unnecessary_eng_tokens,
            on_source_encode=set_lang_as_k,
            target_decode_lang="eng_Latn",
        ),
        Seq2SeqTranslationApp(
            model_sub_path="_cq/",
            encoder_tokenizer_cls=NllbTokenizer,
            extra_preprocess=prepend_qual,
            extra_postprocess=remove_unnecessary_eng_tokens,
            on_source_encode=set_lang_as_c,
            target_decode_lang="eng_Latn",
        ),
        Seq2SeqTranslationApp(
            model_sub_path="_jmad/",
            encoder_tokenizer_cls=T5Tokenizer,
            extra_preprocess=prepend_mad_qual,
            extra_postprocess=remove_unnecessary_eng_tokens_mad,
            target_decode_lang=None,
            max_length=200,
        ),
        Seq2SeqTranslationApp(
            model_sub_path="_jq300/",
            encoder_tokenizer_cls=NllbTokenizer,
            extra_preprocess=prepend_qual,
            extra_postprocess=remove_unnecessary_eng_tokens,
            on_source_encode=set_lang_as_j,
            target_decode_lang="eng_Latn",
            max_length=300,
        ),
        Seq2SeqTranslationApp(
            model_sub_path="_komad/",
            encoder_tokenizer_cls=T5Tokenizer,
            extra_preprocess=prepend_mad_qual,
            extra_postprocess=remove_unnecessary_eng_tokens_mad,
            target_decode_lang=None,
            max_length=200,
        ),
        Seq2SeqTranslationApp(
            model_sub_path="_zhmad/",
            encoder_tokenizer_cls=T5Tokenizer,
            extra_preprocess=prepend_mad_qual,
            extra_postprocess=remove_unnecessary_eng_tokens_mad,
            target_decode_lang=None,
            max_length=200,
        ),
    ],
    app_names=[
        "nllb_jq",
        "nllb_ko",
        "nllb_zh",
        "nllb_jmad",
        "nllb_jq300",
        "nllb_komad",
        "nllb_zhmad",
    ],
)

SPELL_CORRECTION_APP = SwitchApp(
    apps=[
        DefaultSpellCorrectionApp(),
        FillProApp(),
        LangsumeApp(),
        PrependSourceApp(),
        PrependSourceNoContextApp(),
        EmilSpellCorrectionApp(
            model_sub_path="_jq/",
            tokenizer_cls=NllbTokenizer,
            extra_preprocess=prepend_qual,
            extra_postprocess=remove_unnecessary_eng_tokens,
            on_source_encode=set_lang_as_j,
            target_decode_lang="eng_Latn",
        )
    ],
    app_names=[
        "default",
        "fillpro",
        "langsume",
        "prepend_source",
        "prepend_source_noctx",
        "emil_j",
    ],
)

IMAGE_CLEANING_APP = SwitchApp(
    apps=[
        NoImageCleanApp(),
        SimpleImageCleanApp(),
        TeleaImageCleanApp(),
        TNetImageClean(),
        TNetEdgeImageClean(),
        BlurImageCleanApp(),
        BlurMaskImageCleanApp(),
        TextFillCleanApp(),
        AdaptiveImageCleanApp(),
    ],
    app_names=[
        "none",
        "simple",
        "telea",
        "smart_telea",
        "edge_connect",
        "blur",
        "blur_mask",
        "text_clean",
        "adaptive_clean",
    ],
    # default_idx=1,
)

IMAGE_REDRAWING_APP = SwitchApp(
    apps=[
        AMGConvertApp(),
        NeighborRedrawApp(),
        ImageRedrawV2App(),
        ImageRedrawGlobalApp(),
        ImageRedrawBigGlobalApp(),
        ImageRedrawBigGlobalAMGApp(),
        ImageRedrawGlobalSmarter(ACTIONS),
        ImageRedrawGlobalSmarter(ACTIONS_SMART_TOON),
        ImageRedrawGlobalSmartBackgroundApp(),
    ],
    app_names=[
        "amg_convert",
        "neighbor",
        "simple",
        "global",
        "big_global",
        "big_global_amg",
        "smart",
        "smart_toon",
        "smart_bg",
    ],
    # default_idx=-1
)

RERANKING_MODEL_APP = SwitchApp(
    apps=[
        BaseRerankingApp(),
        GenericRerankerApp("listenergy_nocontext", ListEnergyRerankerONNX),
        GenericRerankerApp("doctor", DiscriminativeRerankerONNX),
        GenericRerankerApp("human", HumanRerankerONNX),
        GenericRerankerApp(
            "quality", QualityRerankerONNX, tokenizer_name="quality_tokenizer"
        ),
    ],
    app_names=[
        "none",
        "listenergy_nocontext",
        "doctor",
        "human",
        "quality",
    ],
)

TEXT_LINE_MODEL_APP = SwitchApp(
    apps=[
        None,
        YOLOLineImageDetectionApp(),
        YOLOLineImageDetectionApp(model_name="yolo_line_xl", confidence_threshold=0.25),
        yolo_line_e,
        yolo_line_emassive,
        yolo_line_light,
    ],
    app_names=["none", "yolo_line", "yolo_line_xl", "yolo_line_e", "yolo_line_emassive", "yolo_line_light"],
)

# disable for debug
translate_pipeline = AdvancedPipeline(
    text_detection_app=TEXT_DETECTION_APP,
    text_recognition_app=TEXT_RECOGNITION_APP,
    translation_app=TRANSLATION_APP,
    spell_correction_app=SPELL_CORRECTION_APP,
    image_cleaning_app=IMAGE_CLEANING_APP,
    image_redrawing_app=IMAGE_REDRAWING_APP,
    reranking_model_app=RERANKING_MODEL_APP,
    text_line_model_app=TEXT_LINE_MODEL_APP,
)
