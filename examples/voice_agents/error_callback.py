import asyncio
import logging
import os
import pathlib

from dotenv import load_dotenv

from livekit.agents import AgentServer, JobContext, cli, inference
from livekit.agents.utils.audio import audio_frames_from_file
from livekit.agents.voice import Agent, AgentSession
from livekit.agents.voice.events import CloseEvent, ErrorEvent
from livekit.plugins import silero
from livekit.rtc import ParticipantKind

logger = logging.getLogger("my-worker")
logger.setLevel(logging.INFO)

load_dotenv()


server = AgentServer()


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    session = AgentSession(
        stt=inference.STT("deepgram/nova-3"),
        llm=inference.LLM("openai/gpt-4.1-mini"),
        tts=inference.TTS("cartesia/sonic-3"),
        vad=silero.VAD.load(),
    )

    custom_error_audio = os.path.join(pathlib.Path(__file__).parent.absolute(), "error_message.ogg")

    @session.on("error")
    def on_error(ev: ErrorEvent):
        if ev.error.recoverable:
            return

        logger.info(f"session is closing due to unrecoverable error {ev.error}")

        session.say(
            "I'm having trouble connecting right now. Let me transfer your call.",
            audio=audio_frames_from_file(custom_error_audio),
            allow_interruptions=False,
        )

    @session.on("close")
    def on_close(_: CloseEvent):
        logger.info("Session is closing")

        participant = [
            p
            for p in ctx.room.remote_participants.values()
            if p.kind == ParticipantKind.PARTICIPANT_KIND_SIP
        ][0]

        def on_sip_transfer_done(f: asyncio.Future):
            if f.exception():
                logger.error(f"Error transferring SIP participant: {f.exception()}")
            else:
                logger.info("SIP participant transferred")
            ctx.delete_room()

        if participant.kind == ParticipantKind.PARTICIPANT_KIND_SIP:
            ctx.transfer_sip_participant(participant, "tel:+18003310500").add_done_callback(
                on_sip_transfer_done
            )

    await session.start(agent=Agent(instructions="You are a helpful assistant."), room=ctx.room)


if __name__ == "__main__":
    cli.run_app(server)
