from onnxruntime import RunOptions, InferenceSession

def decorated_run(method):
    def new_run(self, *args, **kwargs):
        run_options = RunOptions()

        if self.get_providers()[0] == "CUDAExecutionProvider":
            run_options.add_run_config_entry("kOrtRunOptionsConfigEnableMemPattern", "gpu:0")
            run_options.add_run_config_entry("kOrtRunOptionsConfigEnableMemoryArenaShrinkage", "gpu:0")
            run_options.add_run_config_entry("kOrtSessionOptionsUseDeviceAllocatorForInitializers", "1")
            run_options.add_run_config_entry("memory.enable_memory_arena_shrinkage", "gpu:0")
        return method(self, *args, run_options=run_options, **kwargs)
    
    return new_run

InferenceSession.run = decorated_run(InferenceSession.run)

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
from gandy.text_detection.dfine_image_detection import DFineImageDetectionApp, DFineLineImageDetectionApp
from gandy.text_recognition.tr_recognition import TrOCRTextRecognitionApp, MagnusTextRecognitionApp
from gandy.onnx_models.ebr import (
    ListEnergyRerankerONNX,
    DiscriminativeRerankerONNX,
    HumanRerankerONNX,
    QualityRerankerONNX,
)
from gandy.reranking.generic_reranker import GenericRerankerApp, BaseRerankingApp
from transformers import NllbTokenizer, T5Tokenizer
from gandy.utils.set_tokenizer_langs import (
    set_lang_as_j,
    set_lang_as_k,
    set_lang_as_c,
    prepend_qual,
    prepend_mad_qual_ja,
    prepend_mad_qual_generic,
    remove_unnecessary_eng_tokens,
    remove_unnecessary_eng_tokens_mad,
)
from gandy.translation.llmcpp_translation import LlmCppTranslationApp
from gandy.utils.set_tokenizer_langs import prepend_gem_ja, prepend_gem_ko, prepend_gem_zh
from gandy.full_pipelines.advanced_pipeline import AdvancedPipeline
from gandy.utils.robust_text_line_resize import robust_transform
from gandy.spell_correction.llmcpp_refinement import LlmCppRefinementApp

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

dfine_m = DFineImageDetectionApp(
    model_name="dfine_m", confidence_threshold=0.5, iou_thr=0.3, image_size=1024, filter_out_overlapping_bboxes=True,
)

dfine_l = DFineImageDetectionApp(
    model_name="dfine_l", confidence_threshold=0.4, iou_thr=0.3, image_size=1024, filter_out_overlapping_bboxes=True,
)

dfine_l_denoise = DFineImageDetectionApp(
    model_name="dfine_l_denoise", confidence_threshold=0.5, iou_thr=0.3, image_size=1024, filter_out_overlapping_bboxes=True,
)

yolo_line_e = RTDetrLineImageDetectionApp(
    model_name="yolo_line_e", confidence_threshold=0.38, iou_thr=0.15,
)

yolo_line_emassive = RTDetrExpandedLineImageDetectionApp(
    model_name="yolo_line_emassive", confidence_threshold=0.4, iou_thr=0.15, image_size=1024,
)

# 0.4 = medium
# 0.52 = large
dfine_line_emassive = DFineLineImageDetectionApp(
    model_name="dfine_line_emassive", confidence_threshold=0.52, iou_thr=0.15, image_size=1024,
)

# For Union usage only.
dfine_line_emassive_calibrated = DFineLineImageDetectionApp(
    model_name="dfine_line_emassive", confidence_threshold=0.65, iou_thr=0.15, image_size=1024,
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
        dfine_m,
        dfine_l,
        dfine_l_denoise,
        dfine_line_emassive,
        UnionImageDetectionApp(
            td_model_app=dfine_l,
            line_model_app=dfine_line_emassive_calibrated,
        ),
        UnionImageDetectionApp(
            td_model_app=dfine_l_denoise,
            line_model_app=dfine_line_emassive_calibrated,
        ),
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
        "dfine_m",
        "dfine_l",
        "dfine_l_denoise",
        "debug_dfine_line_emassive",
        "union_dfine_noisy",
        "union_dfine_denoise",
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
            join_lines_with=" ",
            gen_kwargs={
                "num_beams": 5,
                "no_repeat_ngram_size": 20,
            },
            transform=robust_transform, # Intended for use with a line detection model.
        ),
        TrOCRTextRecognitionApp(
            model_sub_path="_zhmassive/",
            do_resize=False,
            gen_kwargs={
                "num_beams": 5,
                "no_repeat_ngram_size": 20,
            },
            extra_postprocess=j_ocr_postprocess,
            transform=robust_transform,
        ),
        TrOCRTextRecognitionApp(
            model_sub_path="_jmassive/",
            do_resize=False,
            gen_kwargs={
                "num_beams": 3, # Could also be 3.
                "no_repeat_ngram_size": 99,
            },
            extra_postprocess=j_ocr_postprocess,
            transform=robust_transform, # Intended for use with a line detection model.
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
    app_names=["trocr", "trocr_jbig", "k_trocr", "k_trocr_massive", "zh_trocr_massive", "trocr_jmassive", "trocr_jmagnus", "trocr_jcomics",],
)

TRANSLATION_APP = SwitchApp(
    apps=[
        LlmCppTranslationApp(
            model_sub_path="gem/gem",
            prepend_fn=prepend_gem_ja,
            lang="Japanese",
        ),
        LlmCppTranslationApp(
            model_sub_path="gem/gem_ko",
            prepend_fn=prepend_gem_ko,
            lang="Korean",
        ),
        LlmCppTranslationApp(
            model_sub_path="gem/gem_zh",
            prepend_fn=prepend_gem_zh,
            lang="Chinese",
        ),
        LlmCppTranslationApp(
            model_sub_path="gem/gemgoliath",
            prepend_fn=lambda s: s,
            lang="Japanese",
        ),
        LlmCppTranslationApp(
            model_sub_path="gem/gemgoliath_ko",
            prepend_fn=lambda s: s,
            lang="Korean",
        ),
        LlmCppTranslationApp(
            model_sub_path="gem/gemgoliath_zh",
            prepend_fn=lambda s: s,
            lang="Chinese",
        ),
    ],
    app_names=[
        "llm_jgem",
        "llm_kgem",
        "llm_zhgem",
        "llm_jgem_goliath",
        "llm_kgem_goliath",
        "llm_zhgem_goliath",
    ],
)

SPELL_CORRECTION_APP = SwitchApp(
    apps=[
        DefaultSpellCorrectionApp(),
        LlmCppRefinementApp(
            model_sub_path="gem/gemgoliath_remix",
            prepend_fn=lambda s: s,
            lang="N/A", # lang is an unused parameter here TODO cleanup
        ),
    ],
    app_names=[
        "default",
        "remix",
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
        dfine_line_emassive,
    ],
    app_names=["none", "yolo_line", "yolo_line_xl", "yolo_line_e", "yolo_line_emassive", "yolo_line_light", "dfine_line_emassive"],
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
