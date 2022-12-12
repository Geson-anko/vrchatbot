import math
import queue
import threading
from typing import Any, Optional, Union

import numpy as np
import soundcard as sc

from .constants import RECOGNIZE_SAMPLE_RATE


def display_audio_devices():
    """Display list of audio devices. You will see the message like below.

    ```
    --- Microphones ---
    Index: 0, Name: ...
    Index: 1, Name: ...
    ...

    --- Speaker ---
    Index: 0, Name: ...
    Index: 1, Name: ...
    ...
    ```
    """

    template = "Index: {0}, Name: {1}"

    print("--- Microphones ---")
    for i, mic in enumerate(sc.all_microphones(True)):
        print(template.format(i, mic.name))

    print()
    print("--- Speakers ---")
    for i, spkr in enumerate(sc.all_speakers()):
        print(template.format(i, spkr.name))


def is_silent(wave: np.ndarray, threshold: float) -> bool:
    """Checking input `wave` is silent.
    Args:
        wave (np.ndarray): 1d array.
        threshold (float): Volume threshold.

    Returns:
        is_silent (bool): Whether wave is silent or not.
    """
    return float(np.sqrt(np.mean(wave**2))) <= threshold


def check_silence_end_point(
    wave: np.ndarray, threshold: float, chunk: int, stride: Optional[int] = None
) -> Optional[int]:
    """Checking silence end point. If wave is silent completely, `None` is returned.

    Args:
        wave (np.ndarray): 1d array.
        threshold (float): Volume threshold.
        chunk (int): Check chunk size for `is_silent`
        stride (Optional[int]): Stride length for checking. If `None`, this equals to `chunk`

    Returns:
        end_point (Optional[int]): End point of wave silence. If wave is silent completely, `None` is returned.
    """

    if stride is None:
        stride = chunk

    for i in range(0, len(wave), stride):
        s = is_silent(wave[i : i + chunk], threshold)
        if not s:
            return i

    return None


