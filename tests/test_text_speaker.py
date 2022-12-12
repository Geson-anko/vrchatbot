import pytest
import soundcard as sc

from vrchatbot import text_speaker as mod


@pytest.mark.skipif(len(sc.all_speakers()) == 0, reason="No audio devices")
def test_TextSpeaker():
    cls = mod.TextSpeaker

    speaker = cls(sc.default_speaker().name)
    speaker.speak_text("こんばんわ")

    speaker = cls()
    assert speaker.speaker.name == sc.default_speaker().name

    class SomeClass:
        pass

    try:
        cls(SomeClass())
        assert False, "ValueError must be occured!"
    except ValueError:
        pass
