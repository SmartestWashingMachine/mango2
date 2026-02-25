from flask import request
from gandy.app import app, translate_pipeline
from gandy.state.config_state import config_state
from gandy.state.context_state import context_state
from gandy.utils.fancy_logger import logger
from gandy.full_pipelines.switch_app import SwitchApp
from typing import List
from gc import collect
import json
import os
from uuid import uuid4

@app.route("/changecleaning", methods=["POST"])
def change_cleaning_route():
    with logger.begin_event('Change cleaning mode') as ctx:
        data = request.json
        new_mode = data["mode"]

        ctx.log('New requested mode', new_mode=new_mode)

        new_mode = translate_pipeline.switch_cleaning_app(new_mode)

        translate_pipeline.log_app_usage(ctx)

    return {}, 200


@app.route("/changeredrawing", methods=["POST"])
def change_redrawing_route():
    with logger.begin_event('Change redrawing mode') as ctx:
        data = request.json
        new_mode = data["mode"]

        ctx.log('New requested mode', new_mode=new_mode)

        new_mode = translate_pipeline.switch_redrawing_app(new_mode)

        translate_pipeline.log_app_usage(ctx)

    return {}, 200

@app.route("/changetilesize", methods=["POST"])
def change_tile_size_route():
    with logger.begin_event('Change tile size') as ctx:
        data = request.json
        tile_width = data["tileWidth"]
        tile_height = data["tileHeight"]

        ctx.log('New requested tile size - changing config', tile_width=tile_width, tile_height=tile_height)

        # This should be the only route outside of /switchmodels that can affect the config state from the user side.
        # Used since /switchmodels is in the settings page: This is called from the image page.
        config_state.set_decoding_params(tile_width=tile_width, tile_height=tile_height)

    return {}, 200

