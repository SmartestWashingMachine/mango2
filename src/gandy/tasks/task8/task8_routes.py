from flask import request
from gandy.app import app, translate_pipeline, socketio
from gandy.state.config_state import config_state
from gandy.utils.fancy_logger import logger

# Task8 - Get names from NER module and return them in a visually appealing format.
# Used in TextView.

@app.route("/processtask8", methods=["POST"])
def process_task8_route():
    with logger.begin_event("Task8") as ctx:
        try:
            data = request.json
            text = data["text"]

            # Hacky. TODO
            no_ctx_inp = text.split('<TSOS>')[-1].strip()
            aug_entries = translate_pipeline.translation_app.get_sel_app().name_adder.get_names(no_ctx_inp, config_state.name_entries, add_empty=True, do_memo=False)
            out_name_entries = config_state.name_entries + aug_entries

            out_text = []
            out_ms = set() # Only show the first source match for each source.
            for o in out_name_entries:
                if o["source"] in out_ms:
                    continue
                out_ms.add(o["source"])

                out_text.append(f"{o['source']} == {o['target']}")

            out_text = " || ".join(out_text).strip()
            if len(out_text) == 0:
                out_text = "No names found."

            data_to_send = {
                "text": [out_text],
                "sourceText": text,
                "boxId": "",
            }
            socketio.patched_emit(
                "done_translating_task8",
                data_to_send,
            )
            socketio.sleep()

            return out_text, 200
        except Exception:
            logger.log("Task8 Error")
            logger.event_exception(ctx)

            socketio.patched_emit("done_translating_task8", {})

            return 'ERROR', 400
