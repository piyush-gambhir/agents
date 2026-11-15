import logging
import urllib.parse

from dotenv import load_dotenv

from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    AutoSubscribe,
    JobContext,
    MetricsCollectedEvent,
    StopResponse,
    cli,
    llm,
    metrics,
    room_io,
    utils,
)
from livekit.plugins import openai, silero

load_dotenv()

logger = logging.getLogger("translator")






class Translator(Agent):
    def __init__(self):
        super().__init__(
            instructions="not-needed",
            stt=openai.STT(),


        )
        self._http_session = utils.http_context.http_session()

    async def translate_text(self, text: str, target_lang: str = "zh-CN") -> str | None:
        """Translate text to target language using Google Translate API"""
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_lang}&dt=t&q={urllib.parse.quote(text)}"

        try:
            async with self._http_session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return "".join(segment[0] for segment in data[0] if segment[0])
                else:
                    logger.error(f"Translation failed with status: {response.status}")
        except Exception as e:
            logger.error(f"Translation error: {str(e)}")

        return None

    async def on_user_turn_completed(self, chat_ctx: llm.ChatContext, new_message: llm.ChatMessage):
        user_transcript = new_message.text_content
        logger.info(f" -> {user_transcript}")


        translated = await self.translate_text(user_transcript)
        if translated:
            self.session.say(translated)


        raise StopResponse()


server = AgentServer()


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    session = AgentSession(

        vad=silero.VAD.load(),
    )

    @session.on("metrics_collected")
    def on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)

    await session.start(
        agent=Translator(),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            text_output=room_io.TextOutputOptions(sync_transcription=False),



            audio_output=True,
        ),
    )
    session.output.set_audio_enabled(False)


if __name__ == "__main__":
    cli.run_app(server)
