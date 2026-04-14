from gandy.translation.llmcpp_translation import LlmCppTranslationApp
from gandy.utils.fancy_logger import logger
from gandy.state.config_state import config_state
from typing import List
import json
import regex as re
import os
from gandy.database.faiss_mt_rag import TranslationRAG

"""

<modelname>.mango_config.json files should contain these field names with examples given:

- create_system_message: 
    "" (No system message made - make sure create_current_user_message is set up correctly in this case.)
    "file" (Instead, the model will read from "<modelname>.create_system_message.txt" in the same directory as the .mango_config.json file.)
    "Translate from Japanese to English.{{PREFIX_EACH_CONTEXT(\nContext: )}}\nSource to Translate: {{SOURCE}}"
    "Translate the source to English. {{IF_DICTIONARY_EXISTS(Use the dictionary to translate names as needed.\nDictionary:\n{{JOIN_EACH_DICTIONARY_NAME_PAIR(__FROM__ == __TO__ (__GENDER__)\n)}})}}\nSource to Translate: {{SOURCE}}"

- create_each_context_message:
    (This creates a user message for each context.)

    "" (No additional user messages made.)
    "file" (Instead, the model will read from "<modelname>.create_each_context_message.txt" in the same directory as the .mango_config.json file.)
    "Context: {{CONTEXT}}"

- create_current_user_message:
    "" (No user messages made - make sure create_system_message is set up correctly in this case.)
    "file" (Instead, the model will read from "<modelname>.create_current_user_message.txt" in the same directory as the .mango_config.json file.)
    "Translate: {{SOURCE}}"
    "{{JOIN_EACH_CONTEXT(\nContext: )}}\nTranslate: {{SOURCE}}"
    "{{PREFIX_EACH_CONTEXT(\nContext: )}}\nTranslate: {{SOURCE}}"

- create_assistant_prefix:
    "" (No text is "pre-fed" to the model. This is usually what you want.)
    "file" (Instead, the model will read from "<modelname>.create_assistant_prefix.txt" in the same directory as the .mango_config.json file.)
    "Sure! Here is the translation:"
    "<think>"
    "<think>\n</think>\n\n"

- extract_from_output:
    "" (No extraction done.)
    "Translated Text: (.+)"

- n_context (integer): Max amount of tokens that the model can parse - not to be confused with context inputs in Mango.

- stop_words (string | array of strings | null): Extra words/phrases to stop generation once reached.

As we can see, there are a few "operators" for templating purposes, like:
- {{LANGUAGE}}: If present, replaced with the "Language" string literal that the user enters in the option menu.
- {{PREFIX_EACH_CONTEXT(...)}}: This is used to prefix each context with a string.
- {{JOIN_EACH_CONTEXT(...)}}: This is used to join each context with a string (in other words: the first context is not prefixed, but the rest are).
- {{CONTEXT}}: This is used to insert the CURRENT source-side context sentence into the message. Should only be used in create_each_context_message.
- {{SOURCE}}: This is used to insert the source text into the message.
- {{IF_CONTEXT_EXISTS(...)}}: Only inserts the string if there is context.
- {{JOIN_EACH_DICTIONARY_NAME_PAIR(__FROM__ ... __TO__)}}: Users might specify how names or terms should be translated in the settings tab. You can decide if they should be mapped into the input somehow or not. __FROM__ is a string consisting of the I-th source term, and __TO__ is for the I-th target term.
- {{IF_DICTIONARY_EXISTS(...)}}: Only inserts the string if there is at least one entry in the dictionary.
- file: This is used to read the contents of a file in the same directory as the .mango_config.json file, with the same name as the field, but with a .txt extension instead of .mango_config.json.
    All the other templating operators can be used in the file as well.
    This does not work in extract_from_output, as it is not a message template, but rather a regex pattern.

Target-side context is not supported. Personally, I found them to dilute the model's attention.
"""

