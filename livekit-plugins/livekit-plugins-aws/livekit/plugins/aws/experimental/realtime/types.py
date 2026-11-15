from typing import Literal

TURN_DETECTION = Literal["HIGH", "MEDIUM", "LOW"]
MODALITIES = Literal["audio", "mixed"]
REALTIME_MODELS = Literal["amazon.nova-sonic-v1:0", "amazon.nova-2-sonic-v1:0"]

SONIC1_VOICES = Literal[
    "matthew",
    "tiffany",
    "amy",
    "lupe",
    "carlos",
    "ambre",
    "florian",
    "greta",
    "lennart",
    "beatrice",
    "lorenzo",
]

SONIC2_VOICES = Literal[
    "matthew",
    "tiffany",
    "amy",
    "olivia",
    "lupe",
    "carlos",
    "ambre",
    "florian",
    "tina",
    "lennart",
    "beatrice",
    "lorenzo",
    "carolina",
    "leo",
    "arjun",
    "kiara",
]
