import asyncio
import logging

from dotenv import load_dotenv

from livekit import rtc
from livekit.agents import AgentServer, AutoSubscribe, JobContext, cli

load_dotenv()

logger = logging.getLogger("my-worker")
logger.setLevel(logging.INFO)

server = AgentServer()


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    logger.info("starting entrypoint")

    async def participant_task_1(ctx: JobContext, p: rtc.RemoteParticipant):

        logger.info(f"participant task 1 starting for {p.identity}")

        await asyncio.sleep(60)
        logger.info(f"participant task done for {p.identity}")

    async def participant_task_2(ctx: JobContext, p: rtc.RemoteParticipant):

        logger.info(f"participant task 2 starting for {p.identity}")
        await asyncio.sleep(10)

    ctx.add_participant_entrypoint(entrypoint_fnc=participant_task_1)
    ctx.add_participant_entrypoint(entrypoint_fnc=participant_task_2)

    await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)
    logger.info("connected to the room")


if __name__ == "__main__":
    cli.run_app(server)
