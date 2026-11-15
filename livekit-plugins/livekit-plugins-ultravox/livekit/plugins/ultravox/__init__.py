# Copyright 2023 LiveKit, Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0


# distributed under the License is distributed on an "AS IS" BASIS,

# See the License for the specific language governing permissions and
# limitations under the License.

"""Ultravox plugin for LiveKit Agents

Support for Ultravox Realtime API

"""

from . import realtime, utils
from .models import UltravoxModel, UltravoxVoice
from .realtime.realtime_model import RealtimeModel, RealtimeSession
from .version import __version__

__all__ = [
    "UltravoxVoice",
    "UltravoxModel",
    "realtime",
    "RealtimeModel",
    "RealtimeSession",
    "utils",
    "__version__",
]

from livekit.agents import Plugin

from .log import logger


class UltravoxPlugin(Plugin):
    def __init__(self) -> None:
        super().__init__(__name__, __version__, __package__, logger)


Plugin.register_plugin(UltravoxPlugin())


_module = dir()
NOT_IN_ALL = [m for m in _module if m not in __all__]

__pdoc__ = {}

for n in NOT_IN_ALL:
    __pdoc__[n] = False
