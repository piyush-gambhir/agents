import logging

from dotenv import load_dotenv

from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    cli,
    room_io,
    voice,  # noqa: F401
)
from livekit.plugins import google, silero

logger = logging.getLogger("realtime-video-agent")

load_dotenv()

server = AgentServer()


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    session = AgentSession(
        vad=silero.VAD.load(),
        llm=google.realtime.RealtimeModel(),
    )

    agent = Agent(
        instructions="You are an AI assistant that interacts with user via voice. You are able to see the user's video and hear the user's voice.",
    )

    await session.start(
        agent=agent,
        room=ctx.room,
        room_options=room_io.RoomOptions(
            video_input=True,
        ),
    )

    await session.generate_reply(
        instructions="introduce yourself very briefly and ask about the user's day"
    )


if __name__ == "__main__":
    cli.run_app(server)
