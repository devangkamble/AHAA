"""Computation Engine — Mifflin-St Jeor BMR, TDEE, BMI, macros."""
from models.schemas import (
    BMIResult, ComputedMetrics, MacroTargets, UserProfile
)

ACTIVITY_LEVELS = [
    {"label": "Sedentary",         "mult": 1.20,  "desc": "Little or no exercise"},
    {"label": "Lightly Active",    "mult": 1.375, "desc": "Light exercise 1–3 days/week"},
    {"label": "Moderately Active", "mult": 1.55,  "desc": "Moderate exercise 3–5 days/week"},
    {"label": "Very Active",       "mult": 1.725, "desc": "Hard exercise 6–7 days/week"},
    {"label": "Extra Active",      "mult": 1.90,  "desc": "Very hard exercise + physical job"},
]

HEALTH_GOALS = [
    {"id": "loss",     "label": "Weight Loss",     "icon": "↓", "delta": -500},
    {"id": "maintain", "label": "Maintenance",     "icon": "=", "delta":    0},
    {"id": "muscle",   "label": "Muscle Building", "icon": "↑", "delta":  300},
    {"id": "cardio",   "label": "Cardiovascular",  "icon": "♥", "delta":    0},
    {"id": "rehab",    "label": "Injury Recovery", "icon": "✦", "delta":    0},
    {"id": "flex",     "label": "Flexibility",     "icon": "∿", "delta":    0},
]


def _bmr(profile: UserProfile) -> float:
    h, w, a = profile.height_cm, profile.weight_kg, profile.age
    base = 10 * w + 6.25 * h - 5 * a
    if profile.gender == "Male":
        return base + 5
    if profile.gender == "Female":
        return base - 161
    return base - 78  # Other: midpoint


def _bmi(profile: UserProfile) -> BMIResult:
    hm = profile.height_cm / 100
    val = round(profile.weight_kg / (hm * hm), 1)
    if val < 18.5:
        cat, color = "Underweight", "amber"
    elif val < 25:
        cat, color = "Normal Weight", "green"
    elif val < 30:
        cat, color = "Overweight", "amber"
    else:
        cat, color = "Obese", "red"
    return BMIResult(value=val, category=cat, color=color)


def _macros(calories: int, goals: list[str]) -> MacroTargets:
    if "muscle" in goals:
        p, c, f = 0.30, 0.45, 0.25
    elif "loss" in goals:
        p, c, f = 0.35, 0.35, 0.30
    elif "cardio" in goals:
        p, c, f = 0.20, 0.55, 0.25
    else:
        p, c, f = 0.25, 0.45, 0.30

    return MacroTargets(
        protein_g=round(calories * p / 4),
        carbs_g=round(calories * c / 4),
        fat_g=round(calories * f / 9),
        protein_pct=round(p * 100),
        carbs_pct=round(c * 100),
        fat_pct=round(f * 100),
    )


def compute_metrics(profile: UserProfile) -> ComputedMetrics:
    bmr = round(_bmr(profile))
    activity = ACTIVITY_LEVELS[profile.activity_level]
    tdee = round(bmr * activity["mult"])

    delta = sum(
        g["delta"] for g in HEALTH_GOALS if g["id"] in profile.goals
    )
    adjusted_calories = max(1200, tdee + delta)

    goal_labels = [
        g["label"] for g in HEALTH_GOALS if g["id"] in profile.goals
    ]

    return ComputedMetrics(
        bmi=_bmi(profile),
        bmr=bmr,
        tdee=tdee,
        adjusted_calories=adjusted_calories,
        activity_label=activity["label"],
        goal_labels=goal_labels,
        macros=_macros(adjusted_calories, profile.goals),
    )
