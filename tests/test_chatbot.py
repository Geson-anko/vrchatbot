from collections import deque

import pytest

from vrchatbot import chatbot as mod

api_key_file_path = "data/API_KEY.txt"

first_prompt = "次の会話は人工知能と人間の会話です。人工知能はとても元気で、知的で、創造的で、日本語を離します。"


def test_ChatBot__init__():
    cls = mod.ChatBot

    bot = cls(api_key_file_path)
    assert bot.engine == "text-davinci-003"
    assert bot.max_tokens == 128
    assert bot.max_receptive_tokens == 4096
    assert bot.free_tokens_for_user == 128
    assert bot.tail_space == bot.max_tokens + bot.free_tokens_for_user
    assert bot.temperature == 0.9
    assert bot.behaivour_prompt is None
    assert bot.human_name == "人間:"
    assert bot.ai_name == "人工知能:"
    assert bot.current_token_size == 0
    assert bot.stored_prompts == deque()
    assert bot.stored_prompts_token_sizes == deque()

    bot = cls(api_key_file_path, behaviour_prompt=first_prompt)
    assert bot.behaivour_prompt == first_prompt
    assert bot.current_token_size > 0


def test_ChatBot_make_tail_space():
    cls = mod.ChatBot
    bot = cls(api_key_file_path, max_tokens=5, max_receptive_tokens=20, free_tokens_for_user=5)

    bot.make_tail_space()  # nothing do

    bot.current_token_size = 15
    bot.stored_prompts.append("")
    bot.stored_prompts_token_sizes.append(15)
    bot.make_tail_space()
    assert bot.current_token_size == 0
    assert list(bot.stored_prompts) == []
    assert list(bot.stored_prompts_token_sizes) == []


def test_ChatBot_responce():
    cls = mod.ChatBot
    bot = cls(api_key_file_path, behaviour_prompt=first_prompt)

    user_inputs = ["こんばんわ", "はじめまして", "お話しませんか？"]

    for i in user_inputs:
        print("User:", i)
        resp_text = bot.responce(i)
        print("AI:", resp_text)
