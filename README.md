# AHAA : Adaptive Health Advisor Agent

A local, privacy-first health advisory app that generates personalized nutrition and workout plans. It combines a deterministic computation engine (BMR/TDEE/BMI, macros) with a guardrail-checked LLM (via Ollama) orchestrated by a LangGraph pipeline.

## Features

- **Deterministic metrics**: BMI, BMR (Mifflin–St Jeor), TDEE, calorie targets, and macro splits computed in Python — not hallucinated.
- **Safety engine**: Condition/injury/allergy checks build forbidden-food and forbidden-move lists before any LLM call.
- **LangGraph pipeline**: `compute_metrics → safety_check → build_prompt` produces a constrained system prompt.
- **Streaming responses**: Server-Sent Events stream the full 9-section health report and chat replies token-by-token from Ollama.
- **Local LLM**: Runs against a local Ollama instance (default `llama3.2:3b`). No data leaves the machine.
- **Single-page UI**: Jinja template + vanilla JS frontend.

## Architecture

```
templates/index.html  ──►  routes/main.py        (renders UI)
static/js, static/css ──►  routes/api.py         (/api/generate, /api/chat, /api/health)
                              │
                              ▼
                      agents/graph.py            (LangGraph)
                      ├─ compute_metrics_node ──► engines/computation.py
                      ├─ safety_check_node    ──► engines/safety.py
                      └─ build_prompt_node    ──► engines/safety.py
                              │
                              ▼
                      Ollama /api/chat (stream)
```

## Requirements

- Python 3.10+
- [Ollama](https://ollama.com) running locally
- A pulled model, e.g. `ollama pull llama3.2:3b`

## Setup

```bash
git clone https://github.com/devangkamble/AHAA.git
cd AHAA

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env               # then edit values
```

### Environment variables

| Variable           | Default                    | Purpose                          |
|--------------------|----------------------------|----------------------------------|
| `OLLAMA_BASE_URL`  | `http://localhost:11434`   | Ollama server URL                |
| `OLLAMA_MODEL`     | `llama3.2:3b`              | Local model name                 |
| `FLASK_DEBUG`      | `true`                     | Flask debug mode                 |
| `FLASK_SECRET_KEY` | `ahaa-dev-secret`          | Change in production             |

## Run

Start Ollama in one terminal:

```bash
ollama serve
```

Start AHAA:

```bash
python app.py
```

Open <http://localhost:5000>.

Windows users can double-click `START.bat`.

## API

| Method | Path             | Description                                              |
|--------|------------------|----------------------------------------------------------|
| GET    | `/`              | Web UI                                                   |
| POST   | `/api/generate`  | Generate full health report (SSE stream)                 |
| POST   | `/api/chat`      | Follow-up chat with persisted system prompt (SSE stream) |
| GET    | `/api/health`    | Health check + Ollama connectivity + available models    |

### Example: `/api/generate`

```json
{
  "profile": {
    "height_cm": 175,
    "weight_kg": 78,
    "age": 30,
    "gender": "Male",
    "activity_level": 2,
    "goals": ["loss"],
    "conditions": [],
    "injuries": [],
    "food_allergies": [],
    "drug_allergies": []
  }
}
```

Response is `text/event-stream` with event types: `metrics`, `safety`, `system_prompt`, `chunk`, `error`, `done`.

## Project layout

```
AHAA/
├── app.py                 # Flask app factory + entrypoint
├── server.py              # Standalone Anthropic-proxy runner (alternate)
├── config.py              # Pydantic settings loader
├── requirements.txt
├── agents/                # LangGraph state, nodes, graph
├── engines/               # computation.py, safety.py
├── models/schemas.py      # Pydantic request/response models
├── routes/                # main.py (UI), api.py (SSE endpoints)
├── templates/index.html   # Jinja template
├── static/                # css, js
└── START.bat              # Windows launcher
```

## Disclaimer

AHAA is an educational/informational tool. It is **not** a substitute for professional medical advice, diagnosis, or treatment. Consult a qualified clinician before acting on any output, especially with existing medical conditions, medications, or injuries.

## License

No license file present. All rights reserved by the author unless a license is added.
