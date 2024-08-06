from transformers.generation.streamers import TextStreamer
from gandy.app import socketio
from gandy.state.config_state import config_state
from gandy.utils.replace_terms import replace_many

class SocketStreamer(TextStreamer):
    def __init__(
        self, tokenizer=None, skip_prompt: bool = False, box_id=None, **decode_kwargs
    ):
        decode_kwargs["skip_special_tokens"] = True

        super().__init__(tokenizer, skip_prompt, **decode_kwargs)

        self.box_id = box_id
        self.old_text = None

    # This is a slightly more optimized put for our models.
    # Most code from TextStreamer.
    def optimized_put(self, value):
        """
        Receives tokens, decodes them, and prints them to stdout as soon as they form entire words.
        """
        if len(value.shape) > 1 and value.shape[0] > 1:
            raise ValueError("TextStreamer only supports batch size 1")
        elif len(value.shape) > 1:
            value = value[0]

        # Add the new token to the cache and decodes the entire thing.
        self.token_cache.extend(value.tolist())
        text = self.tokenizer.decode(self.token_cache, **self.decode_kwargs)

        # Prints until the last space char (simple heuristic to avoid printing incomplete words,
        # which may change with the subsequent token -- there are probably smarter ways to do this!)
        printable_text = text[:text.rfind(" ") + 1]

        self.on_finalized_text(printable_text)

    def put(self, value):
        # We send all tokens at every put() since websockets are unreliable - packets can be dropped (yes, even on localhost).
        self.print_len = 0  # Comment this line if we only want to emit the next token.
        return self.optimized_put(value)

    def on_finalized_text(self, text: str, stream_end: bool = False):
        if stream_end:
            return

        # Note: This snippet may introduce some bugs.
        if text == self.old_text:
            return
        self.old_text = text

        text = replace_many(text, config_state.target_terms, ctx=None)

        # This is where the "magic" happens.
        socketio.patched_emit(
            "item_stream",
            {
                "text": text,
                "boxId": self.box_id,
                "sourceText": [],
            },
        )
        socketio.sleep()

    def __repr__(self) -> str:
        return f"SocketStreamer(box_id='{self.box_id}')"

    def __str__(self) -> str:
        return f"SocketStreamer(box_id='{self.box_id}')"
