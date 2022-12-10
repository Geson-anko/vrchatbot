from typing import Any, Optional

import whisper


class SpeechRecongition:
    def __init__(
        self,
        model_name: str = "base",
        device: Any = "cuda",
        options: Optional[whisper.DecodingOptions] = None,
    ) -> None:
        """
        Args:
            model_name (str): Whisper model name.
            device (str): torch devices.
            options (Optional[whisper.DecodingOptions]): If None, default options are provided.
        """
        self.model = whisper.load_model(model_name, device)

        if options is None:
            self.options = whisper.DecodingOptions()
        else:
            self.options = options

    def recongnize(self, audio: Any) -> tuple[list[dict], str]:
        """Recongnize text.

        Args:
            audio (np.ndarray | torch.Tensor): 16kHz, max duration is 30 seconds.

        Returns:
            language_probs (list[dict]): Language probabilities.
            text (str): Recongnized text.
        """
        audio = whisper.pad_or_trim(audio)
        mel = whisper.log_mel_spectrogram(audio).to(self.model.device)

        _, probs = self.model.detect_language(mel)
        result = whisper.decode(self.model, mel, self.options)

        return probs, result.text
