from flask import request
from gandy.app import app, translate_pipeline
from gandy.state.config_state import config_state
from gandy.state.context_state import context_state
from gandy.utils.fancy_logger import logger
from gandy.full_pipelines.switch_app import SwitchApp
from typing import List


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

        translate_pipeline.translation_app.select_app(data["translationModelName"])
        translate_pipeline.text_recognition_app.select_app(
            data["textRecognitionModelName"]
        )
        translate_pipeline.text_detection_app.select_app(data["textDetectionModelName"])
        translate_pipeline.spell_correction_app.select_app(
            data["spellCorrectionModelName"]
        )

        reranking_model_name = data["rerankingModelName"]
        decoding_mode = data["decodingMode"]

        # Set OCR preprocessor.
        translate_pipeline.text_line_app.select_app(data["textLineModelName"])

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

                translate_pipeline.reranking_app.select_app(reranking_model_name)
            else:
                ctx.log(
                    f"Unsupported language detected for reranking - disabling reranking"
                )
                translate_pipeline.reranking_app.select_app("none")
        else:
            ctx.log(f"Using beam search mode - reranking disabled.")
            translate_pipeline.reranking_app.select_app("none")

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

        config_state.set_decoding_params(
            top_p=float(data["topP"]),
            top_k=data["topK"],
            length_penalty=float(data["lengthPenalty"]),
            repetition_penalty=float(data["repetitionPenalty"]),
            temperature=float(data["temperature"]),
            epsilon_cutoff=float(data["epsilonCutoff"]),
            num_beams=int(data["numBeams"]),
            decoding_mode=data["decodingMode"],
            max_length_a=max_length_a if max_length_a > 0 else 0,
            force_translation_cpu=data["forceTranslationCPU"],
            force_td_cpu=data["forceTdCpu"],
            force_tl_cpu=data["forceTlCpu"],
            force_ocr_cpu=data["forceOcrCpu"],
            use_cuda=data["enableCuda"],
            n_context=c_amount,
            no_repeat_ngram_size=int(data["noRepeatNgramSize"]),
            stroke_size=float(data["strokeSize"]),
            bottom_text_only=data["bottomTextOnly"],
            batch_ocr=data["batchOcr"],
            cut_ocr_punct=data["cutOcrPunct"],
            ignore_detect_single_words=data["ignoreDetectSingleWords"],
            sort_text_from_top_left=data["sortTextFromTopLeft"]
        )

        config_state.update_terms(terms=data["terms"])

        context_state.reset_list()

        ctx.log("Received config data", **data)
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
