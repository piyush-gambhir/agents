# Copyright 2023 LiveKit, Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0


# distributed under the License is distributed on an "AS IS" BASIS,

# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

SpeechModel = Literal[
    "mars-flash",
    "mars-pro",
    "mars-instruct",
]


MODEL_SAMPLE_RATES: dict[str, int] = {
    "mars-flash": 22050,
    "mars-pro": 48000,
    "mars-instruct": 22050,
}


OutputFormat = Literal[
    "pcm_s16le",
    "pcm_s32le",
    "wav",
    "flac",
    "adts",
]


@dataclass
class _TTSOptions:
    """Internal TTS configuration options."""

    voice_id: int
    language: str
    speech_model: str
    output_format: str
    user_instructions: str | None
    enhance_named_entities: bool


DEFAULT_VOICE_ID = 147320
DEFAULT_LANGUAGE = "en-us"
DEFAULT_MODEL: SpeechModel = "mars-flash"
DEFAULT_OUTPUT_FORMAT: OutputFormat = "pcm_s16le"
NUM_CHANNELS = 1
