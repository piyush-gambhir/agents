# Copyright 2026 LiveKit, Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0


# distributed under the License is distributed on an "AS IS" BASIS,

# See the License for the specific language governing permissions and
# limitations under the License.

"""Cerebras plugin for LiveKit Agents

Support for LLM with Cerebras fast inference, including payload optimization
via gzip compression and msgpack encoding.
"""

from livekit.agents import Plugin

from .llm import LLM
from .log import logger
from .version import __version__

__all__ = ["LLM", "__version__"]


class CerebrasPlugin(Plugin):
    def __init__(self) -> None:
        super().__init__(__name__, __version__, __package__, logger)


Plugin.register_plugin(CerebrasPlugin())


_module = dir()
NOT_IN_ALL = [m for m in _module if m not in __all__]

__pdoc__ = {}

for n in NOT_IN_ALL:
    __pdoc__[n] = False
