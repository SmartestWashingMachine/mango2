from transformers import AutoTokenizer, pipeline
from optimum.onnxruntime import ORTModelForTokenClassification
import json
from gandy.state.config_state import config_state
from gandy.utils.fancy_logger import logger
import os

DO_SAVE_MISSING_NAMES = True

def ceil(n):
    return int(-1 * n // 1 * -1)

def get_matches_from_dict(name: str, data_dict, min_possible_name_fract = 0.5, splitting_strategy = "chunk"):
    found = []

    if name in data_dict:
        for target in data_dict[name]:
            found.append({ "source": name, "target": target["name"], "gender": target["gender"], })
        return found


    # Otherwise create a bunch of possible names with the sliding window approach. I think this is the best way to go about this.
    # ... not the fastest though. Let's not go into big O. I don't want to think about it.
    # The other possibility could be to use another RAG pipeline I guess?
    if min_possible_name_fract < 1.0:
        possible_names = []

        if splitting_strategy == "sliding_window":
            for start_i in range(0, len(name) - 1):
                end_point = len(name) if start_i == 0 else len(name) + 1 # So we don't re-include the full name as we know it does not exist.

                for end_i in range(start_i + 1, end_point):
                    candidate = name[start_i:end_i]

                    # Only add possible names that are about half (default parameter value = 0.5) the size of the original name.
                    candidate_coverage = len(candidate) / len(name)
                    if candidate_coverage >= min_possible_name_fract:
                        possible_names.append(candidate)
        elif splitting_strategy == "chunk":
            chunk_n = ceil(len(name) * min_possible_name_fract)
            possible_names = [name[i:i+chunk_n] for i in range(0, len(name), chunk_n)]
        else:
            raise RuntimeError('Invalid splitting strategy given.')

        for p in possible_names:
            if p in data_dict:
                for target in data_dict[p]:
                    found.append({ "source": p, "target": target["name"], "gender": target["gender"], })

    return found

# TODO: Verify load/unload support.
"""
This module is pretty nifty:
It utilizes an NER model to look for names in the source string and checks if they exist in a source-target dictionary file.
The idea is that users can supply a massive fudging bundle of names and let the gods figure it out.
Once names are found, they are converted into valid objects that can be used in conjunction with config_state.name_entries.
Ideally, the translation model will have some way to map these name entries for use in translation.
"""
class NameAdder():
    def __init__(self, onnx_path: str = "models/ner/base"):
        self.loaded = False
        self.onnx_path = onnx_path

        # Shares similar conditions to the translation module.
        self.can_cuda = config_state.use_cuda and not config_state.force_translation_cpu

        self.memo = { 'src': None, 'output': None, }

    def load_model(self):
        if self.loaded:
            return

        # Need to use_fast=False - there's a version compatibility issue (see: https://github.com/huggingface/transformers/issues/31789)
        tokenizer = AutoTokenizer.from_pretrained(self.onnx_path, use_fast=False)

        self.model = ORTModelForTokenClassification.from_pretrained(self.onnx_path, provider=self.get_provider(self.can_cuda))
        self.nlp = pipeline("token-classification", model=self.model, tokenizer=tokenizer, aggregation_strategy="simple", device=self.get_device(self.can_cuda))

        with open(self.get_dictionary_path(), encoding='utf-8') as f:
            self.data_dict = json.load(f)

        self.loaded = True

    def unload_model(self):
        try:
            del self.nlp
            del self.model
            del self.data_dict
        except:
            pass

        self.nlp = None
        self.model = None
        self.data_dict = None
        self.loaded = False

    def get_missing_dictionary_path(self):
        return f"models/ner/missing_dictionary.json"

    def save_missing_dictionary(self, missing_data):
        missing_path = self.get_missing_dictionary_path()

        if os.path.exists(missing_path):
            with open(missing_path, encoding='utf-8') as f:
                existing_missing_data = json.load(f)
        else:
            existing_missing_data = {}

        # The user might have already updated some entries in the missing dictionary - we don't want to "reset" those entries.
        for k in missing_data:
            if k not in existing_missing_data:
                existing_missing_data[k] = missing_data[k]

        with open(missing_path, 'w', encoding='utf-8') as f:
            json.dump(existing_missing_data, f, indent=2, ensure_ascii=False)

    def cut_honorifics(self, src: str):
        # TODO: Maybe only cut if a suffix.
        honorifics = { 'はん', '様', 'さま', 'さん', 'ちゃん', 'たん', 'くん', '先生', 'せんせい', '先輩', 'せんぱい', }

        for h in honorifics:
            src = src.replace(h, '').strip()

        return src

    def get_names(self, src: str, entries_to_ignore, add_empty = False, do_memo = True):
        if not self.loaded:
            self.load_model()

        if src == self.memo['src'] and do_memo:
            return self.memo['output']

        ents_to_ignore = [x['source'] for x in entries_to_ignore]
        with logger.begin_event('Augmenting name entries from dictionary file', src=src, ignoring_src_names=ents_to_ignore) as ctx:
            user_selected_sources = set(ents_to_ignore)

            # Currently just for JA.
            output = self.nlp(src)
            extracted = [entity['word'] for entity in output if entity['entity_group'] == 'PER']

            if DO_SAVE_MISSING_NAMES:
                missing_names = {}
                do_resave_missing_dictionary = False

            extra_name_entries = []
            for extr in extracted:
                extr_no_honor = self.cut_honorifics(extr)
                founds = get_matches_from_dict(extr_no_honor, self.data_dict, min_possible_name_fract=0.5, splitting_strategy="chunk")
                was_initially_empty = len(founds) == 0

                founds = [f for f in founds if f['source'] not in user_selected_sources]
                extra_name_entries.extend(founds)

                if was_initially_empty and add_empty:
                    # For use in Task8.
                    extra_name_entries.append({ 'source': extr_no_honor, 'target': '???', 'gender': '', })

                ctx.log(f'Found matches', processed_ner_word=extr_no_honor, original_ner_word=extr, found=founds)

                if DO_SAVE_MISSING_NAMES:
                    if was_initially_empty:
                        missing_names[extr_no_honor] = [{ 'name': '', 'gender': '', }]

                        do_resave_missing_dictionary = True

            if do_resave_missing_dictionary:
                # A missing name was added.
                ctx.log(f'Saving missing dictionary with potential new names.', missing_names=list(missing_names.keys()))
                self.save_missing_dictionary(missing_names)

            if len(extra_name_entries) > 0:
                ctx.log('Additional names added!', ner_detected=len(extracted), ner_words=extracted, n_additional=len(extra_name_entries))
            else:
                ctx.log('No additional names added.', ner_detected=len(extracted), ner_words=extracted)

            if do_memo:
                self.memo = {
                    'src': src,
                    'output': extra_name_entries,
                }

        return extra_name_entries

    def get_device(self, can_cuda: bool):
        if can_cuda:
            return "cuda:0"
        return "cpu"
    
    def get_provider(self, can_cuda: bool):
        if can_cuda:
            return "CUDAExecutionProvider"
        return "CPUExecutionProvider"

    def get_dictionary_path(self):
        return f"models/ner/dictionary.json"