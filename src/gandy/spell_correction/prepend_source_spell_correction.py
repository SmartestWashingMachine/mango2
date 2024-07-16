from gandy.spell_correction.base_spell_correction import BaseSpellCorrection


class PrependSourceApp(BaseSpellCorrection):
    def process(self, translation_input, texts):
        return f"{translation_input[-1]} // {texts}"


class PrependSourceNoContextApp(BaseSpellCorrection):
    def process(self, translation_input, texts, *args, **kwargs):
        return f"{translation_input[-1].split('<TSOS>')[-1].strip()} // {texts}"
