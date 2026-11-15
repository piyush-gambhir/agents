# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0


# distributed under the License is distributed on an "AS IS" BASIS,

# See the License for the specific language governing permissions and
# limitations under the License.

"""Azure plugin for LiveKit Agents

Support for Azure AI including Azure Speech. For Azure OpenAI, see the [OpenAI plugin](https://github.com/livekit/agents/tree/main/livekit-plugins/livekit-plugins-openai).

See https://docs.livekit.io/agents/integrations/azure/ for more information.
"""

from . import responses
from .stt import STT, SpeechStream
from .tts import TTS
from .version import __version__

__all__ = ["STT", "SpeechStream", "TTS", "responses", "__version__"]

from livekit.agents import Plugin

from .log import logger


class AzurePlugin(Plugin):
    def __init__(self) -> None:
        super().__init__(__name__, __version__, __package__, logger)


Plugin.register_plugin(AzurePlugin())


_module = dir()
NOT_IN_ALL = [m for m in _module if m not in __all__]

__pdoc__ = {}

for n in NOT_IN_ALL:
    __pdoc__[n] = False
