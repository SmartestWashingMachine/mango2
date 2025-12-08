from onnxruntime import RunOptions, InferenceSession
from gandy.utils.try_print import try_print

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
from gandy.image_redrawing.physics.image_redraw_physics import ImageRedrawPhysics
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
from gandy.text_detection.dfine_image_detection import DFineImageDetectionApp, DFineLineImageDetectionApp, DFineFrameDetectionApp
from gandy.text_recognition.custom_gguf_ocr import CustomGgufOcrApp
from gandy.reranking.generic_reranker import BaseRerankingApp
from gandy.translation.llmcpp_translation import LlmCppTranslationApp, GoliathTranslationApp
from gandy.translation.custom_gguf_translation import CustomGgufTranslationApp
from gandy.utils.set_tokenizer_langs import prepend_gem_ja, prepend_gem_ko, prepend_gem_zh
from gandy.full_pipelines.advanced_pipeline import AdvancedPipeline
from gandy.utils.robust_text_line_resize import robust_transform, alt_robust_transform, alt_robust_transform_custom
from gandy.spell_correction.llmcpp_refinement import LlmCppRefinementApp
import os

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

dfine_l_group = DFineImageDetectionApp(
    model_name="dfine_l_group", confidence_threshold=0.5, iou_thr=0.3, image_size=1024, filter_out_overlapping_bboxes=True,
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

dfine_frame = DFineFrameDetectionApp(
    model_name="dfine_frame", confidence_threshold=0.4, iou_thr=0.7, image_size=1024,
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
        dfine_l_group,
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
        "dfine_l_group",
    ],
)

TEXT_RECOGNITION_APP = SwitchApp(
    apps=[
        CustomGgufOcrApp(
            model_sub_path="config",
            config_sub_path="j_ocr_tiny",
            transform=alt_robust_transform_custom, # Intended for use with a line detection model.
        ),
        CustomGgufOcrApp(
            model_sub_path="config",
            config_sub_path="ko_ocr_tiny",
            transform=alt_robust_transform_custom,
            join_lines_with=" "
        ),
        CustomGgufOcrApp(
            model_sub_path="config",
            config_sub_path="zh_ocr_tiny",
            transform=alt_robust_transform_custom,
        ),
    ],
    app_names=["j_ocr_tiny", "ko_ocr_tiny", "zh_ocr_tiny"],
)

TRANSLATION_APP = SwitchApp(
    apps=[
        CustomGgufTranslationApp(
            model_sub_path="config",
            prepend_fn=lambda s: s,
            lang="Generic",
            config_sub_path="jam",
        ),
        CustomGgufTranslationApp(
            model_sub_path="config",
            prepend_fn=lambda s: s,
            lang="Generic",
            config_sub_path="kam",
        ),
        CustomGgufTranslationApp(
            model_sub_path="config",
            prepend_fn=lambda s: s,
            lang="Generic",
            config_sub_path="zham",
        ),
    ],
    app_names=[
        "gem_uni_ja",
        "gem_uni_ko",
        "gem_uni_zh",
        # There's also the gem_reforged_x_massive model family.
        # There's also the mage_uni_x model family - but let's keep that as a genuine custom model.
    ],
)

SPELL_CORRECTION_APP = SwitchApp(
    apps=[
        DefaultSpellCorrectionApp(),
        LlmCppRefinementApp(
            model_sub_path="gem/gemgoliath_remix",
            prepend_fn=lambda s: s,
            lang="N/A", # lang is an unused parameter here TODO cleanup
            prepend_model_output="\\nHere\\'s the refined translation:\\n" # Llama CPP seems to already add an extra newline.
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
        ImageRedrawPhysics(),
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
        "physics",
    ],
    # default_idx=-1
)

RERANKING_MODEL_APP = SwitchApp(
    apps=[
        BaseRerankingApp(),
    ],
    app_names=[
        "none",
        # All the other rerankers still require Pytorch and they kinda suck.
        # They were a product of their time, you see.
        # Nowadays LLMs seem to be better at reranking, so that might be a potential addition in the future. (See MT Hunyuan Chimera)
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

# CUSTOM TRANSLATION MODEL GGUFS

os.makedirs("models/custom_translators", exist_ok=True)

IGNORE_FILES = TRANSLATION_APP.app_names + ["jam", "kam", "zham"] # These are my models.

custom_model_suffix = ".mango_config.json"

for model in os.listdir("models/custom_translators"):
    if model.endswith(custom_model_suffix):
        model_name = model[:-len(custom_model_suffix)] # GGUF attachment automatically added
        if os.path.exists(f"models/custom_translators/{model_name}.mango_config.json"):
            if model_name in IGNORE_FILES:
                continue

            try_print(f'Found translation model: "{model}"')

            custom_translation_app = CustomGgufTranslationApp(
                model_sub_path="config",
                prepend_fn=lambda s: s,
                lang="Generic",
                config_sub_path=model_name,
            )

            user_model_name = f"(Custom Translator) {model_name}"
            TRANSLATION_APP.add_app(custom_translation_app, user_model_name)
        else:
            try_print(f'WARNING: No config found for "{model}"')

os.makedirs("models/custom_ocrs", exist_ok=True)

# IGNORE_FILES = ['q25_j', 'q25_k', 'q25_zh']
IGNORE_FILES = TEXT_RECOGNITION_APP.app_names

for model in os.listdir("models/custom_ocrs"):
    if model.endswith(custom_model_suffix):
        model_name = model[:-len(custom_model_suffix)] # GGUF attachment automatically added
        if os.path.exists(f"models/custom_ocrs/{model_name}.mango_config.json"):
            if model_name in IGNORE_FILES:
                continue

            try_print(f'Found OCR model: "{model}"')

            custom_ocr_app = CustomGgufOcrApp(
                model_sub_path="config",
                config_sub_path=model_name,
                transform=alt_robust_transform_custom, # Intended for use with a line detection model.
            )

            user_model_name = f"(Custom OCR) {model_name}"
            TEXT_RECOGNITION_APP.add_app(custom_ocr_app, user_model_name)
        else:
            try_print(f'WARNING: No config found for "{model}"')

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
    frame_model=dfine_frame,
)
