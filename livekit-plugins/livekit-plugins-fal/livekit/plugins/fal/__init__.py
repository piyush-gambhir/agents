# Copyright 2023 LiveKit, Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0


# distributed under the License is distributed on an "AS IS" BASIS,

# See the License for the specific language governing permissions and
# limitations under the License.

"""Fal plugin for LiveKit Agents

See https://docs.livekit.io/agents/integrations/stt/fal/ for more information.
"""

from .stt import WizperSTT, WizperSTT as STT
from .version import __version__

__all__ = ["WizperSTT", "__version__", "STT"]


from livekit.agents import Plugin

from .log import logger


class FalPlugin(Plugin):
    def __init__(self) -> None:
        super().__init__(__name__, __version__, __package__, logger)


Plugin.register_plugin(FalPlugin())


_module = dir()
NOT_IN_ALL = [m for m in _module if m not in __all__]

__pdoc__ = {}

for n in NOT_IN_ALL:
    __pdoc__[n] = False
