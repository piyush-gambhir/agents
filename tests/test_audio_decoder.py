import io
import os
import struct
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import aiohttp
import pytest

from livekit.agents import inference
from livekit.agents.stt import SpeechEventType
from livekit.agents.utils.codecs import AudioStreamDecoder, StreamBuffer
from livekit.agents.utils.misc import is_cloud

from .utils import wer

pytestmark = pytest.mark.unit

TEST_AUDIO_FILEPATH = os.path.join(os.path.dirname(__file__), "change-sophie.opus")


@pytest.mark.asyncio
@pytest.mark.skipif(
    os.getenv("LIVEKIT_API_KEY") is None
    or os.getenv("LIVEKIT_API_SECRET") is None
    or not is_cloud(os.getenv("LIVEKIT_URL", "")),
    reason="LiveKit cloud credentials are invalid",
)
async def test_decode_and_transcribe():

    if not os.path.exists(TEST_AUDIO_FILEPATH):
        pytest.skip(f"Test file not found: {TEST_AUDIO_FILEPATH}")

    decoder = AudioStreamDecoder()
    with open(TEST_AUDIO_FILEPATH, "rb") as f:
        opus_data = f.read()
    decoder.push(opus_data)
    decoder.end_input()

    session = aiohttp.ClientSession()
    stt = inference.STT(model="deepgram/nova-3", http_session=session)
    stream = stt.stream()


    async for frame in decoder:
        stream.push_frame(frame)


    stream.end_input()


    final_text = ""
    async for event in stream:
        if event.type == SpeechEventType.FINAL_TRANSCRIPT:
            if event.alternatives:
                if final_text:
                    final_text += " "
                final_text += event.alternatives[0].text

    await decoder.aclose()
    await stream.aclose()
    await session.close()


    expected_text = (
        "the people that are crazy enough to think they can change the world are the ones who do"
    )
    assert wer(final_text, expected_text) < 0.2


def test_stream_buffer():
    buffer = StreamBuffer()
    data_chunks = [b"hello", b"world", b"test", b"data"]
    received_data = bytearray()
    write_completed = threading.Event()

    def writer():
        for chunk in data_chunks:
            buffer.write(chunk)
            time.sleep(0.01)
        buffer.end_input()
        write_completed.set()

    def reader():
        while True:
            data = buffer.read(4)
            if not data:
                break
            received_data.extend(data)


    with ThreadPoolExecutor(max_workers=2) as executor:
        reader_future = executor.submit(reader)
        writer_future = executor.submit(writer)


        writer_future.result()
        reader_future.result()


    expected_data = b"".join(data_chunks)
    assert bytes(received_data) == expected_data


def test_stream_buffer_large_chunks():
    import hashlib

    buffer = StreamBuffer()
    large_chunk = os.urandom(1024 * 1024)
    num_chunks = 5
    total_size = 0
    write_completed = threading.Event()
    input_hasher = hashlib.sha256()

    def writer():
        nonlocal total_size
        for _ in range(num_chunks):
            buffer.write(large_chunk)
            total_size += len(large_chunk)
            input_hasher.update(large_chunk)
        buffer.end_input()
        write_completed.set()

    received_size = 0
    output_hasher = hashlib.sha256()

    def reader():
        nonlocal received_size

        time.sleep(1)
        while True:
            chunk = buffer.read(8192)
            if not chunk:
                break
            received_size += len(chunk)
            output_hasher.update(chunk)


    with ThreadPoolExecutor(max_workers=2) as executor:
        reader_future = executor.submit(reader)
        writer_future = executor.submit(writer)


        writer_future.result()
        reader_future.result()

    assert received_size == total_size
    assert total_size == num_chunks * len(large_chunk)
    assert input_hasher.hexdigest() == output_hasher.hexdigest()


def test_stream_buffer_early_close():
    buffer = StreamBuffer()


    buffer.write(b"test data")


    buffer.close()


    assert buffer.read() == b""


