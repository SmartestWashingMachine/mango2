from gandy.utils.speech_bubble import SpeechBubble
from dataclasses import dataclass
from typing import List

@dataclass
class TextBlock():
    uuid: str

    translated_text: str
    original_bbox: SpeechBubble
    final_bbox: SpeechBubble
    font_size: int

    # Computed from translated_text.
    wrapped_lines: str
    # Computed from bbox.
    mass: float
    anchor_point: List[float]

    displacement: None