class CustomGgufTranslationApp(LlmCppTranslationApp):
    def __init__(self, model_sub_path="", prepend_fn=None, lang="", prepend_model_output=None, config_sub_path=None):
        super().__init__(model_sub_path, prepend_fn, lang, prepend_model_output)

        self.config_sub_path = config_sub_path or model_sub_path

        self.file_field_values = {}

        self.rag = None # Only used by certain models.

        # mango_config is loaded twice; once on model load and once on app startup (see model_apps).
        # model load = get fresh data juuuust in case the user changed something.
        # app startup = basic metadata info (model display name / description) for the UI.
        # The same logic applies to CustomGgufOcrApp.

    def get_mango_config_path(self):
        return f"{self.config_sub_path}.json"

    def locate_in_folder(self, file_name: str):
        return os.path.join(os.path.dirname(self.config_sub_path), file_name)

    def load_mango_config(self):
        with logger.begin_event("Loading Mango config") as ctx:
            with open(self.get_mango_config_path(), 'r', encoding='utf-8') as f:
                mango_config = json.load(f)
                ctx.log('Loaded Mango config', mango_config=mango_config)

        return mango_config

    def get_model_path_for_llmcpp(self):
        if self.model_sub_path == "config":
            return self.locate_in_folder(f"{self.mango_config['model_name']}.gguf")

        # TODO - below should never be called anyways.
        return os.path.join("models", "custom_translators", f"{self.model_sub_path}.gguf")

    def can_load(self):
        return os.path.exists(self.get_mango_config_path())
    
    def load_model(self):
        self.mango_config = self.load_mango_config()

        # Create the language-specific RAG database if possible.
        with logger.begin_event("Initializing RAG engine") as ctx:
            suffix = self.mango_config.get("rag_name", "") # "Japanese" | "Chinese" | "Korean" | ""

            ctx.log("Using RAG engine", suffix=suffix)
            self.rag = TranslationRAG(suffix)

            if not self.rag.data_file_exists():
                ctx.log("Defaulting to generic RAG engine as language-specific suffix does not exist!", suffix=suffix)
                self.rag = TranslationRAG("")

        return super().load_model(extra_commands=self.mango_config.get("extra_commands", []), extra_body=self.mango_config.get("extra_body", {}))
    
    def ignore_field(self, msg: str):
        return msg == "" or msg is None
    
    def get_field_value(self, msg: str):
        fv = self.mango_config[msg]

        do_strip = fv == "file"

        if fv == "file":
            if msg in self.file_field_values:
                return self.file_field_values[msg], do_strip # Cached.

            with open(self.locate_in_folder(f"{os.path.basename(self.config_sub_path.replace('.mango_config', ''))}.{msg}.txt"), 'r', encoding='utf-8') as f:
                fv = f.read().strip().replace("\\n", "\n")

                self.file_field_values[msg] = fv

        return fv, do_strip
    
    def map_contexts_template(self, contexts: List[str], sep, prefix = True):
        sep = sep.group(1)
        if sep is None or len(contexts) == 0:
            return ""

        if prefix:
            return sep + sep.join(contexts)
        return sep.join(contexts).rstrip()
    
    def map_if_context_exists(self, contexts: List[str], sep):
        if len(contexts) == 0:
            return ""
        return sep.group(1) if sep is not None else ""
    
    def map_dictionary_template(self, sep, translation_input: str, filter_entry):
        sep = sep.group(1) # Should be another string template in the form of "__FROM__ == __TO__"

        # The model used here (if augmented) will memorize the last input for name entries.
        # In other words: IF_DICTIONARY_EXISTS followed by MAP_DICTIONARY calls will actually only call the full NER pipeline once.
        name_entries = self.get_augmented_name_entries(translation_input)
        if sep is None or len(name_entries) == 0:
            return ""

        full_replacement = ""
        for entry in name_entries:
            if not filter_entry(entry):
                continue

            entry_sep = sep

            entry_sep = entry_sep.replace("__FROM__", entry["source"])
            entry_sep = entry_sep.replace("__TO__", entry["target"])

            mapped_gender = entry["gender"]
            if mapped_gender == "":
                mapped_gender = "N/A"

            entry_sep = re.sub(r"__IF_GENDER_EXISTS\((.*?)\)__", lambda m: m.group(1) if m is not None and mapped_gender != "N/A" else "", entry_sep, flags=re.DOTALL)
            entry_sep = entry_sep.replace("__GENDER__", mapped_gender)

            full_replacement += entry_sep

        return full_replacement.rstrip()
    
    def map_dictionary_template_gender_and_non_gender(self, sep, translation_input: str):
        # This is to collect ALL dictionary pairs - whether they have a gender specified or not.
        return self.map_dictionary_template(sep, translation_input, filter_entry=lambda x: True)
    
    def map_dictionary_template_only_gendered(self, sep, translation_input: str):
        return self.map_dictionary_template(sep, translation_input, filter_entry=lambda x: x["gender"] != "")

    def map_dictionary_template_only_non_gendered(self, sep, translation_input: str):
        return self.map_dictionary_template(sep, translation_input, filter_entry=lambda x: x["gender"] == "")

    def map_if_dictionary_exists(self, sep, translation_input):
        if len(self.get_augmented_name_entries(translation_input)) == 0:
            return ""
        return sep.group(1) if sep is not None else ""
    
    def map_rag_entries(self, sep: str, source: str):
        sep = sep.group(1) # Should be another string template in the form of "__SRC__ == __TGT__"

        similar_results = self.rag.get_entries(source)

        full_replacement = ''
        for r in similar_results:
            entry_sep = sep
            entry_sep = entry_sep.replace('__SRC__', r[0])
            entry_sep = entry_sep.replace('__TGT__', r[1])

            full_replacement += entry_sep

        return full_replacement.rstrip()
    
    def populate_template_str(self, msg: str, contexts: List[str], source: str):
        msg = re.sub(r"\{\{PREFIX_EACH_CONTEXT\((.*?)\)\}\}", lambda m: self.map_contexts_template(contexts, m), msg, flags=re.DOTALL)
        msg = re.sub(r"\{\{JOIN_EACH_CONTEXT\((.*?)\)\}\}", lambda m: self.map_contexts_template(contexts, m, prefix=False), msg, flags=re.DOTALL)

        # Must come before IF_EXISTS - order matters.
        msg = re.sub(r"\{\{JOIN_EACH_DICTIONARY_NAME_PAIR\((.*?)\)\}\}", lambda m: self.map_dictionary_template_gender_and_non_gender(m, source), msg, flags=re.DOTALL)

        msg = re.sub(r"\{\{JOIN_EACH_GENDERED_DICTIONARY_NAME_PAIR\((.*?)\)\}\}", lambda m: self.map_dictionary_template_only_gendered(m, source), msg, flags=re.DOTALL)

        msg = re.sub(r"\{\{JOIN_EACH_NON_GENDERED_DICTIONARY_NAME_PAIR\((.*?)\)\}\}", lambda m: self.map_dictionary_template_only_non_gendered(m, source), msg, flags=re.DOTALL)

        msg = re.sub(r"\{\{JOIN_EACH_RAG_ENTRY\((.*?)\)\}\}", lambda m: self.map_rag_entries(m, source), msg, flags=re.DOTALL)

        msg = re.sub(r"\{\{IF_CONTEXT_EXISTS\((.*?)\)\}\}", lambda m: self.map_if_context_exists(contexts, m), msg, flags=re.DOTALL)
        msg = re.sub(r"\{\{IF_DICTIONARY_EXISTS\((.*?)\)\}\}", lambda m: self.map_if_dictionary_exists(m, source), msg, flags=re.DOTALL)

        msg = msg.replace("{{SOURCE}}", source)
        msg = msg.replace("{{LANGUAGE}}", config_state.output_language)

        # This should ideally only happen in map_each_context_message.
        if len(contexts) > 0:
            msg = msg.replace("{{CONTEXT}}", contexts[0])

        return msg

    def map_system_message(self, contexts: List[str], source: str):
        field, do_strip = self.get_field_value("create_system_message")
        if self.ignore_field(field):
            return []
        
        mapped = self.populate_template_str(field, contexts, source)
        if do_strip:
            mapped = mapped.strip()
        mapped = [mapped]

        return [{ "role": "system", "content": m, } for m in mapped]
    
    def map_each_context_message(self, contexts: List[str], source: str):
        field, do_strip = self.get_field_value("create_each_context_message")
        if self.ignore_field(field):
            return []

        messages = []
        for context in contexts:
            mapped = self.populate_template_str(field, [context], source)
            if do_strip:
                mapped = mapped.strip()
            messages.append(mapped)
    
        return [{ "role": "user", "content": m, } for m in messages]

    def map_current_user_message(self, contexts: List[str], source: str):
        field, do_strip = self.get_field_value("create_current_user_message")
        if self.ignore_field(field):
            return []

        mapped = self.populate_template_str(field, contexts, source)
        if do_strip:
            mapped = mapped.strip()
        mapped = [mapped]
    
        return [{ "role": "user", "content": m, } for m in mapped]

    def map_assistant_prefix(self, contexts: List[str], source: str):
        field, do_strip = self.get_field_value("create_assistant_prefix")
        if self.ignore_field(field):
            return []

        mapped = self.populate_template_str(field, contexts, source)
        if do_strip:
            mapped = mapped.strip()
        mapped = [mapped]

        return [{ "role": "assistant", "content": m, } for m in mapped]

    def create_messages(self, inp: str):
        with logger.begin_event("Splitting input & contexts") as ctx:
            inp, contexts = self.remap_input_with_contexts(inp)

            ctx.log('Done splitting', original_input=inp, cur_text=inp, contexts=contexts)

        with logger.begin_event("Creating list of messages from Mango config template") as ctx:
            messages = []
            messages += self.map_system_message(contexts, inp)
            messages += self.map_each_context_message(contexts, inp)
            messages += self.map_current_user_message(contexts, inp)
            messages += self.map_assistant_prefix(contexts, inp)

            ctx.log('Done creating list of messages', messages=messages)

        return messages
    
    def remove_other_words(self, output: str):
        rw = self.mango_config.get("remove_words", [])
        if rw is None or len(rw) == 0 or not isinstance(rw, list):
            return output

        for r in rw:
            output = output.replace(r, "")
        output = output.strip()

        return output

    def remove_stop_words(self, output: str):
        output = self.remove_other_words(output)

        sw = self.get_stop_words()
        if sw is None or len(sw) == 0:
            return output
        
        if isinstance(sw, str):
            sw = [sw]

        for stop in sw:
            output = output.rsplit(stop, maxsplit=1)[0].strip()
        return output

    def misc_postprocess_extract(self, output: str):
        if self.ignore_field(self.mango_config["extract_from_output"]):
            return self.remove_stop_words(output)

        with logger.begin_event(f"Extracting translation from output according to config") as ctx:
            try:
                initial = output
                output = re.search(self.mango_config["extract_from_output"], output, flags=re.DOTALL).group(1)
                ctx.log(f"Extracted", initial=initial, extracted=output)

                return self.remove_stop_words(output).strip()
            except:
                keep_empty = self.mango_config.get("keep_empty_extraction", False)
                ctx.log(f"Failed to find extraction.", keep_empty_extraction=keep_empty)

                if keep_empty:
                    return self.remove_stop_words("")

                return self.remove_stop_words(output).strip()
            
    def misc_postprocess(self, output):
        output = self.misc_postprocess_extract(output)

        if config_state.shorten_translations:
            # A neat thing about the shortener is that it only sees the translation output (English) - so it works regardless of the input language.
            with logger.begin_event("Shortening translation", before=output) as ctx:
                output = self.shortener.process(output)
                ctx.log("Done shortening", after=output)

        return output

    def get_n_context(self):
        return int(self.mango_config["n_context"])

    def get_stop_words(self):
        stops = self.mango_config["stop_words"]
        if len(stops) == 0:
            stops = None
