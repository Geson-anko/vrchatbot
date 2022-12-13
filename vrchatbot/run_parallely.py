import os
import queue
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .chatbot import ChatBot
from .recorder import Recorder
from .speech_recongnition import SpeechRecongition
from .text_speaker import TextSpeaker


@dataclass
class Context:
    recognized_text_queue: queue.Queue
    shutdown: bool = False


def speech_recognition_thread(context: Context, recorder: Recorder, recognizer: SpeechRecongition) -> None:
    """speech recognition for background thread
    Args:
        context (Context): Shared value
        recoder (Recoder): Mic recoder. must have `record_forever_background` method
        recognizer (SpeechRecognition): must have `recognize` method.
    """

    wave_queue = recorder.record_forever_background(is_daemon=True)

    while not context.shutdown:
        try:
            wave = wave_queue.get(timeout=5)
            _, text = recognizer.recongnize(wave)
            if text != "":
                context.recognized_text_queue.put(text)

        except queue.Empty:
            pass


def run_parallely(
    recorder: Recorder, recognizer: SpeechRecongition, chatbot: ChatBot, speaker: TextSpeaker, log_dir: Any = "./"
) -> None:
    """Run bot process parallely.

    Main thread processes language, and Sub thread processes audio.
    """
    recognized_text_queue = queue.Queue()
    context = Context(recognized_text_queue, False)
    audio_thread = threading.Thread(target=speech_recognition_thread, args=(context, recorder, recognizer))
    audio_thread.start()
    log_file_name = datetime.now().strftime("%Y-%m-%d %H-%M-%S.parallely.log")
    print("run-parallely")
    try:
        with open(os.path.join(log_dir, log_file_name), "a", encoding="utf-8") as logf:
            while True:
                try:
                    qsize = recognized_text_queue.qsize()
                    if qsize == 0:
                        user_input = recognized_text_queue.get(timeout=5)
                    else:
                        user_input = " ".join([recognized_text_queue.get_nowait() for _ in range(qsize)])

                    rec_txt = f"Recongnized: {user_input}\n"
                    print(rec_txt)
                    logf.write(rec_txt)
                    responce = chatbot.responce(user_input)
                    rsp_txt = f"Responce: {responce}\n"
                    print(rsp_txt)
                    logf.write(rsp_txt)

                    speaker.speak_text(responce)

                except queue.Empty:
                    pass
    except KeyboardInterrupt:
        pass

    print("Shutdown...")

    context.shutdown = True
    audio_thread.join()
