from gandy.translation.llmcpp_translation import LlmCppTranslationApp
from gandy.utils.fancy_logger import logger
from typing import List
import json
import regex as re
import os

"""

<modelname>.mango_config.json files should contain these field names with examples given:

- create_system_message: 
    "" (No system message made - make sure create_current_user_message is set up correctly in this case.)
    "Translate from Japanese to English.{{PREFIX_EACH_CONTEXT(\nContext: )}}\nSource to Translate: {{SOURCE}}"

- create_each_context_message:
    (This creates a user message for each context.)

    "" (No additional user messages made.)
    "Context: {{CONTEXT}}"

- create_current_user_message:
    "" (No user messages made - make sure create_system_message is set up correctly in this case.)
    "Translate: {{SOURCE}}"
    "{{JOIN_EACH_CONTEXT(\nContext: )}}\nTranslate: {{SOURCE}}"
    "{{PREFIX_EACH_CONTEXT(\nContext: )}}\nTranslate: {{SOURCE}}"

- create_assistant_prefix:
    "" (No text is "pre-fed" to the model. This is usually what you want.)
    "Sure! Here is the translation:"
    "<think>"
    "<think>\n</think>\n\n"

- extract_from_output:
    "" (No extraction done.)
    "Translated Text: (.+)"

- n_context (integer): Max amount of tokens that the model can parse - not to be confused with context inputs in Mango.

As we can see, there are a few "operators" for templating purposes:
- {{PREFIX_EACH_CONTEXT(...)}}: This is used to prefix each context with a string.
- {{JOIN_EACH_CONTEXT(...)}}: This is used to join each context with a string (in other words: the first context is not prefixed, but the rest are).
- {{CONTEXT}}: This is used to insert the CURRENT source-side context sentence into the message. Should only be used in create_each_context_message.
- {{SOURCE}}: This is used to insert the source text into the message.
- {{IF_CONTEXT_EXISTS(...)}}: Only inserts the string if there is context.

Target-side context is not supported. Personally, I found them to dilute the model's attention.
"""

class CustomGgufTranslationApp(LlmCppTranslationApp):
    def get_mango_config_path(self):
        return f"models/custom_translators/{self.model_sub_path}" + ".mango_config.json"
    
    def load_mango_config(self):
        with open(self.get_mango_config_path(), 'r', encoding='utf-8') as f:
            mango_config = json.load(f)

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
    
    def populate_template_str(self, msg: str, contexts: List[str], source: str):
        msg = re.sub(r"\{\{PREFIX_EACH_CONTEXT\((.*?)\)\}\}", lambda m: self.map_contexts_template(contexts, m), msg)
        msg = re.sub(r"\{\{JOIN_EACH_CONTEXT\((.*?)\)\}\}", lambda m: self.map_contexts_template(contexts, m, prefix=False), msg)

        msg = re.sub(r"\{\{IF_CONTEXT_EXISTS\((.*?)\)\}\}", lambda m: self.map_if_context_exists(contexts, m), msg)

        msg = msg.replace("{{SOURCE}}", source)

        # This should ideally only happen in map_each_context_message.
        if len(contexts) > 0:
            msg = msg.replace("{{CONTEXT}}", contexts[0])

        return msg

    def map_system_message(self, contexts: List[str], source: str):
        field: str = self.mango_config["create_system_message"]
        if self.ignore_field(field):
            return []
        
        mapped = self.populate_template_str(field, contexts, source)
        mapped = [mapped]

        return [{ "role": "system", "content": m, } for m in mapped]
    
    def map_each_context_message(self, contexts: List[str], source: str):
        field: str = self.mango_config["create_each_context_message"]
        if self.ignore_field(field):
            return []

        messages = []
        for context in contexts:
            mapped = self.populate_template_str(field, [context], source)
            messages.append(mapped)
    
        return [{ "role": "user", "content": m, } for m in messages]

    def map_current_user_message(self, contexts: List[str], source: str):
        field: str = self.mango_config["create_current_user_message"]
        if self.ignore_field(field):
            return []

        mapped = self.populate_template_str(field, contexts, source)
        mapped = [mapped]
    
        return [{ "role": "user", "content": m, } for m in mapped]

    def map_assistant_prefix(self, contexts: List[str], source: str):
        field: str = self.mango_config["create_assistant_prefix"]
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

    def misc_postprocess(self, output: str):
        if self.ignore_field(self.mango_config["extract_from_output"]):
            return output

        try:
            return re.search(self.mango_config["extract_from_output"], output).group(1)
        except:
            return output

    def get_n_context(self):
        return int(self.mango_config.get("n_context"))
