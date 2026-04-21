"""Unified text-generation interface over Gemini and OpenAI.

Demos never import provider SDKs directly — they only call `generate(...)`.
"""

from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"


class LLMConfigError(RuntimeError):
    """Raised when required provider configuration is missing."""


def current_provider() -> str:
    return os.getenv("PROVIDER", "gemini").strip().lower()


def current_model() -> str:
    if current_provider() == "openai":
        return os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
    return os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)


@lru_cache(maxsize=1)
def _gemini_client():
    from google import genai

    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise LLMConfigError(
            "GEMINI_API_KEY is not set. Add it to your .env file "
            "(get one at https://aistudio.google.com/app/apikey), then restart."
        )
    return genai.Client(api_key=key)


@lru_cache(maxsize=1)
def _openai_client():
    from openai import OpenAI

    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise LLMConfigError(
            "OPENAI_API_KEY is not set. Add it to your .env file "
            "(get one at https://platform.openai.com/api-keys), then restart."
        )
    return OpenAI(api_key=key)


def generate(system: str, user: str, temperature: float = 0.3) -> str:
    """Send a single-turn prompt to the configured provider and return the text.

    Args:
        system: Instructions that set role, tone, and output format.
        user: The actual request / content to operate on.
        temperature: 0.0 = deterministic, 1.0 = creative. Default 0.3 suits legal drafting.
    """
    provider = current_provider()

    if provider == "gemini":
        from google.genai import types

        client = _gemini_client()
        resp = client.models.generate_content(
            model=current_model(),
            contents=user,
            config=types.GenerateContentConfig(
                system_instruction=system,
                temperature=temperature,
            ),
        )
        return (resp.text or "").strip()

    if provider == "openai":
        client = _openai_client()
        resp = client.chat.completions.create(
            model=current_model(),
            temperature=temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return (resp.choices[0].message.content or "").strip()

    raise LLMConfigError(
        f"Unknown PROVIDER={provider!r}. Set PROVIDER to 'gemini' or 'openai' in .env."
    )
