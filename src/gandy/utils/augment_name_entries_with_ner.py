import json
from gandy.utils.fancy_logger import logger
from gandy.translation.name_agent import NameAgent

"""
This module is pretty nifty:
It utilizes an NER model to look for names in the source string and checks if they exist in a source-target dictionary file.
The idea is that users can supply a massive fudging bundle of names and let the gods figure it out.
Once names are found, they are converted into valid objects that can be used in conjunction with config_state.name_entries.
Ideally, the translation model will have some way to map these name entries for use in translation.
"""
class NameAdder():
    def __init__(self, agent: NameAgent):
        self.loaded = False
        self.agent = agent

        self.can_cuda = False

        self.memo = self.new_memo()

        with logger.begin_event("Loading conditional dictionary") as ctx:
            self.conditional_dictionary = self.load_conditional_dictionary()
            ctx.log("N entries loaded", n_entries=len(self.conditional_dictionary))

    def new_memo(self):
        return { 'src': None, 'output': None, }

    # No additional overhead; reuses same model from translator.
    def load_model(self):
        pass

    def unload_model(self):
        pass

    def get_dictionary_path(self):
        return f"models/ner/dictionary.json"

    def save_conditional_dictionary(self):
        with open(self.get_dictionary_path(), 'w', encoding='utf-8') as f:
            json.dump(self.conditional_dictionary, f, indent=2, ensure_ascii=False)

        self.memo = self.new_memo()

    def load_conditional_dictionary(self):
        try:
            with open(self.get_dictionary_path(), 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {} # File probably does not exist or is malformed in some fashion.

    def cut_honorifics(self, src: str):
        # TODO: Maybe only cut if a suffix.
        honorifics = { 'はん', '様', 'さま', 'さん', 'ちゃん', 'たん', 'くん', '先生', 'せんせい', '先輩', 'せんぱい', }

        for h in honorifics:
            src = src.replace(h, '').strip()

        return src
    
    def nlp(self, src: str):
        return self.agent.process(src)

    def get_names(self, src: str, entries_to_ignore, do_memo = True, socketio = None):
        if src == self.memo['src'] and do_memo:
            return self.memo['output']

        ents_to_ignore = [x['source'] for x in entries_to_ignore]
        with logger.begin_event('Augmenting name entries from dictionary file', src=src, ignoring_src_names=ents_to_ignore) as ctx:
            user_selected_sources = set(ents_to_ignore) # consistent dictionary entries.

            # Additional entries to return.
            extra_name_entries = []

            # Find all names in source text.
            identified_entries = self.nlp(src)
            n_new = 0 # If a new entry is identified NOT originally found in the conditional dictionary, save it to disk.

            for found_ent in identified_entries:
                found_ent["source"] = self.cut_honorifics(found_ent["source"])
                if found_ent["source"] in user_selected_sources:
                    continue

                # Save to conditional dictionary if it is a new name.
                if found_ent["source"] not in self.conditional_dictionary:
                    self.conditional_dictionary[found_ent["source"]] = found_ent
                    n_new += 1

                    if socketio is not None:
                        socketio.patched_emit('detected_missing_name', { 'source': found_ent["source"], 'target': found_ent["target"], 'gender': found_ent["gender"], })
                        socketio.sleep()

                # Use the entry from the conditional dictionary.
                extra_name_entries.append(self.conditional_dictionary[found_ent["source"]])

            if n_new > 0:
                self.save_conditional_dictionary()

            if len(extra_name_entries) > 0:
                ctx.log('Additional names added!', llm_entries=identified_entries, final_entries=extra_name_entries, n_additional=len(extra_name_entries))
            else:
                ctx.log('No additional names added.', final_entries=extra_name_entries)

            if do_memo:
                self.memo = {
                    'src': src,
                    'output': extra_name_entries,
                }

        return extra_name_entries