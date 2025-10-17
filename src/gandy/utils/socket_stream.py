from gandy.app import socketio
from gandy.state.config_state import config_state
from gandy.utils.replace_terms import replace_many

class SocketStreamer():
    def __init__(
        self, tokenizer=None, skip_prompt: bool = False, box_id=None, metadata={}, **decode_kwargs
    ):
        decode_kwargs["skip_special_tokens"] = True

        self.box_id = box_id
        self.old_text = None
        self.metadata = metadata

        self.postprocess_before_sending = lambda s: s

        self.token_cache = []

    # This is a slightly more optimized put for our models.
    # Most code from TextStreamer.
    def optimized_put(self, value, replace=False, already_detokenized=False):
        """
        Receives tokens, decodes them, and prints them to stdout as soon as they form entire words.
        """
        # Add the new token to the cache and decodes the entire thing.
        if already_detokenized:
            # Used by the LLM translation app. It deals with text strings rather than tokens.
            self.token_cache.append(value)

            text = "".join(self.token_cache)
        else:
            raise RuntimeError("already_detokenized should always be True as Pytorch is no longer used in this app.")

        printable_text = text

        self.on_finalized_text(printable_text)

    def put(self, value, replace=False, already_detokenized=False):
        # We send all tokens at every put() since websockets are unreliable - packets can be dropped (yes, even on localhost).
        self.print_len = 0  # Comment this line if we only want to emit the next token.
        return self.optimized_put(value, replace=replace, already_detokenized=already_detokenized)

    def on_finalized_text(self, text: str, stream_end: bool = False):
        if stream_end:
            return

        # Note: This snippet may introduce some bugs.
        if text == self.old_text:
            return
        self.old_text = text

        text = replace_many(text, config_state.target_terms, ctx=None)
        text = self.postprocess_before_sending(text)

        data_to_send = {
            "text": text,
            "boxId": self.box_id,
            "sourceText": [],
            **self.metadata,
        }

        # This is where the "magic" happens.
        socketio.patched_emit(
            "item_stream",
            data_to_send,
        )
        socketio.sleep()

    def __repr__(self) -> str:
        return f"SocketStreamer(box_id='{self.box_id}')"

    def __str__(self) -> str:
        return f"SocketStreamer(box_id='{self.box_id}')"
