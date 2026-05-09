"""LangGraph node functions — each returns an updated state slice."""
import traceback
from agents.state import AHAAState
from engines.computation import compute_metrics
from engines.safety import build_system_prompt, run_safety_check


def compute_metrics_node(state: AHAAState) -> dict:
    if state.get("error"):
        return {}
    try:
        metrics = compute_metrics(state["profile"])
        return {"metrics": metrics}
    except Exception as exc:
        return {"error": f"Computation failed: {exc}"}


def safety_check_node(state: AHAAState) -> dict:
    if state.get("error"):
        return {}
    try:
        safety = run_safety_check(state["profile"])
        return {"safety": safety}
    except Exception as exc:
        return {"error": f"Safety check failed: {exc}"}


def build_prompt_node(state: AHAAState) -> dict:
    if state.get("error"):
        return {}
    try:
        prompt = build_system_prompt(
            state["profile"], state["metrics"], state["safety"]
        )
        return {"system_prompt": prompt}
    except Exception as exc:
        return {"error": f"Prompt build failed: {exc}"}
