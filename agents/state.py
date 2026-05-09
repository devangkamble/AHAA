from typing import TypedDict
from models.schemas import ComputedMetrics, SafetyResult, UserProfile


class AHAAState(TypedDict):
    profile: UserProfile
    metrics: ComputedMetrics | None
    safety: SafetyResult | None
    system_prompt: str
    error: str | None
