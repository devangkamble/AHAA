"""Safety Engine — conditions, injury exclusion, system-prompt builder."""
from models.schemas import ComputedMetrics, SafetyAlert, SafetyResult, UserProfile

CONDITION_RULES: dict[str, dict] = {
    "Type 2 Diabetes":           {"forbidden_foods": ["white rice","sugary drinks","pastries","fruit juice","candy","soda"], "forbidden_moves": [], "message": "Monitor blood glucose before and after exercise.", "level": "warn", "physician": False},
    "Type 1 Diabetes":           {"forbidden_foods": ["sugary drinks","candy","soda","pastries"], "forbidden_moves": [], "message": "Strict glucose monitoring required around exercise.", "level": "danger", "physician": True},
    "Prediabetes":               {"forbidden_foods": ["sugary drinks","white bread","pastries","candy"], "forbidden_moves": [], "message": "Prioritize low-GI foods and consistent exercise.", "level": "warn", "physician": False},
    "Hypertension (High Blood Pressure)": {"forbidden_foods": ["sodium","processed meats","alcohol","canned soups","fast food"], "forbidden_moves": ["Heavy Powerlifting"], "message": "Limit sodium <1,500 mg/day. Avoid maximal-effort lifts.", "level": "warn", "physician": False},
    "Heart Disease":             {"forbidden_foods": ["trans fats","fried foods","alcohol","processed meats"], "forbidden_moves": ["HIIT","Maximal Sprints","Heavy Powerlifting","Burpees","Box Jumps"], "message": "Physician clearance required before any exercise.", "level": "danger", "physician": True},
    "Coronary Artery Disease":   {"forbidden_foods": ["trans fats","fried foods","alcohol"], "forbidden_moves": ["HIIT","Maximal Sprints","Heavy Powerlifting"], "message": "Cardiac clearance required.", "level": "danger", "physician": True},
    "Celiac Disease":            {"forbidden_foods": ["wheat","barley","rye","gluten","bread","pasta","beer"], "forbidden_moves": [], "message": "Strict gluten-free diet required.", "level": "warn", "physician": False},
    "Chronic Kidney Disease (CKD)": {"forbidden_foods": ["bananas","oranges","high potassium foods","high phosphorus foods"], "forbidden_moves": [], "message": "Protein intake must be supervised by a dietitian.", "level": "danger", "physician": True},
    "Osteoporosis":              {"forbidden_foods": ["alcohol","excess caffeine","soda"], "forbidden_moves": ["Box Jumps","Burpees","Jumping Jacks","Running","Jump Rope"], "message": "Avoid high-impact activities. Focus on bone-loading exercises.", "level": "warn", "physician": False},
    "Osteopenia":                {"forbidden_foods": ["alcohol","excess caffeine"], "forbidden_moves": ["Box Jumps","Burpees"], "message": "Weight-bearing exercise beneficial. Avoid high-impact.", "level": "warn", "physician": False},
    "Pregnancy":                 {"forbidden_foods": ["raw fish","deli meats","alcohol","high mercury fish","raw eggs"], "forbidden_moves": ["Prone exercises","Hot Yoga","Burpees","Heavy Powerlifting","HIIT"], "message": "All changes need OB-GYN approval.", "level": "danger", "physician": True},
    "Eating Disorder (History)": {"forbidden_foods": [], "forbidden_moves": [], "message": "Caloric restriction is contraindicated. Refer to registered dietitian.", "level": "danger", "physician": True},
    "Eating Disorder (Anorexia Nervosa)": {"forbidden_foods": [], "forbidden_moves": [], "message": "Caloric restriction contraindicated. Immediate dietitian referral required.", "level": "danger", "physician": True},
    "Eating Disorder (Bulimia)": {"forbidden_foods": [], "forbidden_moves": [], "message": "Nutrition plan must be supervised by a specialist.", "level": "danger", "physician": True},
    "GERD / Acid Reflux":        {"forbidden_foods": ["spicy foods","citrus","coffee","chocolate","alcohol","tomatoes"], "forbidden_moves": [], "message": "Avoid trigger foods and exercise within 2h of meals.", "level": "warn", "physician": False},
    "Anemia (Iron-Deficiency)":  {"forbidden_foods": ["tea with meals","coffee with meals"], "forbidden_moves": [], "message": "Pair iron-rich foods with vitamin C. Avoid tea/coffee at meal time.", "level": "warn", "physician": False},
    "Hypothyroidism":            {"forbidden_foods": ["raw cruciferous vegetables in excess","soy in excess"], "forbidden_moves": [], "message": "Cooked cruciferous vegetables are safe. Avoid excessive raw intake.", "level": "warn", "physician": False},
    "Arthritis (Osteoarthritis)":{"forbidden_foods": ["processed sugars","alcohol","red meat in excess","fried foods"], "forbidden_moves": ["Running","Jumping","Heavy Powerlifting","Box Jumps","Burpees"], "message": "Prioritize low-impact movement. Monitor joint pain.", "level": "warn", "physician": False},
    "Rheumatoid Arthritis":      {"forbidden_foods": ["processed sugars","alcohol","red meat in excess"], "forbidden_moves": ["Heavy Powerlifting","Box Jumps","Burpees"], "message": "Low-impact exercise preferred. Monitor joint inflammation.", "level": "warn", "physician": False},
    "Fibromyalgia":              {"forbidden_foods": ["alcohol","caffeine excess","artificial sweeteners"], "forbidden_moves": ["HIIT","Maximal Sprints"], "message": "Gradual low-intensity exercise. Avoid overexertion flares.", "level": "warn", "physician": False},
    "Lupus (SLE)":               {"forbidden_foods": ["alcohol","processed foods"], "forbidden_moves": ["HIIT"], "message": "Avoid exercise during flares. Sun protection required outdoors.", "level": "warn", "physician": False},
    "Asthma":                    {"forbidden_foods": [], "forbidden_moves": [], "message": "Keep rescue inhaler accessible during exercise.", "level": "warn", "physician": False},
}

