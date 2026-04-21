"""Access to bundled sample documents in `samples/`.

Each demo pulls pre-canned content from here so the user can populate the
form without touching the file picker.
"""

from __future__ import annotations

import re
from pathlib import Path

SAMPLES_ROOT = Path(__file__).resolve().parent.parent / "samples"


def _read(rel: str) -> str:
    return (SAMPLES_ROOT / rel).read_text(encoding="utf-8")


def chronology_files() -> list[tuple[str, str]]:
    """All chronology source documents as (filename, text) pairs, sorted."""
    d = SAMPLES_ROOT / "chronology"
    return [
        (p.name, p.read_text(encoding="utf-8"))
        for p in sorted(d.glob("*.txt"))
    ]


def plain_legalese() -> str:
    return _read("correspondence/legalese_clause.txt")


def email_sample() -> dict[str, str]:
    """Structured inputs for the email-drafting sub-tab."""
    return {
        "recipient": "Client in a pending divorce matter (first follow-up after intake)",
        "tone": "Warm",
        "bullets": "\n".join(
            [
                "- Thank Jane for coming in Thursday and for the documents she already forwarded.",
                "- Confirm we will file the petition for SAPCR modification within the next two weeks.",
                "- Ask her to send the screenshots of the 8/14 and 9/27 text messages if she hasn't already.",
                "- Remind her to keep a running log of missed or shortened possession periods.",
                "- Mention that our paralegal, Katie, will reach out separately about the filing fee.",
                "- Note that nothing in this email should be forwarded to John Parker.",
                "- Invite her to call with any questions; our number is 972-555-0132.",
            ]
        ),
    }


def template_text() -> str:
    return _read("templates/will_template.txt")


def template_facts() -> str:
    """The client-facts block, with the instructional header + dashed separator stripped."""
    raw = _read("templates/client_facts.txt")
    match = re.search(r"^-{5,}$", raw, flags=re.MULTILINE)
    if match:
        return raw[match.end():].strip()
    return raw.strip()
