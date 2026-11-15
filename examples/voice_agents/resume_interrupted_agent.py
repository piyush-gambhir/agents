import logging

from dotenv import load_dotenv

from livekit.agents import Agent, AgentServer, AgentSession, JobContext, cli, inference
from livekit.plugins import silero

logger = logging.getLogger("resume-agent")

load_dotenv()


server = AgentServer()


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    session = AgentSession(
        vad=silero.VAD.load(),
        llm=inference.LLM("openai/gpt-4.1-mini"),
        stt=inference.STT("deepgram/nova-3"),
        tts=inference.TTS("cartesia/sonic-3"),
        false_interruption_timeout=1.0,
        resume_false_interruption=True,
    )

    await session.start(agent=Agent(instructions="You are a helpful assistant."), room=ctx.room)


if __name__ == "__main__":
    cli.run_app(server)
