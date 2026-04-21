"""Legal AI Demos — Streamlit entry point.

Run locally:

    streamlit run app.py

Configure once via .env (see .env.example). Provider is selected by the
PROVIDER env var; no code changes needed to switch between Gemini and OpenAI.
"""

from __future__ import annotations

import streamlit as st

from core.llm_client import current_model, current_provider
from demos import chronology, correspondence, templates

st.set_page_config(page_title="Legal AI Demos", layout="wide")


def _sidebar() -> None:
    st.sidebar.title("Legal AI Demos")
    st.sidebar.markdown(
        "Three local, attorney-focused demos. Your data never leaves your "
        "machine except through the API call you trigger — and you get a "
        "preview of exactly what goes over the wire."
    )
    st.sidebar.divider()
    st.sidebar.markdown("**Active provider**")
    st.sidebar.code(f"{current_provider()} / {current_model()}", language="text")
    st.sidebar.caption("Change `PROVIDER` and the matching key in `.env`, then restart.")


def _privacy_tab() -> None:
    st.header("Privacy & ethics")
    st.markdown(
        """
These demos call a third-party API (Google Gemini or OpenAI). Before using them on real
client information, understand the following:

**1. Data retention differs by provider and tier.**

- **Gemini API** (paid tier): prompts are not used to train models. Retention windows are
  documented at [ai.google.dev](https://ai.google.dev/gemini-api/terms).
- **OpenAI API** (not ChatGPT consumer): prompts are not used to train models by default,
  and there is a 30-day abuse-monitoring retention window. Zero-retention is available on
  request for eligible accounts. See [openai.com/enterprise-privacy](https://openai.com/enterprise-privacy/).
- **Consumer chat UIs** (free ChatGPT, Gemini app, etc.) have different terms and should
  generally not be used for unredacted client material.

**2. The anonymizer is a safety net, not a waiver.**

It replaces SSNs, phone numbers, email addresses, and a list of names you provide with
stable tokens. It will not catch:
- Names you forget to add to the list.
- Case numbers, policy numbers, account numbers.
- Identifying facts (employer, rare medical conditions, unique addresses).

Always use the **"Preview what will be sent"** panel before clicking send.

**3. Your ethical obligations are unchanged.**

Texas Disciplinary Rule 1.05 (Confidentiality) and the ABA's Formal Opinion 512 on generative
AI apply. Treat any prompt as a disclosure to the vendor's systems, review every output
before filing or sending, and document your AI use where required by local rule.

**4. Practical tips.**

- Use the API (this app) rather than a consumer chat UI for anything client-related.
- Prefer the paid tier of whichever provider you choose — the free tier often has different
  retention defaults.
- Anonymize first, then review the preview, then send.
- Save outputs locally; don't rely on the provider to keep a history.
        """
    )


def main() -> None:
    _sidebar()
    tab_chrono, tab_corr, tab_tmpl, tab_priv = st.tabs(
        ["Chronology", "Correspondence", "Templates", "Privacy"]
    )
    with tab_chrono:
        chronology.render()
    with tab_corr:
        correspondence.render()
    with tab_tmpl:
        templates.render()
    with tab_priv:
        _privacy_tab()


if __name__ == "__main__":
    main()
