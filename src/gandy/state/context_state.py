from typing import List
from gandy.utils.get_sep_regex import get_last_sentence


class ContextState:
    def __init__(self):
        self.prev_source_text_list = []
        self.prev_target_text_list = []

        self.cur_used_max_context = None

    def reset_list(self):
        self.prev_source_text_list = []
        self.prev_target_text_list = []

        self.cur_used_max_context = None

    def update_list(self, text_list: List[str], text: str, max_context: int):
        if (
            self.cur_used_max_context != max_context
            and self.cur_used_max_context is not None
        ):
            # If the context amount changed, reset the list.
            self.prev_source_text_list = []
            self.prev_target_text_list = []
            text_list = []
        self.cur_used_max_context = max_context

        if max_context is None:
            raise RuntimeError("max_context must be given.")

        text_list = text_list + [text]

        # max_context from translation app is the count for contextual sentences + current sentence. (so 1 context and 1 current would be 2).
        # Whereas ContextState is only concerned with the context sentence count, so we subtract max_context by 1.
        if len(text_list) > (max_context - 1):
            text_list = text_list[1:]

        return text_list

    def update_source_list(self, text: str, max_context: int):
        text = get_last_sentence(text)  # Strip out any context.

        self.prev_source_text_list = self.update_list(
            self.prev_source_text_list, text, max_context
        )

    def update_target_list(self, text: str, max_context: int):
        self.prev_target_text_list = self.update_list(
            self.prev_target_text_list, text, max_context
        )


# Used for task3 and task2 (clipboard copying with OCR box)
context_state = ContextState()
