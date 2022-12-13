import os
import queue
import time
from argparse import ArgumentParser
from datetime import datetime

import toml
from whisper import DecodingOptions

from .chatbot import ChatBot
from .recorder import Recorder, display_audio_devices
from .run_parallely import run_parallely
from .speech_recongnition import SpeechRecongition
from .text_speaker import TextSpeaker

DISPLAY_AUDIO_DEVICES = "audio-devices"
RUN = "run"
CHAT = "chat"
RECOGNIZE = "recognize"
RUN_PARALLELY = "run-parallely"


def get_parser() -> ArgumentParser:
    """Making argument parser."""
    parser = ArgumentParser()

    parser.add_argument("command", type=str, choices=[DISPLAY_AUDIO_DEVICES, RUN, CHAT, RECOGNIZE, RUN_PARALLELY])
    parser.add_argument("-c", "--config_file_path", type=str, default="botconfig.toml")
    parser.add_argument("--log_dir", type=str, default="data/logs/")

    return parser


def main(args, config: dict) -> None:
    print("Setting up...")
    recorder = Recorder(**config["Recorder"])
    speech_recognizer = SpeechRecongition(
        options=DecodingOptions(**config["DecodingOption"]), **config["SpeechRecognition"]
    )
    chatbot = ChatBot(**config["ChatBot"])
    speaker = TextSpeaker(**config["Speaker"])
    print("Ready.")

    log_file_name = datetime.now().strftime("%Y-%m-%d %H-%M-%S.log")

    with open(os.path.join(args.log_dir, log_file_name), "a", encoding="utf-8") as logf:
        while True:
            wave = recorder.record_audio_until_silence(5)
            if wave is None:
                continue
            _, text = speech_recognizer.recongnize(wave)
            if text == "":
                continue

            rec_txt = f"Recongnized: {text}\n"
            logf.write(rec_txt)
            print(rec_txt)
            responce = chatbot.responce(text)
            rsp_txt = f"Responce: {responce}\n"
            logf.write(rsp_txt)
            print(rsp_txt)

            speaker.speak_text(responce)


def chat(args, config: dict) -> None:
    print("Setting up...")
    chatbot = ChatBot(**config["ChatBot"])
    print("Ready.")

    log_file_name = datetime.now().strftime("%Y-%m-%d %H-%M-%S.log")
    with open(os.path.join(args.log_dir, log_file_name), "a", encoding="utf-8") as logf:
        while True:
            user_input = input(chatbot.human_name)
            logf.write(f"{chatbot.human_name}{user_input}\n")
            responce = chatbot.responce(user_input)
            print(chatbot.ai_name, responce)
            logf.write(f"{chatbot.ai_name}{responce}\n")


def recoginize_forever(args, config: dict) -> None:
    """Demonstration for speech recoginition."""
    print("Setting up...")
    recorder = Recorder(**config["Recorder"])
    speech_recognizer = SpeechRecongition(
        options=DecodingOptions(**config["DecodingOption"]), **config["SpeechRecognition"]
    )
    wave_queue = recorder.record_forever_background(is_daemon=True)
    print("Ready.")

    log_file_name = datetime.now().strftime("%Y-%m-%d %H-%M-%S.log")
    with open(os.path.join(args.log_dir, log_file_name), "a", encoding="utf-8") as logf:
        while True:
            try:
                wave = wave_queue.get(timeout=5)
                probs, text = speech_recognizer.recongnize(wave)
                msg = f"{max(probs, key=probs.get)}: {text}\n"
                print(msg, end="")
                logf.write(msg)

            except queue.Empty:
                pass

            time.sleep(0.01)


def _run_parallely_main(args, config: dict) -> None:
    """Parallely."""
    print("Setting up...")
    recorder = Recorder(**config["Recorder"])
    speech_recognizer = SpeechRecongition(
        options=DecodingOptions(**config["DecodingOption"]), **config["SpeechRecognition"]
    )
    chatbot = ChatBot(**config["ChatBot"])
    speaker = TextSpeaker(**config["Speaker"])
    print("Ready.")

    run_parallely(recorder, speech_recognizer, chatbot, speaker, args.log_dir)


if __name__ == "__main__":

    parser = get_parser()
    args = parser.parse_args()

    if args.command == DISPLAY_AUDIO_DEVICES:
        display_audio_devices()
    elif args.command == RUN:
        cfg = toml.load(args.config_file_path)
        main(args, cfg)
    elif args.command == CHAT:
        cfg = toml.load(args.config_file_path)
        chat(args, cfg)
    elif args.command == RECOGNIZE:
        cfg = toml.load(args.config_file_path)
        recoginize_forever(args, cfg)
    elif args.command == RUN_PARALLELY:
        cfg = toml.load(args.config_file_path)
        _run_parallely_main(args, cfg)
