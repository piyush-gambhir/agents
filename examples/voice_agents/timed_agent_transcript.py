import asyncio
import logging
from collections.abc import AsyncGenerator, AsyncIterable

from dotenv import load_dotenv

from livekit.agents import Agent, AgentServer, AgentSession, JobContext, cli, inference, room_io
from livekit.agents.types import TimedString
from livekit.agents.voice.agent import ModelSettings
from livekit.plugins import cartesia, silero

logger = logging.getLogger("my-worker")
logger.setLevel(logging.INFO)

load_dotenv()


class MyAgent(Agent):
    def __init__(self):
        super().__init__(instructions="You are a helpful assistant.")

        self._closing_task: asyncio.Task[None] | None = None

    async def transcription_node(
        self, text: AsyncIterable[str | TimedString], model_settings: ModelSettings
    ) -> AsyncGenerator[str | TimedString, None]:
        async for chunk in text:
            if isinstance(chunk, TimedString):
                logger.info(f"TimedString: '{chunk}' ({chunk.start_time} - {chunk.end_time})")
            yield chunk


server = AgentServer()


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    session = AgentSession(
        stt=inference.STT("deepgram/nova-3"),
        llm=inference.LLM("google/gemini-2.5-flash"),
        tts=cartesia.TTS(),
        vad=silero.VAD.load(),
        use_tts_aligned_transcript=True,
    )

    await session.start(
        agent=MyAgent(),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            text_output=room_io.TextOutputOptions(
                json_format=False,
                sync_transcription=True,
            )
        ),
    )

    session.generate_reply(instructions="say hello to the user")


if __name__ == "__main__":
    cli.run_app(server)