class Recorder:
    """Recording Audio."""

    def __init__(
        self,
        mic_index_or_name: Optional[Union[str, int]] = None,
        buffer_size: int = 4096,
        sample_rate: int = RECOGNIZE_SAMPLE_RATE,
        silence_duration_for_stop: float = 0.5,  # seconds
        volume_threshold: float = 0.01,
        silence_check_chunk: int = 1024,
        max_recording_duration: float = 30.0,  # seconds
        silence_check_stride: Optional[int] = None,
    ) -> None:
        """
        Args:
            mic_index_or_name (Optional[str | int]): Mic index or name. You can check with `display_audio_devices`
                If `None`, default microphone will be used.
            buffer_size (int): Recording buffer size.
            sample_rate: (int): Default 16kHz
            silence_duration_for_stop (float): Seconds.  If it is silent during this time, recording will be interrupted.
            volume_threshold (float): Volume threshold for checking silence.
            silence_check_chunk (float): Check chunk size for `is_silent`
            max_recording_duration (float): Max recording duration [seconds.]
            silence_check_stride (Optional[int]): Stride size for `check_silence_end_point`

        Raises:
            ValueError: if mic_index_or_name is not str or int.
        """

        if mic_index_or_name is None:
            self.mic = sc.default_microphone()
        else:
            if isinstance(mic_index_or_name, str):
                id = mic_index_or_name
            elif isinstance(mic_index_or_name, int):
                id = sc.all_microphones(True)[mic_index_or_name].name
            else:
                raise ValueError(
                    "Type of `mic_index_or_name must be str or int. Input: {}".format(type(mic_index_or_name))
                )

            self.mic = sc.get_microphone(
                id=id,
                include_loopback=True,
            )

        self.buffer_size = buffer_size
        self.sample_rate = sample_rate
        self.silence_duration_for_stop = silence_duration_for_stop
        self.volume_threshold = volume_threshold
        self.silence_check_chunk = silence_check_chunk
        self.max_recording_duration = max_recording_duration
        self.silence_check_stride = silence_check_stride

        self._shutdown = False

    def record_audio_until_silence(self, waiting_timeout: float = 5) -> Optional[np.ndarray]:
        """Recording from mic until silence continues decided duration. And, Record begins when
        there is no silence.

        Args:
            waiting_timeout: Time to timeout until silence disappears.

        Returns:
            wave (Optinal[np.ndarray]): Recorded wave. If timeouted, `None` is returned.
        """
        with self.mic.recorder(self.sample_rate, 1) as mic:
            waiting_length_for_timeout = 0
            recorded_waves = []
            silence_length = 0
            record_start = False
            recorded_length = 0

            mic.record(self.buffer_size)
            for _ in range(
                math.ceil((waiting_timeout + self.max_recording_duration) * self.sample_rate / self.buffer_size)
            ):  # Avoid while True
                wave = mic.record(self.buffer_size).reshape(-1).astype("float32")
                start_idx = check_silence_end_point(
                    wave, self.volume_threshold, self.silence_check_chunk, self.silence_check_stride
                )

                if start_idx is None and not record_start:
                    waiting_length_for_timeout += self.buffer_size
                    if waiting_length_for_timeout >= int(waiting_timeout * self.sample_rate):
                        return
                    else:
                        continue
                elif start_idx is None and record_start:
                    silence_length += self.buffer_size

                elif start_idx is not None and not record_start:
                    record_start = True
                    wave = wave[start_idx:]
                    silence_length = 0

                elif start_idx is not None:
                    silence_length = 0

                if silence_length >= int(self.silence_duration_for_stop * self.sample_rate):
                    break

                recorded_length += len(wave)
                recorded_waves.append(wave)

                if recorded_length >= int(self.max_recording_duration * self.sample_rate):
                    break

            return np.concatenate(recorded_waves)

    def record_forever(self, wave_queue: Union[queue.Queue, Any]) -> None:
        """Record audio forever.

        Args:
            wave_queue (Queue): Queue for storing recorded waves.
                wave type is 1d `np.ndarray`.
        """
        self._shutdown = False

        send_and_reset = False

        record_start = False
        recorded_waves = []
        silence_length = 0
        recorded_length = 0

        with self.mic.recorder(self.sample_rate, 1) as mic:
            while not self._shutdown:

                if send_and_reset:
                    if len(recorded_waves) > 0:
                        wave_queue.put(np.concatenate(recorded_waves))

                    record_start = False
                    recorded_waves.clear()
                    recorded_length = 0
                    silence_length = 0

                    send_and_reset = False

                wave = mic.record(self.buffer_size).reshape(-1).astype("float32")
                start_idx = check_silence_end_point(
                    wave, self.volume_threshold, self.silence_check_chunk, self.silence_check_stride
                )

                if start_idx is None and not record_start:
                    continue

                elif start_idx is not None and not record_start:
                    wave = wave[:start_idx]
                    record_start = True

                elif start_idx is None and record_start:
                    silence_length += len(wave)

                recorded_length += len(wave)
                recorded_waves.append(wave)

                if silence_length >= int(self.silence_duration_for_stop * self.sample_rate):
                    send_and_reset = True
                    continue

                if recorded_length >= int(self.max_recording_duration * self.sample_rate):
                    send_and_reset = True
                    continue

            if len(recorded_waves) > 0:
                wave_queue.put(np.concatenate(recorded_waves))  # For test code.

    _record_forever_thread: Optional[threading.Thread] = None

    def record_forever_background(
        self, wave_queue: Optional[Union[queue.Queue, Any]] = None, is_daemon: bool = False
    ) -> Union[queue.Queue, Any]:
        """Throw :meth:`record_forever` to background thread.
        Args:
            wave_queue (Optional[Union[Queue, Any]]): Queue for storing recorded waves.
            is_daemon (bool): Whether `record_forever` thread is daemon thread or not.

        Returns:
            wave_queue (Queue): Queue for storing recorded waves.
        """

        if wave_queue is None:
            q = queue.Queue()
        else:
            q = wave_queue

        self._record_forever_thread = threading.Thread(target=self.record_forever, args=(q,), daemon=is_daemon)
        self._record_forever_thread.start()
        return q

    def shutdown_record_forever(self, timeout: Optional[float] = None) -> None:
        """Shutdown (stop) `record_forever` thread.

        Args:
            timeout (Optional[float]): Waiting for shutdown until timeout.
        """
        self._shutdown = True

        if self._record_forever_thread is not None:
            self._record_forever_thread.join(timeout)
