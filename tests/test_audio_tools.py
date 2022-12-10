import math
import time

import matplotlib.pyplot as plt
import numpy as np
import pytest
import soundcard as sc

from vrchatbot import audio_tools as mod


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

    try:
        cls(None)
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


@pytest.mark.skipif(len(sc.all_speakers()) == 0, reason="No audio devices")
def test_TextSpeaker():
    cls = mod.TextSpeaker

    speaker = cls(sc.default_speaker().name)
    speaker.speak_text("こんばんわ")