def test_stream_buffer_slow_writer_fast_reader():
    """Reader calls read(256) in a tight loop while writer pushes small chunks with delays."""
    buffer = StreamBuffer()
    chunk_size = 48
    num_chunks = 50
    chunks = [os.urandom(chunk_size) for _ in range(num_chunks)]
    received = bytearray()

    def writer():
        for chunk in chunks:
            buffer.write(chunk)
            time.sleep(0.005)
        buffer.end_input()

    def reader():
        while True:
            data = buffer.read(256)
            if not data:
                break
            received.extend(data)

    with ThreadPoolExecutor(max_workers=2) as pool:
        rf = pool.submit(reader)
        wf = pool.submit(writer)
        wf.result(timeout=10)
        rf.result(timeout=10)

    assert bytes(received) == b"".join(chunks)


def test_stream_buffer_reader_starts_before_writer():
    """Reader blocks on read() before any data exists, then writer starts."""
    buffer = StreamBuffer()
    payload = os.urandom(1024)
    received = bytearray()
    reader_started = threading.Event()

    def reader():
        reader_started.set()
        while True:
            data = buffer.read(256)
            if not data:
                break
            received.extend(data)

    def writer():
        reader_started.wait()
        time.sleep(0.05)
        buffer.write(payload)
        buffer.end_input()

    with ThreadPoolExecutor(max_workers=2) as pool:
        rf = pool.submit(reader)
        wf = pool.submit(writer)
        wf.result(timeout=10)
        rf.result(timeout=10)

    assert bytes(received) == payload


def test_stream_buffer_end_input_with_pending_data():
    """Writer pushes data then immediately calls end_input(). Reader must get all data."""
    buffer = StreamBuffer()
    payload = os.urandom(2048)


    buffer.write(payload)
    buffer.end_input()

    received = bytearray()
    while True:
        data = buffer.read(256)
        if not data:
            break
        received.extend(data)

    assert bytes(received) == payload


def test_stream_buffer_compaction():
    """Verify that compaction preserves unread data after _COMPACT_THRESHOLD bytes are consumed."""
    import hashlib

    buffer = StreamBuffer()
    chunk_size = 512 * 1024

    num_writer_chunks = 12
    total_written = num_writer_chunks * chunk_size
    read_size = 4096

    chunks = [os.urandom(chunk_size) for _ in range(num_writer_chunks)]
    input_hasher = hashlib.sha256()
    for c in chunks:
        input_hasher.update(c)

    received = bytearray()
    output_hasher = hashlib.sha256()

    def writer():
        for chunk in chunks:
            buffer.write(chunk)
            time.sleep(0.002)
        buffer.end_input()

    def reader():
        while True:
            data = buffer.read(read_size)
            if not data:
                break
            received.extend(data)
            output_hasher.update(data)

    with ThreadPoolExecutor(max_workers=2) as pool:
        wf = pool.submit(writer)
        rf = pool.submit(reader)
        wf.result(timeout=30)
        rf.result(timeout=30)

    assert len(received) == total_written
    assert input_hasher.hexdigest() == output_hasher.hexdigest()







def test_stream_buffer_compaction_boundary():
    """Compaction must not lose the tail bytes sitting between read_pos and write_pos."""
    buffer = StreamBuffer()
    threshold = StreamBuffer._COMPACT_THRESHOLD



    extra = b"HELLO_AFTER_COMPACT"
    big_block = os.urandom(threshold) + extra

    buffer.write(big_block)
    buffer.end_input()


    drained = 0
    while drained < threshold:
        chunk = buffer.read(8192)
        assert chunk
        drained += len(chunk)


    remainder = bytearray()
    while True:
        data = buffer.read(8192)
        if not data:
            break
        remainder.extend(data)

    assert bytes(remainder) == extra


def test_stream_buffer_close_while_reading():
    """Reader is blocked in read(), then close() is called. Must unblock promptly."""
    buffer = StreamBuffer()
    reader_started = threading.Event()
    result = []

    def reader():
        reader_started.set()
        data = buffer.read(256)
        result.append(data)

    with ThreadPoolExecutor(max_workers=1) as pool:
        rf = pool.submit(reader)
        reader_started.wait()
        time.sleep(0.05)
        buffer.close()
        rf.result(timeout=2)

    assert result == [b""]


