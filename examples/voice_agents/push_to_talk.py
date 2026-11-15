import asyncio
import logging

from dotenv import load_dotenv

from livekit import rtc
from livekit.agents import Agent, AgentServer, AgentSession, JobContext, JobRequest, cli, inference
from livekit.agents.llm import ChatContext, ChatMessage, StopResponse

logger = logging.getLogger("push-to-talk")
logger.setLevel(logging.INFO)

load_dotenv()


class MyAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="You are a helpful assistant.",
            stt=inference.STT("deepgram/nova-3"),
            llm=inference.LLM("google/gemini-2.5-flash"),
            tts=inference.TTS("cartesia/sonic-3"),
        )

    async def on_user_turn_completed(self, turn_ctx: ChatContext, new_message: ChatMessage) -> None:

        if not new_message.text_content:
            logger.info("ignore empty user turn")
            raise StopResponse()


async def handle_request(request: JobRequest) -> None:
    await request.accept(
        identity="ptt-agent",
        attributes={"push-to-talk": "1"},
    )


server = AgentServer()


@server.rtc_session(on_request=handle_request)
async def entrypoint(ctx: JobContext):
    session = AgentSession(turn_detection="manual")

    agent = MyAgent()
    await session.start(agent=agent, room=ctx.room)

    session.input.set_audio_enabled(False)

    @ctx.room.local_participant.register_rpc_method("start_turn")
    async def start_turn(data: rtc.RpcInvocationData):
        session.interrupt()
        session.clear_user_turn()

        session.room_io.set_participant(data.caller_identity)
        session.input.set_audio_enabled(True)

    @ctx.room.local_participant.register_rpc_method("end_turn")
    async def end_turn(data: rtc.RpcInvocationData):
        session.input.set_audio_enabled(False)
        try:
            user_transcript = await session.commit_user_turn(
                transcript_timeout=5.0,
                stt_flush_duration=2.0,
            )
            logger.info(f"user transcript: {user_transcript}")
        except asyncio.CancelledError:
            logger.info("commit user turn cancelled")
        except Exception as e:
            logger.error("error committing user turn", exc_info=e)

    @ctx.room.local_participant.register_rpc_method("cancel_turn")
    async def cancel_turn(data: rtc.RpcInvocationData):
        session.input.set_audio_enabled(False)
        session.clear_user_turn()
        logger.info("cancel turn")


if __name__ == "__main__":
    cli.run_app(server)
