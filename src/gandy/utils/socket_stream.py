from transformers.generation.streamers import TextStreamer
from gandy.app import socketio


class SocketStreamer(TextStreamer):
    def __init__(
        self, tokenizer=None, skip_prompt: bool = False, box_id=None, **decode_kwargs
    ):
        decode_kwargs["skip_special_tokens"] = True

        super().__init__(tokenizer, skip_prompt, **decode_kwargs)

        self.box_id = box_id
        self.old_text = None

    def put(self, value):
        # We send all tokens at every put() since websockets are unreliable - packets can be dropped (yes, even on localhost).
        self.print_len = 0  # Comment this line if we only want to emit the next token.
        return super().put(value)

    def on_finalized_text(self, text: str, stream_end: bool = False):
        if stream_end:
            return

        # Note: This snippet may introduce some bugs.
        if text == self.old_text:
            return
        self.old_text = text

        # This is where the "magic" happens.
        socketio.emit(
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