def _make_wav(sample_rate: int, num_channels: int, num_samples: int) -> bytes:
    """Generate a valid PCM16 WAV file in memory."""
    bits_per_sample = 16
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8
    data_size = num_samples * num_channels * (bits_per_sample // 8)

    buf = io.BytesIO()

    buf.write(b"RIFF")
    buf.write(struct.pack("<I", 36 + data_size))
    buf.write(b"WAVE")

    buf.write(b"fmt ")
    buf.write(struct.pack("<I", 16))
    buf.write(
        struct.pack(
            "<HHIIHH", 1, num_channels, sample_rate, byte_rate, block_align, bits_per_sample
        )
    )

    buf.write(b"data")
    buf.write(struct.pack("<I", data_size))

    buf.write(b"\x00" * data_size)
    return buf.getvalue()


@pytest.mark.asyncio
async def test_wav_inline_decoder():
    """WAV inline decoder should produce the correct total number of samples."""
    sample_rate = 24000
    num_channels = 1
    num_samples = 24000

    wav_bytes = _make_wav(sample_rate, num_channels, num_samples)

    decoder = AudioStreamDecoder(
        sample_rate=sample_rate, num_channels=num_channels, format="audio/wav"
    )


    chunk_size = 37
    for i in range(0, len(wav_bytes), chunk_size):
        decoder.push(wav_bytes[i : i + chunk_size])
    decoder.end_input()

    total_samples = 0
    async for frame in decoder:
        assert frame.sample_rate == sample_rate
        assert frame.num_channels == num_channels
        total_samples += frame.samples_per_channel

    assert total_samples == num_samples
    await decoder.aclose()


@pytest.mark.asyncio
async def test_wav_inline_decoder_with_resampling():
    """WAV inline decoder should correctly resample to a different output rate."""
    src_rate = 16000
    out_rate = 48000
    num_channels = 1
    num_samples = 16000

    wav_bytes = _make_wav(src_rate, num_channels, num_samples)

    decoder = AudioStreamDecoder(
        sample_rate=out_rate, num_channels=num_channels, format="audio/wav"
    )
    decoder.push(wav_bytes)
    decoder.end_input()

    total_samples = 0
    async for frame in decoder:
        assert frame.sample_rate == out_rate
        total_samples += frame.samples_per_channel


    expected = num_samples * out_rate // src_rate
    assert abs(total_samples - expected) <= out_rate // 50
    await decoder.aclose()


@pytest.mark.asyncio
async def test_wav_multi_chunk_each_with_headers():
    """Each push() is a complete WAV file; decoder must re-parse headers each time."""
    sample_rate = 24000
    num_channels = 1
    samples_per_chunk = 2400
    num_chunks = 5

    wav_chunk = _make_wav(sample_rate, num_channels, samples_per_chunk)

    decoder = AudioStreamDecoder(
        sample_rate=sample_rate, num_channels=num_channels, format="audio/wav"
    )

    for _ in range(num_chunks):
        decoder.push(wav_chunk)
    decoder.end_input()

    total_samples = 0
    async for frame in decoder:
        assert frame.sample_rate == sample_rate
        assert frame.num_channels == num_channels
        total_samples += frame.samples_per_channel

    assert total_samples == samples_per_chunk * num_chunks
    await decoder.aclose()


@pytest.mark.asyncio
async def test_wav_multi_chunk_with_resampling():
    """Multiple WAV chunks with resampling should produce correct total duration."""
    src_rate = 16000
    out_rate = 48000
    num_channels = 1
    samples_per_chunk = 1600
    num_chunks = 3

    wav_chunk = _make_wav(src_rate, num_channels, samples_per_chunk)

    decoder = AudioStreamDecoder(
        sample_rate=out_rate, num_channels=num_channels, format="audio/wav"
    )

    for _ in range(num_chunks):
        decoder.push(wav_chunk)
    decoder.end_input()

    total_samples = 0
    async for frame in decoder:
        assert frame.sample_rate == out_rate
        total_samples += frame.samples_per_channel

    expected = samples_per_chunk * num_chunks * out_rate // src_rate
    assert abs(total_samples - expected) <= out_rate // 50
    await decoder.aclose()
