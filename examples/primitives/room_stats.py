import asyncio
import logging
from itertools import chain

from dotenv import load_dotenv
from google.protobuf.json_format import MessageToDict

from livekit.agents import Agent, AgentServer, AgentSession, JobContext, cli
from livekit.plugins import openai

logger = logging.getLogger("minimal-worker")
logger.setLevel(logging.INFO)

load_dotenv()

server = AgentServer()


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    session = AgentSession(llm=openai.realtime.RealtimeModel())
    await session.start(Agent(instructions="You are a helpful assistant"), room=ctx.room)

    logger.info(f"connected to the room {ctx.room.name}")

    while True:
        rtc_stats = await ctx.room.get_session_stats()

        all_stats = chain(
            (("PUBLISHER", stats) for stats in rtc_stats.publisher_stats),
            (("SUBSCRIBER", stats) for stats in rtc_stats.subscriber_stats),
        )

        for source, stats in all_stats:
            stats_kind = stats.WhichOneof("stats")

            logger.info(
                f"RtcStats - {stats_kind} - {source}", extra={"stats": MessageToDict(stats)}
            )

        await asyncio.sleep(5 * 60)


if __name__ == "__main__":
    cli.run_app(server)
