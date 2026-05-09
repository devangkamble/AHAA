"""API routes — /api/generate and /api/chat, streaming via direct Ollama requests."""
import json
import traceback

import requests as http
from flask import Blueprint, Response, request, stream_with_context
from pydantic import ValidationError

from agents.graph import ahaa_graph
from agents.state import AHAAState
from config import get_settings
from models.schemas import ChatRequest, GenerateRequest

api_bp = Blueprint("api", __name__, url_prefix="/api")


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


def _stream_ollama(system_prompt: str, messages: list[dict]):
    """Stream token chunks directly from Ollama /api/chat."""
    cfg = get_settings()
    ollama_messages = [{"role": "system", "content": system_prompt}] + messages

    resp = http.post(
        f"{cfg.OLLAMA_BASE_URL}/api/chat",
        json={
            "model": cfg.OLLAMA_MODEL,
            "stream": True,
            "messages": ollama_messages,
            "options": {
                "temperature": 0.1,
                "num_predict": 4096,
                "num_ctx": 8192,
                "top_p": 0.9,
            },
        },
        stream=True,
        timeout=300,
    )
    resp.raise_for_status()

    for line in resp.iter_lines():
        if not line:
            continue
        try:
            chunk = json.loads(line)
            text = chunk.get("message", {}).get("content", "")
            if text:
                yield text
            if chunk.get("done"):
                break
        except json.JSONDecodeError:
            pass


# ── POST /api/generate ────────────────────────────────────────
@api_bp.route("/generate", methods=["POST"])
def generate():
    try:
        req = GenerateRequest.model_validate(request.get_json(force=True) or {})
    except ValidationError as exc:
        errors = "; ".join(e["msg"] for e in exc.errors())
        return Response(
            _sse({"type": "error", "message": f"Validation: {errors}"}) + _sse({"type": "done"}),
            mimetype="text/event-stream",
        )

    def stream():
        try:
            # 1. Run LangGraph pipeline: compute → safety → build_prompt
            initial: AHAAState = {
                "profile": req.profile,
                "metrics": None,
                "safety": None,
                "system_prompt": "",
                "error": None,
            }
            result = ahaa_graph.invoke(initial)

            if result.get("error"):
                yield _sse({"type": "error", "message": result["error"]})
                yield _sse({"type": "done"})
                return

            # 2. Send computed data to frontend immediately
            yield _sse({"type": "metrics", "data": result["metrics"].model_dump()})
            yield _sse({"type": "safety",  "data": result["safety"].model_dump()})
            yield _sse({"type": "system_prompt", "data": result["system_prompt"]})

            # 3. Stream Ollama response token-by-token
            user_msg = (
                f"Output the full 9-section health report now for this patient. "
                f"BMI={result['metrics'].bmi.value}, target={result['metrics'].adjusted_calories} kcal/day. "
                f"Include the complete 7-day meal plan and 7-day workout plan tables. "
                f"Use exact numbers. Start with Section 1 immediately."
            )
            for token in _stream_ollama(result["system_prompt"], [{"role": "user", "content": user_msg}]):
                yield _sse({"type": "chunk", "text": token})

        except http.exceptions.ConnectionError:
            yield _sse({"type": "error", "message": "Cannot reach Ollama. Make sure it is running (ollama serve)."})
        except Exception:
            yield _sse({"type": "error", "message": traceback.format_exc(limit=3)})

        yield _sse({"type": "done"})

    return Response(
        stream_with_context(stream()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── POST /api/chat ────────────────────────────────────────────
@api_bp.route("/chat", methods=["POST"])
def chat():
    try:
        req = ChatRequest.model_validate(request.get_json(force=True) or {})
    except ValidationError as exc:
        errors = "; ".join(e["msg"] for e in exc.errors())
        return Response(
            _sse({"type": "error", "message": f"Validation: {errors}"}) + _sse({"type": "done"}),
            mimetype="text/event-stream",
        )

    def stream():
        try:
            messages = list(req.history) + [{"role": "user", "content": req.message}]
            for token in _stream_ollama(req.system_prompt, messages):
                yield _sse({"type": "chunk", "text": token})
        except http.exceptions.ConnectionError:
            yield _sse({"type": "error", "message": "Cannot reach Ollama. Make sure it is running."})
        except Exception:
            yield _sse({"type": "error", "message": traceback.format_exc(limit=3)})
        yield _sse({"type": "done"})

    return Response(
        stream_with_context(stream()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── GET /api/health ───────────────────────────────────────────
@api_bp.route("/health")
def health():
    cfg = get_settings()
    try:
        r = http.get(f"{cfg.OLLAMA_BASE_URL}/api/tags", timeout=3)
        ollama_ok = r.ok
        models = [m["name"] for m in r.json().get("models", [])]
    except Exception:
        ollama_ok = False
        models = []
    return {"status": "ok", "ollama": ollama_ok, "model": cfg.OLLAMA_MODEL, "available_models": models}
