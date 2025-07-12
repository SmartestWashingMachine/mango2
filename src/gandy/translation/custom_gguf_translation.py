from gandy.translation.llmcpp_translation import LlmCppTranslationApp
from gandy.utils.fancy_logger import logger
from gandy.state.config_state import config_state
from typing import List
import json
import regex as re
import os

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

As we can see, there are a few "operators" for templating purposes:
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
- file_no_strip: Similar to "file", but does not strip any whitespace from the beginning and end of the file contents. This should almost never be used.

Target-side context is not supported. Personally, I found them to dilute the model's attention.
"""

class CustomGgufTranslationApp(LlmCppTranslationApp):
    def get_mango_config_path(self):
        return f"models/custom_translators/{self.model_sub_path}" + ".mango_config.json"
    
    def load_mango_config(self):
        with logger.begin_event("Loading Mango config") as ctx:
            with open(self.get_mango_config_path(), 'r', encoding='utf-8') as f:
                mango_config = json.load(f)
                ctx.log('Loaded Mango config', mango_config=mango_config)

        return mango_config

    def get_model_path_for_llmcpp(self):
        return os.path.join("models", "custom_translators", f"{self.model_sub_path}.gguf")

    def can_load(self):
        return True
    
    def load_model(self):
        self.mango_config = self.load_mango_config()

        return super().load_model()
    
    def ignore_field(self, msg: str):
        return msg == "" or msg is None
    
    def get_field_value(self, msg: str):
        fv = self.mango_config[msg]

        if fv == "file" or fv == "file_no_strip":
            with open(f"models/custom_translators/{self.model_sub_path}.{msg}.txt", 'r', encoding='utf-8') as f:
                fv = f.read().replace("\\n", "\n")
        if fv == "file_no_strip":
            fv = fv.strip()

        return fv
    
    def map_contexts_template(self, contexts: List[str], sep, prefix = True):
        sep = sep.group(1)
        if sep is None or len(contexts) == 0:
            return ""

        if prefix:
            return sep + sep.join(contexts)
        return sep.join(contexts)
    
    def map_if_context_exists(self, contexts: List[str], sep):
        if len(contexts) == 0:
            return ""
        return sep.group(1) if sep is not None else ""
    
    def map_dictionary_template(self, sep):
        sep = sep.group(1) # Should be another string template in the form of "__FROM__ == __TO__"
        if sep is None or len(config_state.name_entries) == 0:
            return ""

        full_replacement = ""
        for entry in config_state.name_entries:
            entry_sep = sep

            entry_sep = entry_sep.replace("__FROM__", entry["source"])
            entry_sep = entry_sep.replace("__TO__", entry["target"])

            mapped_gender = entry["gender"]
            if mapped_gender == "":
                mapped_gender = "N/A"
            entry_sep = entry_sep.replace("__GENDER__", mapped_gender)

            full_replacement += entry_sep

        return full_replacement
    
    def map_if_dictionary_exists(self, sep):
        if len(config_state.name_entries) == 0:
            return ""
        return sep.group(1) if sep is not None else ""
    
    def populate_template_str(self, msg: str, contexts: List[str], source: str):
        msg = re.sub(r"\{\{PREFIX_EACH_CONTEXT\((.*?)\)\}\}", lambda m: self.map_contexts_template(contexts, m), msg, flags=re.DOTALL)
        msg = re.sub(r"\{\{JOIN_EACH_CONTEXT\((.*?)\)\}\}", lambda m: self.map_contexts_template(contexts, m, prefix=False), msg, flags=re.DOTALL)

        msg = re.sub(r"\{\{IF_CONTEXT_EXISTS\((.*?)\)\}\}", lambda m: self.map_if_context_exists(contexts, m), msg, flags=re.DOTALL)
        msg = re.sub(r"\{\{IF_DICTIONARY_EXISTS\((.*?)\)\}\}", lambda m: self.map_if_dictionary_exists(m), msg, flags=re.DOTALL)

        msg = re.sub(r"\{\{JOIN_EACH_DICTIONARY_NAME_PAIR\((.*?)\)\}\}", lambda m: self.map_dictionary_template(m), msg, flags=re.DOTALL)

        msg = msg.replace("{{SOURCE}}", source)

        # This should ideally only happen in map_each_context_message.
        if len(contexts) > 0:
            msg = msg.replace("{{CONTEXT}}", contexts[0])

        return msg

    def map_system_message(self, contexts: List[str], source: str):
        field = self.get_field_value("create_system_message")
        if self.ignore_field(field):
            return []
        
        mapped = self.populate_template_str(field, contexts, source)
        mapped = [mapped]

        return [{ "role": "system", "content": m, } for m in mapped]
    
    def map_each_context_message(self, contexts: List[str], source: str):
        field = self.get_field_value("create_each_context_message")
        if self.ignore_field(field):
            return []

        messages = []
        for context in contexts:
            mapped = self.populate_template_str(field, [context], source)
            messages.append(mapped)
    
        return [{ "role": "user", "content": m, } for m in messages]

    def map_current_user_message(self, contexts: List[str], source: str):
        field = self.get_field_value("create_current_user_message")
        if self.ignore_field(field):
            return []

        mapped = self.populate_template_str(field, contexts, source)
        mapped = [mapped]
    
        return [{ "role": "user", "content": m, } for m in mapped]

    def map_assistant_prefix(self, contexts: List[str], source: str):
        field = self.get_field_value("create_assistant_prefix")
        if self.ignore_field(field):
            return []

        mapped = self.populate_template_str(field, contexts, source)
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
    
    def remove_stop_words(self, output: str):
        sw = self.get_stop_words()
        if sw is None or len(sw) == 0:
            return output
        
        if isinstance(sw, str):
            sw = [sw]

        for stop in sw:
            output = output.rsplit(stop, maxsplit=1)[0].strip()
        return output

    def misc_postprocess(self, output: str):
        if self.ignore_field(self.mango_config["extract_from_output"]):
            return self.remove_stop_words(output)

        try:
            output = re.search(self.mango_config["extract_from_output"], output, flags=re.DOTALL).group(1)

            return self.remove_stop_words(output)
        except:
            return self.remove_stop_words(output)

    def get_n_context(self):
        return int(self.mango_config["n_context"])

    def get_stop_words(self):
        return self.mango_config["stop_words"]