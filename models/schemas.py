from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field, model_validator


# ── Request / Input ───────────────────────────────────────────
class UserProfile(BaseModel):
    height_cm: float = Field(..., ge=100, le=250)
    weight_kg: float = Field(..., ge=30, le=300)
    age: int = Field(..., ge=10, le=110)
    gender: Literal["Male", "Female", "Other"]
    activity_level: int = Field(..., ge=0, le=4)
    goals: list[str] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)
    injuries: list[str] = Field(default_factory=list)
    food_allergies: list[str] = Field(default_factory=list)
    drug_allergies: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def goals_required(self) -> UserProfile:
        if not self.goals:
            raise ValueError("Select at least one health goal.")
        return self


class GenerateRequest(BaseModel):
    profile: UserProfile


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    history: list[dict] = Field(default_factory=list)
    system_prompt: str


# ── Computed / Output ─────────────────────────────────────────
class MacroTargets(BaseModel):
    protein_g: int
    carbs_g: int
    fat_g: int
    protein_pct: int
    carbs_pct: int
    fat_pct: int


class BMIResult(BaseModel):
    value: float
    category: str
    color: Literal["green", "amber", "red"]


class ComputedMetrics(BaseModel):
    bmi: BMIResult
    bmr: int
    tdee: int
    adjusted_calories: int
    activity_label: str
    goal_labels: list[str]
    macros: MacroTargets


class SafetyAlert(BaseModel):
    condition: str
    level: Literal["warn", "danger"]
    message: str


class SafetyResult(BaseModel):
    alerts: list[SafetyAlert]
    requires_physician: bool
    forbidden_foods: list[str]
    forbidden_moves: list[str]


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