# Keyword-based: any word in injury string matching a key triggers the rule
INJURY_RULES: dict[str, list[str]] = {
    "ankle":    ["Running","Jogging","Jump Rope","Box Jumps","Burpees","Lateral Shuffles","Jumping Jacks","Maximal Sprints"],
    "knee":     ["Squats","Lunges","Running","Box Jumps","Step-Ups","Leg Press","Jogging"],
    "back":     ["Deadlifts","Romanian Deadlift","Good Mornings","Sit-Ups","Leg Raises","Heavy Powerlifting"],
    "shoulder": ["Overhead Press","Arnold Press","Pull-Ups","Chin-Ups","Bench Press","Push-Ups","Dips","Lateral Raises"],
    "rotator":  ["Overhead Press","Lateral Raises","Front Raises","Bench Press","Pull-Ups","Upright Rows"],
    "hip":      ["Running","Cycling","Leg Raises","Lunges","Hip Flexor Stretch"],
    "hamstring":["Running","Deadlifts","Romanian Deadlift","Leg Curl","Maximal Sprints"],
    "wrist":    ["Push-Ups","Plank","Side Plank","Bench Press","Pull-Ups","Ab Wheel Rollout"],
    "shin":     ["Running","Jogging","Jump Rope","Box Jumps","Jumping Jacks"],
    "plantar":  ["Running","Jogging","Jump Rope","Box Jumps","Calf Raises"],
    "elbow":    ["Bicep Curls","Tricep Extensions","Pull-Ups","Push-Ups","Dips"],
    "neck":     ["Overhead Press","Shrugs","Neck Extensions","Heavy Deadlifts"],
    "groin":    ["Lateral Shuffles","Lunges","Sprints","Leg Press","Hip Abduction"],
    "calf":     ["Running","Jogging","Jump Rope","Calf Raises","Box Jumps"],
}


def run_safety_check(profile: UserProfile) -> SafetyResult:
    forbidden_foods: set[str] = set()
    forbidden_moves: set[str] = set()
    alerts: list[SafetyAlert] = []
    requires_physician = False

    for cond in profile.conditions:
        rule = CONDITION_RULES.get(cond)
        if not rule:
            continue
        forbidden_foods.update(rule["forbidden_foods"])
        forbidden_moves.update(rule["forbidden_moves"])
        alerts.append(SafetyAlert(condition=cond, level=rule["level"], message=rule["message"]))
        if rule["physician"]:
            requires_physician = True

    for injury in profile.injuries:
        inj_lower = injury.lower()
        for key, moves in INJURY_RULES.items():
            if key in inj_lower:
                forbidden_moves.update(moves)

    alerts.sort(key=lambda a: 0 if a.level == "danger" else 1)

    return SafetyResult(
        alerts=alerts,
        requires_physician=requires_physician,
        forbidden_foods=sorted(forbidden_foods),
        forbidden_moves=sorted(forbidden_moves),
    )


