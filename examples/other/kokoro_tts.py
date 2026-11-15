import logging

from dotenv import load_dotenv

from livekit.agents import Agent, AgentServer, AgentSession, JobContext, JobProcess, cli, metrics
from livekit.agents.voice import MetricsCollectedEvent
from livekit.plugins import deepgram, openai, silero

logger = logging.getLogger("kokoro-tts-agent")

load_dotenv()


class MyAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="Your name is Kelly. You would interact with users via voice."
            "with that in mind keep your responses concise and to the point."
            "You are curious and friendly, and have a sense of humor.",
        )


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session()
async def entrypoint(ctx: JobContext):

    ctx.log_context_fields = {
        "room": ctx.room.name,
        "user_id": "your user_id",
    }
    session = AgentSession(
        vad=ctx.proc.userdata["vad"],
        llm=openai.LLM(model="gpt-4.1-mini"),
        stt=deepgram.STT(model="nova-3", language="multi"),
        tts=openai.TTS(
            model="kokoro",
            voice="af_alloy",
            api_key="not-needed",
            base_url="http://localhost:8880/v1",
            response_format="wav",
        ),
    )

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)

    await session.start(agent=MyAgent(), room=ctx.room)


if __name__ == "__main__":
    cli.run_app(server)
