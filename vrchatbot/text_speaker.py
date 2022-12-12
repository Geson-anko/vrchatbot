from typing import Optional, Union

import pyopenjtalk
import soundcard as sc


class TextSpeaker:
    """Text speaker."""

    def __init__(self, speaker_index_or_name: Optional[Union[str, int]] = None) -> None:
        """
        Args:
            speaker_index_or_name (str | int): Speaker index or name. You can check with `display_audio_devices`
        """

        if speaker_index_or_name is None:
            self.speaker = sc.default_speaker()
        else:
            if isinstance(speaker_index_or_name, str):
                id = speaker_index_or_name
            elif isinstance(speaker_index_or_name, int):
                id = sc.all_speakers()[speaker_index_or_name].name
            else:
                raise ValueError(
                    "Type of `speaker_index_or_name must be str or int. Input: {}".format(type(speaker_index_or_name))
                )

            self.speaker = sc.get_speaker(id)

    def speak_text(self, text: str) -> None:
        """Speech to text.

        Args:
            text (str): Japanese text.
        """
        wave, sr = pyopenjtalk.tts(text)
        wave = wave / (2**15)

        self.speaker.play(wave, sr)
