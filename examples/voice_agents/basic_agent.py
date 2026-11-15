import logging

from dotenv import load_dotenv

from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    MetricsCollectedEvent,
    RunContext,
    TurnHandlingOptions,
    cli,
    inference,
    metrics,
    room_io,
    text_transforms,
)
from livekit.agents.beta import EndCallTool
from livekit.agents.llm import function_tool
from livekit.plugins import silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel




logger = logging.getLogger("basic-agent")

load_dotenv()


class MyAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="Your name is Kelly, built by LiveKit. You would interact with users via voice."
            "with that in mind keep your responses concise and to the point."
            "do not use emojis, asterisks, markdown, or other special characters in your responses."
            "You are curious and friendly, and have a sense of humor."
            "you will speak english to the user",
            tools=[EndCallTool()],
        )

    async def on_enter(self) -> None:


        self.session.generate_reply(instructions="greet the user and introduce yourself")



    @function_tool
    async def lookup_weather(
        self, context: RunContext, location: str, latitude: str, longitude: str
    ) -> str:
        """Called when the user asks for weather related information.
        Ensure the user's location (city or region) is provided.
        When given a location, please estimate the latitude and longitude of the location and
        do not ask the user for them.

        Args:
            location: The location they are asking for
            latitude: The latitude of the location, do not ask user for it
            longitude: The longitude of the location, do not ask user for it
        """

        logger.info(f"Looking up weather for {location}")

        return "sunny with a temperature of 70 degrees."


server = AgentServer()


def prewarm(proc: JobProcess) -> None:
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session()
async def entrypoint(ctx: JobContext) -> None:

    ctx.log_context_fields = {
        "room": ctx.room.name,
    }
    session: AgentSession = AgentSession(


        stt=inference.STT("deepgram/nova-3", language="multi"),


        llm=inference.LLM("openai/gpt-4.1-mini"),


        tts=inference.TTS("cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
        vad=ctx.proc.userdata["vad"],
        turn_handling=TurnHandlingOptions(


            turn_detection=MultilingualModel(),
            interruption={


                "resume_false_interruption": True,
                "false_interruption_timeout": 1.0,
            },


            preemptive_generation={"enabled": True, "max_retries": 3},
        ),

        aec_warmup_duration=3.0,
        tts_text_transforms=[
            "filter_emoji",
            "filter_markdown",
            text_transforms.replace({"LiveKit": "<<ˈ|l|aɪ|v>> <<ˈ|k|ɪ|t>>"}),
        ],
    )

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent) -> None:
        metrics.log_metrics(ev.metrics)

    async def log_usage():
        logger.info(f"Usage: {session.usage}")


    ctx.add_shutdown_callback(log_usage)

    await session.start(
        agent=MyAgent(),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(


            ),
        ),
    )


if __name__ == "__main__":
    cli.run_app(server)
