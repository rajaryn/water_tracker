"""
Hydration Recommendation Engine v1
Implements Dietary Reference Intakes (DRI) from the Institute of Medicine (IOM / National Academies),
EFSA reference values, and WHO activity/environmental adjustment principles.
"""

from typing import Dict, Any

CALCULATION_VERSION = "v1"
RESEARCH_BASIS = "Institute of Medicine (IOM) DRI & EFSA / WHO Contextual Models"

def calculate_hydration_target(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates an estimated daily hydration target based on user profile.
    
    Expected profile keys:
    - age: int (default: 25)
    - sex: str ('male', 'female', 'prefer_not_to_say')
    - activity_level: str ('sedentary', 'lightly_active', 'moderately_active', 'highly_active')
    - environment: str ('indoors', 'mixed', 'outdoors')
    - pregnancy_status: str ('neither', 'pregnant', 'breastfeeding', 'prefer_not_to_say')
    """
    age = int(profile.get("age", 25))
    sex = str(profile.get("sex", "prefer_not_to_say")).lower()
    activity = str(profile.get("activity_level", "sedentary")).lower()
    environment = str(profile.get("environment", "indoors")).lower()
    pregnancy = str(profile.get("pregnancy_status", "neither")).lower()

    adjustments = []

    # 1. Baseline Reference Total Water Intake (IOM / EFSA standard for adults)
    # IOM: Men 3.7L/day total water, Women 2.7L/day total water.
    # ~20% of total water comes from dietary food, ~80% from beverages/drinking water.
    if sex == "male":
        baseline_total_water_ml = 3700
        baseline_fluid_ml = 2960 # 80% of 3700ml
        adjustments.append({
            "factor": "Baseline Intake (IOM Adult Male 19+)",
            "change": f"{baseline_fluid_ml} ml fluid",
            "details": "Based on IOM reference of 3.7 L total water/day (80% fluid, 20% food)"
        })
    elif sex == "female":
        baseline_total_water_ml = 2700
        baseline_fluid_ml = 2160 # 80% of 2700ml
        adjustments.append({
            "factor": "Baseline Intake (IOM Adult Female 19+)",
            "change": f"{baseline_fluid_ml} ml fluid",
            "details": "Based on IOM reference of 2.7 L total water/day (80% fluid, 20% food)"
        })
    else:
        # Mid-point reference for unspecified sex
        baseline_total_water_ml = 3200
        baseline_fluid_ml = 2560
        adjustments.append({
            "factor": "Baseline Intake (Unspecified Sex General Reference)",
            "change": f"{baseline_fluid_ml} ml fluid",
            "details": "Midpoint reference based on IOM adult guidelines (80% fluid, 20% food)"
        })

    current_fluid_ml = baseline_fluid_ml

    # 2. Pregnancy & Lactation Adjustments (IOM Guidelines)
    if sex == "female" or sex == "prefer_not_to_say":
        if pregnancy == "pregnant":
            pregnancy_add_ml = 300 # Fluid increase
            current_fluid_ml += pregnancy_add_ml
            adjustments.append({
                "factor": "Pregnancy Fluid Adjustment",
                "change": f"+{pregnancy_add_ml} ml",
                "details": "IOM recommendation for expanded blood volume & amniotic fluid (+300 ml)"
            })
        elif pregnancy == "breastfeeding":
            lactation_add_ml = 880 # Fluid increase (80% of +1.1L total water)
            current_fluid_ml += lactation_add_ml
            adjustments.append({
                "factor": "Lactation / Breastfeeding Adjustment",
                "change": f"+{lactation_add_ml} ml",
                "details": "IOM recommendation to support milk production (+1.1 L total water / 880 ml fluid)"
            })

    # 3. Activity Level Adjustments (WHO / Exercise physiology)
    activity_multipliers = {
        "sedentary": (1.0, 0, "Sitting mostly, baseline metabolism"),
        "lightly_active": (1.10, int(baseline_fluid_ml * 0.10), "Light daily movement & occasional walking (+10%)"),
        "moderately_active": (1.20, int(baseline_fluid_ml * 0.20), "Regular exercise / substantial physical movement (+20%)"),
        "highly_active": (1.35, int(baseline_fluid_ml * 0.35), "Frequent intense exercise / physically demanding work (+35%)")
    }

    mult, act_add_ml, act_desc = activity_multipliers.get(activity, activity_multipliers["sedentary"])
    if act_add_ml > 0:
        current_fluid_ml += act_add_ml
        adjustments.append({
            "factor": f"Activity Level ({activity.replace('_', ' ').title()})",
            "change": f"+{act_add_ml} ml",
            "details": act_desc
        })

    # 4. Environmental Exposure Adjustments
    env_additions = {
        "indoors": (0, "Controlled indoor climate"),
        "mixed": (150, "Occasional outdoor thermal exposure (+150 ml)"),
        "outdoors": (350, "Increased perspiration loss from outdoor environment (+350 ml)")
    }
    env_add_ml, env_desc = env_additions.get(environment, (0, "Controlled indoor climate"))
    if env_add_ml > 0:
        current_fluid_ml += env_add_ml
        adjustments.append({
            "factor": f"Environment ({environment.title()})",
            "change": f"+{env_add_ml} ml",
            "details": env_desc
        })

    # Round target to clean 50 ml increments for intuitive UX
    final_target_ml = int(round(current_fluid_ml / 50.0) * 50)

    # Estimate corresponding total water intake (fluid / 0.8)
    estimated_total_water_ml = int(round(final_target_ml / 0.8))

    return {
        "target_ml": final_target_ml,
        "target_l": round(final_target_ml / 1000.0, 2),
        "total_water_ml": estimated_total_water_ml,
        "total_water_l": round(estimated_total_water_ml / 1000.0, 2),
        "calculation_version": CALCULATION_VERSION,
        "research_basis": RESEARCH_BASIS,
        "is_estimate": True,
        "disclaimer": (
            "This is an estimated daily hydration target based on dietary reference values, "
            "not a medically prescribed requirement. Individual fluid needs vary based on health, "
            "dietary sodium, climate, and physical workload."
        ),
        "profile_snapshot": {
            "age": age,
            "sex": sex,
            "activity_level": activity,
            "environment": environment,
            "pregnancy_status": pregnancy
        },
        "adjustments_breakdown": adjustments
    }
