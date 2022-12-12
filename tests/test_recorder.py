import math
import queue
import threading
import time

import matplotlib.pyplot as plt
import numpy as np
import pytest
import soundcard as sc

from vrchatbot import recorder as mod


def test_display_audio_devices():
    # To display message, please use pytest option `-s`.
    mod.display_audio_devices()


def test_is_silent():
    f = mod.is_silent

    wave = np.zeros(100)
    threshold = 0.01

    assert f(wave, threshold) is True
    assert f(wave + 1, threshold) is False
    assert f(wave - 1, threshold) is False

    sin = np.sin(np.linspace(0, np.pi * 2, 100))
    assert f(sin, threshold) is False
    assert f(sin * 0.01, threshold) is True


def test_check_silence_end_point():
    f = mod.check_silence_end_point

    chunk = 100
    wave = np.concatenate([np.zeros(chunk), np.ones(chunk)])

    assert f(wave, 0.01, chunk) == 100
    assert f(wave, 0.01, chunk, 50) == 50
    assert f(np.zeros(chunk), 0.01, chunk) is None


@pytest.mark.skipif(len(sc.all_microphones(True)) == 0, reason="No audio devices")
def test_Recorder__init__():
    cls = mod.Recorder

    recoder = cls(0, 4096, 16000, 0.1, 0.0001, 512, 15)

    assert recoder.buffer_size == 4096
    assert recoder.sample_rate == 16000
    assert recoder.silence_duration_for_stop == 0.1
    assert recoder.volume_threshold == 0.0001
    assert recoder.silence_check_chunk == 512
    assert recoder.max_recording_duration == 15

    recorder = cls()
    assert recorder.mic.name == sc.default_microphone().name

    class SomeClass:
        pass

    try:
        cls(SomeClass())
        assert False, "ValueError must be occured!"
    except ValueError:
        pass


@pytest.mark.slow
@pytest.mark.skipif(len(sc.all_microphones(True)) == 0, reason="No audio devices")
def test_Recorder_record_audio_until_silence():
    cls = mod.Recorder

    recorder = cls(sc.default_microphone().name, buffer_size=4096, max_recording_duration=3, volume_threshold=1.0)
    start_time = time.time()
    wave = recorder.record_audio_until_silence(waiting_timeout=5)
    assert wave is None
    assert time.time() - start_time > 5

    sample_rate = 16000
    recorder = cls(
        sc.default_microphone().name,
        1024,
        sample_rate=sample_rate,
        silence_duration_for_stop=10,
        max_recording_duration=3,
        volume_threshold=-1.0,
    )
    start_time = time.time()
    wave = recorder.record_audio_until_silence(5)
    assert isinstance(wave, np.ndarray)
    assert len(wave) == math.ceil(sample_rate * 3 / 1024) * 1024

    if isinstance(wave, np.ndarray):
        plt.plot(wave)
        plt.savefig(f"data/test_results/{__name__}.test_Recorder_record_audio_until_silence.png")


@pytest.mark.slow
@pytest.mark.skipif(len(sc.all_microphones(True)) == 0, reason="No audio devices")
def test_Recoder_record_forever():
    cls = mod.Recorder

    # recording
    chunk = 1024
    duration = 2
    sample_rate = 16000
    recorder = cls(
        sc.default_microphone().name,
        chunk,
        sample_rate=sample_rate,
        volume_threshold=-1,
        max_recording_duration=duration,
        silence_duration_for_stop=duration * 2,
    )

    def late_shutdown(n_secs, recorder):
        time.sleep(n_secs)
        recorder._shutdown = True

    threading.Thread(target=late_shutdown, args=(duration * 2 + 1, recorder)).start()
    q = queue.Queue()
    recorder.record_forever(q)
    assert q.qsize() > 1
    wav = q.get()
    assert isinstance(wav, np.ndarray)
    assert len(wav) == math.ceil(sample_rate * duration / chunk) * chunk

    # Check ignoring silence

    recorder = cls(
        sc.default_microphone().name,
        chunk,
        sample_rate=sample_rate,
        volume_threshold=1,
        max_recording_duration=duration,
        silence_duration_for_stop=duration * 2,
    )

    threading.Thread(target=late_shutdown, args=(duration * 2 + 1, recorder)).start()
    q = queue.Queue()
    recorder.record_forever(q)
    assert q.qsize() == 0


@pytest.mark.slow
@pytest.mark.skipif(len(sc.all_microphones(True)) == 0, reason="No audio devices")
def test_Recoder_record_forever_background_and_shutdown():
    cls = mod.Recorder

    chunk = 1024
    duration = 2
    sample_rate = 16000

    # No recording
    recorder = cls(
        sc.default_microphone().name,
        chunk,
        sample_rate=sample_rate,
        volume_threshold=1,
        max_recording_duration=duration,
        silence_duration_for_stop=duration * 2,
    )

    assert recorder._record_forever_thread is None
    q = recorder.record_forever_background()
    assert isinstance(q, queue.Queue)
    assert isinstance(recorder._record_forever_thread, threading.Thread)
    assert recorder._record_forever_thread.isDaemon() is False
    recorder.shutdown_record_forever()
    assert recorder._shutdown is True
    assert recorder._record_forever_thread.is_alive() is False

    # Recording
    recorder = cls(
        sc.default_microphone().name,
        chunk,
        sample_rate=sample_rate,
        volume_threshold=-1,
        max_recording_duration=duration,
        silence_duration_for_stop=duration * 2,
    )

    input_q = queue.Queue()
    q = recorder.record_forever_background(input_q, True)
    assert q is input_q
    assert recorder._record_forever_thread.isDaemon() is True
    assert recorder._record_forever_thread.is_alive() is True

    time.sleep(duration * 2 + 1)
    recorder.shutdown_record_forever()
    assert q.qsize() > 0
