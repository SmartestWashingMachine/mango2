class ConfigState:
    def __init__(self) -> None:
        self.decoding_mode = "beam"
        self.top_p = 0
        self.top_k = 0
        self.length_penalty = 1.0
        self.repetition_penalty = 1.2
        self.temperature = 1.0
        self.epsilon_cutoff = 0.0
        self.num_beams = 5
        self.force_translation_cpu = False
        self.force_td_cpu = False
        self.max_length_a = 0
        self.no_repeat_ngram_size = 5

        self.n_context = 1

        self.use_cuda = False

        # self.terms = []
        self.source_terms = []
        self.target_terms = []

        self.stroke_size = 8

        self.bottom_text_only = False

        self.tile_width = 100
        self.tile_height = 100

        self.batch_ocr = False
        self.cut_ocr_punct = False
        self.ignore_detect_single_words = False

        self._temp_circuit_broken = False # TODO: Use separate state for this.

    def set_decoding_params(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    # on_side == "source" || "target"
    def find_terms(self, terms, on_side: str):
        return [t for t in terms if (t.get("enabled", False) and t["onSide"] == on_side)]

    def update_terms(self, terms):
        self.source_terms = self.find_terms(terms, on_side="source")
        self.target_terms = self.find_terms(terms, on_side="target")


config_state = ConfigState()
