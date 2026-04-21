"""Demo 3 — Template Generator.

Upload a boilerplate (will, motion, etc.) plus client-specific fields;
produce a customized first draft that preserves structure and flags anything
the model is uncertain about.
"""

from __future__ import annotations

import streamlit as st

from core.anonymizer import anonymize
from core.file_loader import docx_bytes_from_text, load_text
from core.llm_client import generate

SYSTEM_PROMPT = """You are customizing an existing legal template for a Texas attorney.

Rules:
- Preserve the template's structure, headings, numbering, and style. Do not rewrite the boilerplate.
- Fill placeholders and variable sections with the provided client-specific facts.
- Where a fact is missing but clearly required, insert "[[ATTORNEY REVIEW: <what's needed>]]".
- Where you are uncertain whether a fact belongs in a particular section, flag it the same way.
- Never invent case numbers, court names, statute citations, or dates. If a specific citation is needed and not provided, mark it "[[ATTORNEY REVIEW: insert citation]]".
- Output the full customized document, ready to paste into Word.
"""


def render() -> None:
    st.header("Template Generator")
    st.caption(
        "Upload your existing boilerplate and fill in the client-specific facts. "
        "The model returns a customized first draft with `[[ATTORNEY REVIEW]]` markers "
        "wherever it needs your judgment."
    )

    template_file = st.file_uploader(
        "Upload boilerplate (.txt, .md, .pdf, .docx)",
        type=["txt", "md", "pdf", "docx"],
        key="tmpl_upload",
    )
    fields = st.text_area(
        "Client-specific facts (free-form is fine; bullets are clearer)",
        height=220,
        key="tmpl_fields",
        placeholder=(
            "- Client name: Jane Doe\n"
            "- Spouse: John Doe\n"
            "- County: Rockwall County, Texas\n"
            "- Children: Alex Doe (8), Sam Doe (5)\n"
            "- Specific relief requested: sole managing conservatorship"
        ),
    )

    with st.expander("Anonymize PII before sending (recommended)", expanded=True):
        enable = st.checkbox("Enable anonymization", value=True, key="tmpl_anon")
        names_raw = st.text_input(
            "Names to scrub (comma-separated)",
            key="tmpl_names",
            placeholder="Jane Doe, John Doe, Alex Doe, Sam Doe",
        )

    if st.button("Generate draft", type="primary", key="tmpl_run"):
        if not template_file:
            st.warning("Upload a boilerplate document first.")
            return
        if not fields.strip():
            st.warning("Add the client-specific facts.")
            return

        try:
            template_text = load_text(template_file.name, template_file.read())
        except Exception as exc:
            st.error(f"Could not read {template_file.name}: {exc}")
            return

        raw = (
            f"=== TEMPLATE ===\n{template_text}\n\n"
            f"=== CLIENT-SPECIFIC FACTS ===\n{fields.strip()}"
        )
        names = [n.strip() for n in names_raw.split(",")] if names_raw else []
        result = anonymize(raw, names) if enable else anonymize("", [])
        outbound = result.text if enable else raw

        with st.expander("Preview what will be sent to the API", expanded=False):
            st.code(outbound[:4000] + ("…" if len(outbound) > 4000 else ""), language="text")
            if enable and result.mapping:
                st.caption("Token → original mapping (stays on your machine):")
                st.json(result.mapping)

        with st.spinner("Calling the model…"):
            try:
                reply = generate(SYSTEM_PROMPT, outbound, temperature=0.2)
            except Exception as exc:
                st.error(str(exc))
                return

        final = result.restore(reply) if enable else reply
        st.markdown("### Customized draft")
        st.markdown(final)
        st.download_button(
            "Download as .docx",
            data=docx_bytes_from_text(final),
            file_name="draft.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        st.download_button(
            "Download as .txt",
            data=final,
            file_name="draft.txt",
            mime="text/plain",
        )
