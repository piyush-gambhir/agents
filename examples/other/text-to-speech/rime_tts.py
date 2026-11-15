import asyncio
import logging

from dotenv import load_dotenv

from livekit import rtc
from livekit.agents import AgentServer, AutoSubscribe, JobContext, cli, inference
from livekit.agents.tokenize import blingfire
from livekit.agents.tts import StreamAdapter


load_dotenv()
logger = logging.getLogger("rime-tts-demo")
logger.setLevel(logging.INFO)

tokenizer = blingfire.SentenceTokenizer()

server = AgentServer()


@server.rtc_session()
async def entrypoint(ctx: JobContext) -> None:
    """
    Main entrypoint for the TTS demo agent.

    This function:
    1. Initializes connection to LiveKit room
    2. Sets up Rime TTS with specific configuration
    3. Creates and publishes an audio track
    4. Synthesizes and streams sample text

    Args:
        ctx (JobContext): The job context providing access to LiveKit room and other utilities

    Raises:
        Exception: If any error occurs during setup or streaming
    """
    try:

        await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_NONE)
        await ctx.wait_for_participant()
        logger.info("Connected to LiveKit room successfully And participant joined")

        tts = inference.TTS("rime/arcana", voice="Astra")

        logger.info("TTS initialized successfully")


        source = rtc.AudioSource(tts.sample_rate, tts.num_channels)
        track = rtc.LocalAudioTrack.create_audio_track("agent-mic", source)
        options = rtc.TrackPublishOptions()
        options.source = rtc.TrackSource.SOURCE_MICROPHONE


        publication = await ctx.room.local_participant.publish_track(track, options)
        await publication.wait_for_subscription()
        logger.info("Audio track published successfully")


        text = """Hi! I'm using Rime's Arcana model with the Astra voice. I can speak naturally with different tones, paces, and emotions. Want to try other voices like Luna, Celeste, or Orion?"""


        logger.info("Starting audio synthesis...")
        async for output in tts.synthesize(text):
            await source.capture_frame(output.frame)

        logger.info("Audio synthesis completed successfully")
        logger.info("Audio Streaming Simulation Example")
        logger.info("Starting streaming text chunks...")

        streaming_text = """
                Welcome to the Rime Text-to-Speech demonstration! This example shows how to properly segment text\
                for natural-sounding speech synthesis. We handle various punctuation marks, including commas,\
                periods, and question marks. Have you noticed how the voice maintains proper intonation? This is\
                achieved through careful text segmentation. The TTS engine processes each segment independently,\
                ensuring optimal timing and natural flow. Would you like to try different voices like Astra, Luna,\
                or Celeste? Each voice has its own unique characteristics!
        """
        tts_wrapped = StreamAdapter(tts=tts, sentence_tokenizer=tokenizer)
        stream = tts_wrapped.stream()

        async def _playback_task():
            async for audio in stream:
                await source.capture_frame(audio.frame)

        playback_task = asyncio.create_task(_playback_task())

        chunk_size = 15
        for i in range(0, len(streaming_text), chunk_size):
            chunk = streaming_text[i : i + chunk_size]
            logger.debug("Processing chunk: %s...", chunk[:50])
            stream.push_text(chunk)
            await asyncio.sleep(0.1)

        stream.end_input()
        await playback_task
        logger.info("Streaming completed successfully")

    except Exception as e:
        logger.error("An error occurred: %s", str(e), exc_info=True)
        raise
    finally:

        if "stream" in locals():
            await stream.aclose()
        if "tts_wrapped" in locals():
            await tts_wrapped.aclose()


if __name__ == "__main__":

    cli.run_app(server)
