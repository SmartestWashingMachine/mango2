import onnxruntime as ort
import re
import numpy as np
from gandy.state.config_state import config_state
from gandy.utils.fancy_logger import logger

class AudioCodec():
    def __init__(self):
        self.loaded = False

    def load(self):
        if self.loaded:
            return

        # The encoder/decoder is a SNAC 24kHz variant.
        # "Why 24kHz"? Speed - much less tokens to process. We really want to avoid diffusion codecs as they are slooooow.
        # The other SNAC variants have a fourth output layer which dramatically increase the number of tokens.
        # "Why SNAC"? On qualitative tests it produced clearer (Japanese) audio compared to other variants like Mimi.
        # I suspect this is due to SNAC simply being trained on more multilingual data rather than an architectural quirk.
        # Also, many other codec candidates (e.g: NEMO, which had even higher quality than SNAC here) had to be thrown out as they don't port well to ONNX.
        # I suspect I would get a lot of value from further fine-tuning my own audio codec...
        # But that would mean GAN training. And I truly hate working with GANs. Burn in hell GAN.
        # Also note we don't need 100% high quality audio; it just needs to be clear enough to transcribe into text. This isn't a TTS model.
        with logger.begin_event("Loading audio codec"):
            providers = ["CPUExecutionProvider"]
            if config_state.use_cuda:
                providers = ["CUDAExecutionProvider"] + providers
            self.encoder = ort.InferenceSession("models/audio/ja_encoder_model.onnx", providers=providers)
            # We don't care for the decoder - we're not generating audio.

            self.loaded = True

    def flatten_to_strings(self, l0, l1, l2, codebook_size=4096):
        """
        Mixes together three SNAC lists into a single string sequence (that the model expects).

        l0: list of length N
        l1: list of length 2N
        l2: list of length 4N
        """
        output = []
        
        for i in range(len(l0)):
            # Layer 0: No offset
            output.append(f"<|audio_{l0[i]}|>")
            
            # Layer 1: Offset by 4096 (2 tokens)
            for val in l1[i*2 : (i+1)*2]:
                output.append(f"<|audio_{val + codebook_size}|>")
                
            # Layer 2: Offset by 8192 (4 tokens)
            for val in l2[i*4 : (i+1)*4]:
                output.append(f"<|audio_{val + (codebook_size * 2)}|>")
                
        return "".join(output)

    def encode(self, audio_data: bytes):
        # Encode audio into image tokens to pass into LLM.

        with logger.begin_event("Encoding audio into tokens with codec"):
            dummy_encoder_inputs = audio_data[None, None, ...] # Model expects [batch(1), channels(1 - it's mono), n_samples]
            encoder_inputs = {self.encoder.get_inputs()[0].name: dummy_encoder_inputs}

            with logger.begin_event("Calling encoder"):
                out = self.encoder.run(None, encoder_inputs)
            
            l0, l1, l2 = out[0], out[1], out[2]
            
            with logger.begin_event("Flattening"):
                return self.flatten_to_strings(l0, l1, l2)