import logging

from dotenv import load_dotenv
from google.genai import types  # noqa: F401

from livekit.agents import Agent, AgentServer, AgentSession, JobContext, JobProcess, cli
from livekit.plugins import deepgram, google, openai, silero  # noqa: F401
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("realtime-turn-detector")
logger.setLevel(logging.INFO)

load_dotenv()


server = AgentServer()


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    session = AgentSession(
        allow_interruptions=True,
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        stt=deepgram.STT(),
        llm=openai.realtime.RealtimeModel(
            voice="alloy",
            turn_detection=None,
            input_audio_transcription=None,
        ),
    )
    await session.start(agent=Agent(instructions="You are a helpful assistant."), room=ctx.room)


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm

if __name__ == "__main__":
    cli.run_app(server)
