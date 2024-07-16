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
        self.terms = []

    def set_decoding_params(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def update_terms(self, terms):
        self.terms = terms


config_state = ConfigState()
