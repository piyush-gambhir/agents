from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from google.genai import types







LiveAPIModels = Literal[

    "gemini-live-2.5-flash-native-audio",

    "gemini-3.1-flash-live-preview",
    "gemini-2.5-flash-native-audio-preview-12-2025",
]

Voice = Literal[
    "Achernar",
    "Achird",
    "Algenib",
    "Algieba",
    "Alnilam",
    "Aoede",
    "Autonoe",
    "Callirrhoe",
    "Charon",
    "Despina",
    "Enceladus",
    "Erinome",
    "Fenrir",
    "Gacrux",
    "Iapetus",
    "Kore",
    "Laomedeia",
    "Leda",
    "Orus",
    "Pulcherrima",
    "Puck",
    "Rasalgethi",
    "Sadachbia",
    "Sadaltager",
    "Schedar",
    "Sulafat",
    "Umbriel",
    "Vindemiatrix",
    "Zephyr",
    "Zubenelgenubi",
]


ClientEvents = (
    types.ContentListUnion
    | types.ContentListUnionDict
    | types.LiveClientContentOrDict
    | types.LiveClientRealtimeInput
    | types.LiveClientRealtimeInputOrDict
    | types.LiveClientToolResponseOrDict
    | types.FunctionResponseOrDict
    | Sequence[types.FunctionResponseOrDict]
)
