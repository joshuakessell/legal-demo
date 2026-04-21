"""Deterministic PII scrubber for attorney workflows.

Replaces SSNs, phone numbers, email addresses, and user-supplied names with
stable tokens so the LLM can still reason about "the same person" across
mentions without the real values ever leaving the machine.

Returns both the scrubbed text and the mapping, so the UI can:
  - show the user exactly what will be sent to the API
  - optionally restore real names in the model's output afterward
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
PHONE_RE = re.compile(
    r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
)
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")


@dataclass
class AnonymizationResult:
    text: str
    mapping: dict[str, str] = field(default_factory=dict)

    def restore(self, output: str) -> str:
        """Swap tokens in `output` back to their original values."""
        restored = output
        for token, original in self.mapping.items():
            restored = restored.replace(token, original)
        return restored


def _sub_with_token(pattern: re.Pattern, text: str, prefix: str, mapping: dict[str, str]) -> str:
    counter = {"n": 0}
    seen: dict[str, str] = {}

    def repl(match: re.Match) -> str:
        original = match.group(0)
        if original in seen:
            return seen[original]
        counter["n"] += 1
        token = f"[{prefix}_{counter['n']}]"
        seen[original] = token
        mapping[token] = original
        return token

    return pattern.sub(repl, text)


def anonymize(text: str, names: list[str] | None = None) -> AnonymizationResult:
    """Scrub PII from `text`.

    Args:
        text: Input text.
        names: Optional list of names (and other sensitive tokens) to replace
            with `[PERSON_1]`, `[PERSON_2]`, etc. Matching is case-insensitive
            and whole-word-ish. Longer names are replaced first so that
            "John Doe" doesn't get partially matched as "John".
    """
    if not text:
        return AnonymizationResult(text=text)

    mapping: dict[str, str] = {}
    out = text

    if names:
        cleaned = sorted({n.strip() for n in names if n and n.strip()}, key=len, reverse=True)
        for i, name in enumerate(cleaned, start=1):
            token = f"[PERSON_{i}]"
            pattern = re.compile(re.escape(name), re.IGNORECASE)
            if pattern.search(out):
                out = pattern.sub(token, out)
                mapping[token] = name

    out = _sub_with_token(SSN_RE, out, "SSN", mapping)
    out = _sub_with_token(EMAIL_RE, out, "EMAIL", mapping)
    out = _sub_with_token(PHONE_RE, out, "PHONE", mapping)

    return AnonymizationResult(text=out, mapping=mapping)