@app.route("/switchmodels", methods=["POST"])
def change_multiple_models_route():
    with logger.begin_event("Update configuration state") as ctx:
        data = request.json

        # Unload is done below (see "requires_reload")
        translate_pipeline.translation_app.select_app(data["translationModelName"], unload_others=False)
        translate_pipeline.text_recognition_app.select_app(
            data["textRecognitionModelName"], unload_others=False
        )
        translate_pipeline.text_detection_app.select_app(data["textDetectionModelName"], unload_others=False)
        translate_pipeline.spell_correction_app.select_app(
            data["spellCorrectionModelName"], unload_others=False
        )

        reranking_model_name = data["rerankingModelName"]
        decoding_mode = data["decodingMode"]

        # Set OCR preprocessor.
        translate_pipeline.text_line_app.select_app(data["textLineModelName"], unload_others=False)

        if decoding_mode != "beam":
            # Only japanese-2-english models support most forms of reranking.
            non_j_model_names = ["nllb_ko", "nllb_zh"]
            non_j_supported_rerankers = ["quality"]

            if (
                data["translationModelName"] not in non_j_model_names
                or reranking_model_name in non_j_supported_rerankers
            ):
                ctx.log(
                    f"Set reranking model variant",
                    reranking_model_name=reranking_model_name,
                )

                translate_pipeline.reranking_app.select_app(reranking_model_name, unload_others=False)
            else:
                ctx.log(
                    f"Unsupported language detected for reranking - disabling reranking"
                )
                translate_pipeline.reranking_app.select_app("none", unload_others=False)
        else:
            ctx.log(f"Using beam search mode - reranking disabled.")
            translate_pipeline.reranking_app.select_app("none", unload_others=False)

        if data["contextAmount"] == "packed":
            c_amount = 100 # Okay I lied. It's up to 100! But that should be waaay more than enough, especially considering truncation...
        elif data["contextAmount"] == "three":
            c_amount = 4
        elif data["contextAmount"] == "two":
            # Context (2) + Current Sentence (1) == 3 total
            c_amount = 3
        elif data["contextAmount"] == "one":
            c_amount = 2
        else:
            c_amount = 1

        max_length_a = float(data["maxLengthA"])

        requires_reload = config_state.set_decoding_params(
            top_p=float(data["topP"]),
            top_k=data["topK"],
            length_penalty=float(data["lengthPenalty"]),
            repetition_penalty=float(data["repetitionPenalty"]),
            temperature=float(data["temperature"]),
            epsilon_cutoff=float(data["epsilonCutoff"]),
            num_beams=int(data["numBeams"]),
            num_gpu_layers_mt=int(data["numGpuLayersMt"]),
            num_gpu_layers_ocr=int(data["numGpuLayersOcr"]),
            decoding_mode=data["decodingMode"],
            max_length_a=max_length_a if max_length_a > 0 else 0,
            force_translation_cpu=data["forceTranslationCPU"],
            force_ner_cpu=data["forceNerCpu"],
            force_embeddings_cpu=data["forceEmbeddingsCpu"],
            force_spelling_correction_cpu=data["forceSpellingCorrectionCPU"],
            force_td_cpu=data["forceTdCpu"],
            force_tl_cpu=data["forceTlCpu"],
            memory_efficient_tasks=data["memoryEfficientTasks"],
            use_translation_server=data["useTranslationServer"],
            force_ocr_cpu=data["forceOcrCpu"],
            use_cuda=data["enableCuda"],
            n_context=c_amount,
            no_repeat_ngram_size=int(data["noRepeatNgramSize"]),
            stroke_size=float(data["strokeSize"]),
            bottom_text_only=data["bottomTextOnly"],
            ignore_thin_text=data["ignoreThinText"],
            detect_frames=data["detectFrames"],
            batch_ocr=data["batchOcr"],
            cut_ocr_punct=data["cutOcrPunct"],
            cache_mt=data["cacheMt"],
            ignore_detect_single_words=data["ignoreDetectSingleWords"],
            sort_text_from_top_left=data["sortTextFromTopLeft"],
            capture_window=data["captureWindow"],
            name_entries=data["nameEntries"],
            augment_name_entries=data["augmentNameEntries"],
            detect_speaker_name=data["detectSpeakerName"],
            sanitize_ascii=data["sanitizeAscii"],
        )

        config_state.update_terms(terms=data["terms"])

        context_state.reset_list()

        # Might lead to unnecessary loading but oh well
        if requires_reload:
            ctx.log("Reloading all models...")
            translate_pipeline.text_recognition_app.unload_all(do_collect=False)
            translate_pipeline.text_detection_app.unload_all(do_collect=False)
            translate_pipeline.reranking_app.unload_all(do_collect=False)
            translate_pipeline.translation_app.unload_all(do_collect=False)
            translate_pipeline.text_line_app.unload_all(do_collect=False)
            translate_pipeline.spell_correction_app.unload_all(do_collect=False)
            collect()
        else:
            ctx.log("NOT reloading all models!")

        try:
            print('DATA:')
            print(data)
            print('-----------------')
            ctx.log("Received config data", **data)
        except:
            ctx.log("Failed to log config data...")

        translate_pipeline.log_app_usage(ctx)

    return {}, 200


@app.route("/allowedmodels", methods=["GET"])
def get_allowed_models_route():
    with logger.begin_event("Retrieve allowed models") as ctx:
        tp = translate_pipeline
        switch_apps: List[SwitchApp] = [
            tp.text_line_app,
            tp.text_detection_app,
            tp.text_recognition_app,
            tp.translation_app,
            tp.reranking_app,
            tp.spell_correction_app,
            tp.image_cleaning_app,
            tp.image_redrawing_app,
        ]

        data = {}

        for sw in switch_apps:
            for module, module_name in sw.for_each_app():
                try:
                    data[module_name] = module.can_load()
                except:
                    data[module_name] = True

        ctx.log("Installed models", **data)

    return data

save_labels_path = os.path.expanduser("~/Documents/Mango/labels")
os.makedirs(save_labels_path, exist_ok=True)

@app.route("/recommendtranslation", methods=["POST"])
def recommend_translation_route():
    with logger.begin_event("Saving labeled translation preference data") as ctx:
        data = request.json
        item_id = uuid4().hex

        ctx.log("Received data", items=data["items"], recommended=data["recommended"], item_id=item_id)

        with open(os.path.join(save_labels_path, f"{item_id}.json"), "a", encoding="utf-8") as f:
            dat = {
                "items": data["items"],
                "recommended": data["recommended"],
            }

            json.dump(dat, f, ensure_ascii=False, indent=4)

    return {}, 200