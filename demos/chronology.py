"""Demo 1 — Chronology Builder.

Upload discovery docs or paste mixed-order narrative; get a date-sorted
markdown timeline with source-snippet citations per row.
"""

from __future__ import annotations

import streamlit as st

from core import samples
from core.anonymizer import anonymize
from core.file_loader import load_text
from core.llm_client import generate

SYSTEM_PROMPT = """You are a paralegal assistant building a chronology of events for an attorney.

From the source material below, extract every dated event and produce a chronology as a markdown table with three columns:

| Date | Event | Source |
|------|-------|--------|

Rules:
- One row per event.
- Sort strictly by date ascending. If a date is approximate, use the best available form (e.g., "2023-03 (approx.)") and sort it where it fits best.
- "Event" is one sentence, neutral, factual, no legal conclusions.
- "Source" is a short verbatim snippet (< 120 characters) from the input that supports the row, in quotes.
- If the source material is internally inconsistent, add a final "## Inconsistencies" section listing each conflict as a bullet.
- If no dated events can be extracted, say so explicitly.
"""


def _load_samples() -> None:
    st.session_state["chrono_sample_chunks"] = samples.chronology_files()


def _clear_samples() -> None:
    st.session_state.pop("chrono_sample_chunks", None)


def _sample_section() -> None:
    with st.expander("Load sample documents (fictional custody matter)", expanded=False):
        files = samples.chronology_files()
        st.caption(
            "Three fabricated source docs from *Parker v. Doe*. "
            "All names, dates, phones, and addresses are fake."
        )
        for name, text in files:
            st.markdown(f"**{name}**  ·  {len(text.split())} words")
            preview = text[:400] + ("…" if len(text) > 400 else "")
            st.code(preview, language="text")
        st.button(
            f"Import all {len(files)} sample files",
            on_click=_load_samples,
            key="chrono_sample_btn",
        )

    loaded = st.session_state.get("chrono_sample_chunks")
    if loaded:
        c1, c2 = st.columns([5, 1])
        c1.success(f"{len(loaded)} sample file(s) loaded and ready to process.")
        c2.button("Clear", on_click=_clear_samples, key="chrono_sample_clear")


def render() -> None:
    st.header("Chronology Builder")
    st.caption(
        "Upload mixed discovery files or paste in notes. The model returns a date-sorted timeline "
        "with a source snippet for every row."
    )

    _sample_section()

    uploads = st.file_uploader(
        "Upload source documents (.txt, .md, .pdf, .docx)",
        type=["txt", "md", "pdf", "docx"],
        accept_multiple_files=True,
        key="chrono_uploads",
    )
    pasted = st.text_area(
        "Or paste notes / narrative directly",
        height=180,
        key="chrono_pasted",
        placeholder="On 3/4/2023 client met with... On June 1 he sent...",
    )

    with st.expander("Anonymize PII before sending (recommended)", expanded=True):
        enable = st.checkbox("Enable anonymization", value=True, key="chrono_anon")
        names_raw = st.text_input(
            "Names to scrub (comma-separated)",
            key="chrono_names",
            placeholder="Jane Doe, John Smith",
        )

    if st.button("Build chronology", type="primary", key="chrono_run"):
        chunks: list[str] = []
        if uploads:
            for f in uploads:
                try:
                    chunks.append(f"=== {f.name} ===\n{load_text(f.name, f.read())}")
                except Exception as exc:
                    st.error(f"Could not read {f.name}: {exc}")
                    return
        if pasted.strip():
            chunks.append(f"=== pasted notes ===\n{pasted.strip()}")
        for name, text in st.session_state.get("chrono_sample_chunks", []):
            chunks.append(f"=== {name} (sample) ===\n{text}")

        if not chunks:
            st.warning("Upload a file, paste text, or load the sample documents.")
            return

        raw_text = "\n\n".join(chunks)
        names = [n.strip() for n in names_raw.split(",")] if names_raw else []
        result = anonymize(raw_text, names) if enable else anonymize("", [])
        outbound = result.text if enable else raw_text

        with st.expander("Preview what will be sent to the API", expanded=False):
            st.code(outbound[:4000] + ("…" if len(outbound) > 4000 else ""), language="text")
            if enable and result.mapping:
                st.caption("Token → original mapping (stays on your machine):")
                st.json(result.mapping)

        with st.spinner("Calling the model…"):
            try:
                reply = generate(SYSTEM_PROMPT, outbound, temperature=0.1)
            except Exception as exc:
                st.error(str(exc))
                return

        final = result.restore(reply) if enable else reply
        st.markdown("### Chronology")
        st.markdown(final)
        st.download_button(
            "Download as .md",
            data=final,
            file_name="chronology.md",
            mime="text/markdown",
        )
