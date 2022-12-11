from argparse import ArgumentParser
from datetime import datetime

import toml
from whisper import DecodingOptions

from .audio_tools import Recorder, TextSpeaker, display_audio_devices
from .chatbot import ChatBot
from .speech_recongnition import SpeechRecongition

DISPLAY_AUDIO_DEVICES = "audio-devices"
RUN = "run"
CHAT = "chat"


def get_parser() -> ArgumentParser:
    """Making argument parser."""
    parser = ArgumentParser()

    parser.add_argument("command", type=str, choices=[DISPLAY_AUDIO_DEVICES, RUN, CHAT])
    parser.add_argument("-c", "--config_file_path", type=str, default="botconfig.toml")

    return parser


def main(config: dict) -> None:
    print("Setting up...")
    recorder = Recorder(**config["Recorder"])
    speech_recognizer = SpeechRecongition(
        options=DecodingOptions(**config["DecodingOption"]), **config["SpeechRecognition"]
    )
    chatbot = ChatBot(**config["ChatBot"])
    speaker = TextSpeaker(**config["Speaker"])
    print("Ready.")

    log_file_name = datetime.now().strftime("%Y-%m-%d %H-%M-%S.log")

    with open(f"data/logs/{log_file_name}", "a", encoding="utf-8") as logf:
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


def chat(config: dict) -> None:
    print("Setting up...")
    chatbot = ChatBot(**config["ChatBot"])
    print("Ready.")

    log_file_name = datetime.now().strftime("%Y-%m-%d %H-%M-%S.log")
    with open(f"data/logs/{log_file_name}", "a", encoding="utf-8") as logf:
        while True:
            user_input = input(chatbot.human_name)
            logf.write(f"{chatbot.human_name}{user_input}\n")
            responce = chatbot.responce(user_input)
            print(chatbot.ai_name, responce)
            logf.write(f"{chatbot.ai_name}{responce}\n")


if __name__ == "__main__":

    parser = get_parser()
    args = parser.parse_args()

    if args.command == DISPLAY_AUDIO_DEVICES:
        display_audio_devices()
    elif args.command == RUN:
        cfg = toml.load(args.config_file_path)
        main(cfg)
    elif args.command == CHAT:
        cfg = toml.load(args.config_file_path)
        chat(cfg)
