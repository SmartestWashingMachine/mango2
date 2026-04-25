from gandy.translation.llama_server_wrapper import LlamaCppExecutableOpenAIClient
from gandy.utils.fancy_logger import logger
from gandy.state.config_state import config_state
import regex as re

def extract_structured_entities(text):
    # 1. Extract the block between tags (re.S handles newlines)
    block_match = re.search(r'<dictionary>(.*?)</dictionary>', text, flags=re.S)
    if not block_match:
        return []

    content = block_match.group(1).strip()
    results = []

    for line in content.splitlines():
        if '=' not in line:
            continue

        # Split into Original Key and English Value
        raw_key, raw_val = line.split('=', 1)
        original_text = raw_key.strip()
        full_value = raw_val.strip()

        # 2. Extract English Name and Gender using Regex
        # Matches "Name (Gender)" or just "Name"
        # Pattern: captures everything until a space + '(' or end of string
        gender_match = re.search(r'\((Male|Female|Non-binary)\)', full_value, re.I)

        # Clean the name by removing the (Gender) part if it exists
        name_only = re.sub(r'\(.*?\)', '', full_value).strip()

        gender = gender_match.group(1) if gender_match else ""

        results.append({
            "source": original_text,
            "target": name_only,
            "gender": gender
        })

    return results

PROMPT = """
Given a source text, identify entity names and their sex or gender (if possible), outputting them within a <dictionary></dictionary> tag in a specific format. For example:

<dictionary>
健二 = Kenji (Male)
桜 = Sakura (Female)
楽天 = Rakuten
</dictionary>

Source Text:
{input_source}
""".strip()

class NameAgent():
    def __init__(self, llm: LlamaCppExecutableOpenAIClient):
        self.llm = llm # Uses same model as translator for now.

    def map_prompt(self, inp: str):
        return PROMPT.replace("{input_source}", inp.strip())
    
    def extract_from_source(self, inp: str):
        with logger.begin_event("Splitting input & contexts") as ctx:
            inp = inp.split("<TSOS>")[-1].strip()
            ctx.log('Done splitting', original_input=inp, cur_text=inp)

        with logger.begin_event("Creating prompt from splits") as ctx:
            prompt = self.map_prompt(inp)
            ctx.log('Done creating prompt', prompt=prompt)

        with logger.begin_event("Feeding to LLM") as ctx:
            messages = [
                { "role": "user", "content": prompt, },
            ]
            ctx.log('Full messages for spelling correction', messages=messages)

            raw_prediction = self.llm.call_llm_no_batch(messages, use_stream=None)
            ctx.log("Full prediction before extraction", prediction=raw_prediction)

            prediction = extract_structured_entities(raw_prediction)
            ctx.log("Full prediction after extraction", prediction=prediction)

        return prediction
    
    def process(
        self,
        text: str = None,
        use_stream=None,
    ):
        with logger.begin_event("Finding names in source text using name agent", using_stream=use_stream is not None) as ctx:

            if len(text) > 0 and not text.endswith("<TSOS>"):
                output = self.extract_from_source(text) # list of entries

                ctx.log(
                    f"Found name entries from name agent LLM call",
                    input_text=text,
                    extracted=output,
                )
            else:
                ctx.log(f"Poor text found. doing nothing... (no additional names)")
                output = []

        return output