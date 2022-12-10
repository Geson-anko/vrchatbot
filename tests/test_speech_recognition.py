import pytest
import torch
import whisper

from vrchatbot import speech_recongnition as mod


@pytest.mark.skipif(not torch.cuda.is_available(), reason="No cuda device available.")
def test_SpeechRecongition__init__():
    cls = mod.SpeechRecongition

    _ = cls()

    # option
    opt = whisper.DecodingOptions()
    instance = cls("base", "cuda", opt)
    assert instance.options is opt


@pytest.mark.skipif(not torch.cuda.is_available(), reason="No cuda device available.")
def test_SpeechRecongition_recognize():
    cls = mod.SpeechRecongition

    audio = whisper.load_audio("data/sample_transcribe.mp3")
    instance = cls()
    probs, text = instance.recongnize(audio)
    with open("data/test_results/recongnized_text.txt", "w", encoding="utf-8") as f:
        f.write(f"{max(probs, key=probs.get)}: {text}")
