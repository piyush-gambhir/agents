import asyncio
import logging

from dotenv import load_dotenv

from livekit import rtc
from livekit.agents import (
    AgentServer,
    AutoSubscribe,
    JobContext,
    cli,
)
from livekit.agents.vad import VADEventType
from livekit.plugins import silero

load_dotenv()
logger = logging.getLogger("echo-agent")






server = AgentServer()


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    logger.info(f"connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)


    participant: rtc.Participant = await ctx.wait_for_participant()
    stream = rtc.AudioStream.from_participant(
        participant=participant,
        track_source=rtc.TrackSource.SOURCE_MICROPHONE,
    )
    vad = silero.VAD.load(
        min_speech_duration=0.2,
        min_silence_duration=0.6,
    )
    vad_stream = vad.stream()

    source = rtc.AudioSource(sample_rate=48000, num_channels=1)
    track = rtc.LocalAudioTrack.create_audio_track("echo", source)
    await ctx.room.local_participant.publish_track(
        track,
        rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE),
    )

    queue = asyncio.Queue(maxsize=1000)
    is_speaking = False
    is_echoing = False

    async def _set_state(state: str):
        await ctx.room.local_participant.set_attributes({"lk.agent.state": state})

    await _set_state("listening")

    async def _process_input():
        async for audio_event in stream:
            if is_echoing:
                continue
            vad_stream.push_frame(audio_event.frame)
            try:
                queue.put_nowait(audio_event.frame)
            except asyncio.QueueFull:

                queue.get_nowait()
                queue.put_nowait(audio_event.frame)

    async def _process_vad():
        nonlocal is_speaking, is_echoing
        async for vad_event in vad_stream:
            if is_echoing:
                continue
            if vad_event.type == VADEventType.START_OF_SPEECH:
                is_speaking = True
                frames_to_keep = 100
                frames = []
                while not queue.empty():
                    frames.append(queue.get_nowait())
                for frame in frames[-frames_to_keep:]:
                    queue.put_nowait(frame)
            elif vad_event.type == VADEventType.END_OF_SPEECH:
                is_speaking = False
                is_echoing = True
                logger.info("end of speech, playing back")
                await _set_state("speaking")
                try:
                    while not queue.empty():
                        frame = queue.get_nowait()
                        await source.capture_frame(frame)
                except asyncio.QueueEmpty:
                    pass
                finally:
                    is_echoing = False
                    await _set_state("listening")

    await asyncio.gather(
        _process_input(),
        _process_vad(),
    )


if __name__ == "__main__":
    cli.run_app(server)
