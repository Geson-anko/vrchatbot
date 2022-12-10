from collections import deque
from typing import Any, Optional

import openai


class ChatBot:
    """Interface class for chatbot."""

    def __init__(
        self,
        api_key_file_path: Any,
        engine: str = "text-davinci-003",
        max_tokens=128,
        max_receptive_tokens: int = 4096,
        free_tokens_for_user: int = 128,
        temperature=0.9,
        behaviour_prompt: Optional[str] = None,
        human_name: str = "人間:",
        ai_name: str = "人工知能:",
        **kwds: dict,
    ) -> None:
        """
        Args:
            api_key_file_path (str | Pathlike): Path to the api key file.
            engine (str): OpenAI language model engine name.
            max_tokens (int): The maximum number of tokens to generate in the completion.
            max_receptive_tokens (int): The maximum token size for language model input. Please see OpenAI text engine document.
            free_tokens_for_user (int): Free space for user text.
            temperature (float): Temperature of output probability.
            behaviour_prompt_path (Optional[str]):  The first prompt for conversation.
            kwds: Other key word arguments for `Completion.create`.
        """

        with open(api_key_file_path, "r", encoding="utf-8") as f:
            api_key = f.read()
        if api_key == "":
            raise RuntimeError(f"Please write api key to {api_key_file_path}")

        openai.api_key = api_key
        self.engine = engine
        self.max_tokens = max_tokens
        self.max_receptive_tokens = max_receptive_tokens
        self.free_tokens_for_user = free_tokens_for_user
        self.tail_space = free_tokens_for_user + max_tokens
        self.temperature = temperature
        self.behaivour_prompt = behaviour_prompt
        self.human_name = human_name
        self.ai_name = ai_name
        self.completion_kwds = kwds

        if behaviour_prompt is not None:
            resp = openai.Completion.create(
                engine=self.engine,
                prompt=behaviour_prompt,
                max_tokens=10,
                temperature=self.temperature,
                **self.completion_kwds,
            )
            self.behaivour_prompt_token_size = resp["usage"]["completion_tokens"]
        else:
            self.behaivour_prompt_token_size = 0

        self.reset()

    def reset(self):
        """Reset internal state."""
        self.current_token_size = self.behaivour_prompt_token_size
        self.stored_prompts = deque()
        self.stored_prompts_token_sizes = deque()

    def make_tail_space(self) -> None:
        """Make tail space."""

        while self.max_receptive_tokens - self.current_token_size < self.tail_space:
            self.stored_prompts.popleft()
            self.current_token_size -= self.stored_prompts_token_sizes.popleft()

    def responce(self, user_input: str) -> str:
        """Communicate to OpenAI api.

        Args:
            user_input (str): User input text.

        Returns:
            responce (str): Responce text.
        """

        self.make_tail_space()

        user_input = f"{self.human_name} {user_input}\n{self.ai_name}"
        if self.behaivour_prompt is None:
            head = []
        else:
            head = [self.behaivour_prompt]

        sending_prompt = head + list(self.stored_prompts) + [user_input]

        resp = openai.Completion.create(
            engine=self.engine,
            prompt=sending_prompt,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            **self.completion_kwds,
        )

        text = resp["choices"][0]["text"]
        self.stored_prompts_token_sizes.append(resp["usage"]["completion_tokens"] - self.current_token_size)
        self.stored_prompts.append(user_input)
        self.stored_prompts_token_sizes.append(resp["usage"]["prompt_tokens"])
        self.stored_prompts.append(text)

        return text
