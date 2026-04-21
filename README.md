# Legal AI Demos

Three local, attorney-focused demos that run on any machine with Python and either a Gemini **or** an OpenAI API key:

1. **Chronology Builder** — upload discovery documents or client notes and get a date-sorted timeline.
2. **Correspondence Drafter** — draft client emails or translate legalese into plain language.
3. **Template Generator** — feed an existing boilerplate (will, motion, etc.) plus client details and get a customized first draft.

Every demo includes a **PII anonymizer** so you can preview exactly what leaves your machine before calling the API.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # then edit .env and paste in ONE API key
```

Get a key:

- Gemini: https://aistudio.google.com/app/apikey
- OpenAI: https://platform.openai.com/api-keys

Set `PROVIDER=gemini` or `PROVIDER=openai` in `.env`. The same three demos work with either.

## Run

```bash
streamlit run app.py
```

Opens at http://localhost:8501.

## Switching providers

Edit `.env`, change `PROVIDER`, restart Streamlit. No code changes.

## Privacy note

These demos call a third-party API. Even with anonymization enabled, review everything before sending. See the **Privacy** tab inside the app for specifics on data retention and enterprise-tier options.