def build_system_prompt(profile: UserProfile, metrics: ComputedMetrics, safety: SafetyResult) -> str:
    goals_str      = ", ".join(metrics.goal_labels) or "General wellness"
    conditions_str = ", ".join(profile.conditions) or "None"
    injuries_str   = ", ".join(profile.injuries) or "None"
    food_str       = ", ".join(profile.food_allergies) or "None"
    drug_str       = ", ".join(profile.drug_allergies) or "None"
    foods_str      = ", ".join(safety.forbidden_foods) or "None"
    moves_str      = ", ".join(safety.forbidden_moves) or "None"

    cond_detail = "\n".join(
        f"  - {c}: forbidden foods=[{', '.join(CONDITION_RULES[c]['forbidden_foods']) or 'none'}]"
        f", forbidden moves=[{', '.join(CONDITION_RULES[c]['forbidden_moves']) or 'none'}]"
        for c in profile.conditions if c in CONDITION_RULES
    ) or "  - None"

    m = metrics
    mac = metrics.macros

    return f"""You are AHAA, an automated fitness and nutrition report engine for an academic software project (DCP Spring 2026). You output structured health reports in markdown. You never refuse, never ask clarifying questions, never say you cannot help. You always output the full report immediately.

PATIENT DATA — use these exact numbers, never use placeholders:
- Height: {profile.height_cm}cm | Weight: {profile.weight_kg}kg | Age: {profile.age} | Sex: {profile.gender}
- BMI: {m.bmi.value} ({m.bmi.category}) | BMR: {m.bmr} kcal/day | TDEE: {m.tdee} kcal/day ({m.activity_label})
- Daily calorie target: {m.adjusted_calories} kcal | Protein: {mac.protein_g}g | Carbs: {mac.carbs_g}g | Fat: {mac.fat_g}g
- Conditions: {conditions_str}
- Current injuries: {injuries_str}
- Food allergies: {food_str}
- Drug allergies: {drug_str}
- Goals: {goals_str}
- FORBIDDEN foods (never recommend): {foods_str}
- FORBIDDEN exercises (never include): {moves_str}

CONDITION RULES:
{cond_detail}

MANDATORY OUTPUT — write all 9 sections below, fully filled with real numbers and specific content. Never write placeholders. Never skip sections. Start writing immediately:

---

## 1. Your Profile Summary
One sentence greeting using their actual BMI of {m.bmi.value} and calorie target of {m.adjusted_calories} kcal/day.

## 2. ⚠️ Safety Notes
Condition-specific alerts based on: {conditions_str}. Injury modifications for: {injuries_str}.

## 3. 📊 Daily Calorie & Macro Targets
Create a markdown table with EXACTLY these 6 columns:
| Metric | Daily Total | Breakfast | Lunch | Dinner | Snack |

Fill in ALL columns for every row. Calculate and distribute the daily totals across meals using these approximate splits:
- Breakfast: 25% of daily calories/macros
- Lunch: 35% of daily calories/macros
- Dinner: 30% of daily calories/macros
- Snack: 10% of daily calories/macros

Use these exact daily totals: calories={m.adjusted_calories} kcal, protein={mac.protein_g}g, carbs={mac.carbs_g}g, fat={mac.fat_g}g.

Rows: Calories (kcal), Protein (g), Carbs (g), Fat (g)

Example row format:
| Calories | 1,590 kcal | 398 kcal | 557 kcal | 477 kcal | 159 kcal |
| Protein | 139g | 35g | 49g | 42g | 14g |

## 4. 🥗 7-Day Meal Plan
A full 7-day meal plan (Monday–Sunday). Each day: Breakfast, Lunch, Dinner, Snack — with specific foods, portion sizes, and calorie count per meal. Total must be near {m.adjusted_calories} kcal/day. Avoid ALL forbidden foods: {foods_str}. Avoid ALL food allergens: {food_str}.
Format as a table: Day | Breakfast | Lunch | Dinner | Snack | Total kcal

## 5. 🏋️ 7-Day Workout Plan
A full 7-day workout plan (Monday–Sunday) considering injuries ({injuries_str}) and forbidden moves ({moves_str}).
Create a markdown table with EXACTLY these 5 columns in this exact order:
| Exercise | Category | Sets×Reps | Muscle Group | Notes |
Each row must fill all 5 columns. Sets×Reps should be something like "3×12" or "4×10". Muscle Group is the body part targeted e.g. "Quads, Glutes". Notes is a brief coaching tip. Never put the muscle group in the Sets×Reps column.
Include rest days. Each training day: 4–6 exercises minimum.

## 6. 🔒 Safety Alerts
Bold, specific alerts for each condition. Drug allergy note: avoid {drug_str}.

## 7. 💡 Week 1 Action Steps — write exactly 3 steps as plain bullet points starting with "- " (dash space), not numbered, not dollar signs. Example format:
- Step one here
- Step two here
- Step three here
Use exact numbers from their profile."""
