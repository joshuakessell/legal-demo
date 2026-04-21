"""Demo 2 — Correspondence Drafter.

Two modes in one tab:
  - Draft a client / counsel email from bullet points + tone.
  - Translate legalese into plain English suitable for a client letter.
"""

from __future__ import annotations

import streamlit as st

from core import samples
from core.anonymizer import anonymize
from core.llm_client import generate

EMAIL_SYSTEM_PROMPT = """You are drafting professional correspondence on behalf of a Texas attorney.

Rules:
- Match the requested tone exactly.
- Never promise a legal outcome.
- Use plain, clear sentences; no more than one legal term per paragraph without a parenthetical explanation.
- End with a signature block placeholder: "Sincerely,\\n[Attorney Name]\\n[Firm]".
- Keep it under ~250 words unless the user's bullets clearly need more.
- If any bullet is ambiguous or legally risky, add a single line at the end starting with "NOTE FOR ATTORNEY:" flagging it.
"""

PLAIN_SYSTEM_PROMPT = """You are translating legal text into plain English for a client with no legal training.

Rules:
- Preserve the legal meaning precisely — if something is a condition, keep it a condition; if something is optional, keep it optional.
- Target an 8th-grade reading level.
- Expand defined terms on first use (e.g., "indemnify (agree to cover the other side's losses)").
- Do not add advice, recommendations, or outcomes. You are translating, not counseling.
- If anything in the source is genuinely ambiguous, finish with a "Things worth asking your attorney about:" bulleted list.
"""


def _anonymize_panel(raw: str, key_prefix: str) -> tuple[str, dict[str, str]]:
    with st.expander("Anonymize PII before sending (recommended)", expanded=False):
        enable = st.checkbox("Enable anonymization", value=True, key=f"{key_prefix}_anon")
        names_raw = st.text_input(
            "Names to scrub (comma-separated)", key=f"{key_prefix}_names"
        )
    if not enable:
        return raw, {}
    names = [n.strip() for n in names_raw.split(",")] if names_raw else []
    result = anonymize(raw, names)
    return result.text, result.mapping


def _preview(outbound: str, mapping: dict[str, str]) -> None:
    with st.expander("Preview what will be sent to the API", expanded=False):
        st.code(outbound[:4000] + ("…" if len(outbound) > 4000 else ""), language="text")
        if mapping:
            st.caption("Token → original mapping (stays on your machine):")
            st.json(mapping)


def _restore(output: str, mapping: dict[str, str]) -> str:
    restored = output
    for token, original in mapping.items():
        restored = restored.replace(token, original)
    return restored


def _load_email_sample() -> None:
    s = samples.email_sample()
    st.session_state["email_recipient"] = s["recipient"]
    st.session_state["email_tone"] = s["tone"]
    st.session_state["email_bullets"] = s["bullets"]


def _render_email() -> None:
    st.subheader("Draft an email")

    with st.expander("Load sample inputs", expanded=False):
        s = samples.email_sample()
        st.markdown(f"**Recipient context:**  {s['recipient']}")
        st.markdown(f"**Tone:**  {s['tone']}")
        st.markdown("**Key points:**")
        st.code(s["bullets"], language="text")
        st.button(
            "Fill fields with sample",
            on_click=_load_email_sample,
            key="email_sample_btn",
        )

    recipient = st.text_input(
        "Recipient context",
        key="email_recipient",
        placeholder="Opposing counsel in a custody matter",
    )
    tone = st.selectbox("Tone", ["Neutral", "Warm", "Firm"], key="email_tone")
    bullets = st.text_area(
        "Key points (one per line)",
        height=160,
        key="email_bullets",
        placeholder="- Confirm receipt of discovery\n- Propose mediation dates\n- Flag that exhibit B is illegible",
    )

    if st.button("Draft email", type="primary", key="email_run"):
        if not bullets.strip():
            st.warning("Add at least one bullet point.")
            return
        raw = (
            f"Recipient context: {recipient or '(unspecified)'}\n"
            f"Tone: {tone}\n\nKey points:\n{bullets.strip()}"
        )
        outbound, mapping = _anonymize_panel(raw, "email")
        _preview(outbound, mapping)
        with st.spinner("Calling the model…"):
            try:
                reply = generate(EMAIL_SYSTEM_PROMPT, outbound, temperature=0.4)
            except Exception as exc:
                st.error(str(exc))
                return
        st.markdown("### Draft")
        st.markdown(_restore(reply, mapping))


def _load_plain_sample() -> None:
    st.session_state["plain_source"] = samples.plain_legalese()


def _render_plain() -> None:
    st.subheader("Translate legalese to plain English")

    with st.expander("Load sample legalese", expanded=False):
        st.caption("A dense indemnification clause from a fictional commercial lease.")
        preview = samples.plain_legalese()
        st.code(preview[:600] + ("…" if len(preview) > 600 else ""), language="text")
        st.button(
            "Fill field with sample",
            on_click=_load_plain_sample,
            key="plain_sample_btn",
        )

    source = st.text_area(
        "Legal text",
        height=260,
        key="plain_source",
        placeholder="Paste a contract clause, court order, or statute excerpt here…",
    )

    if st.button("Translate", type="primary", key="plain_run"):
        if not source.strip():
            st.warning("Paste some legal text first.")
            return
        outbound, mapping = _anonymize_panel(source.strip(), "plain")
        _preview(outbound, mapping)
        with st.spinner("Calling the model…"):
            try:
                reply = generate(PLAIN_SYSTEM_PROMPT, outbound, temperature=0.2)
            except Exception as exc:
                st.error(str(exc))
                return
        st.markdown("### Plain-English version")
        st.markdown(_restore(reply, mapping))


def render() -> None:
    st.header("Correspondence Drafter")
    st.caption("Draft client emails, or translate legal text into plain English.")
    mode = st.radio(
        "Mode",
        ["Draft an email", "Translate legalese to plain English"],
        horizontal=True,
        key="corr_mode",
    )
    if mode == "Draft an email":
        _render_email()
    else:
        _render_plain()
