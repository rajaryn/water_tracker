/**
 * Client-Side Hydration Recommendation Engine v1
 * Matches Institute of Medicine (IOM), EFSA, and WHO scientific reference models.
 */

export const CALCULATION_VERSION = "v1";
export const RESEARCH_BASIS = "Institute of Medicine (IOM) DRI & EFSA / WHO Contextual Models";

export function calculateHydrationTarget(profile = {}) {
  const age = parseInt(profile.age || 25, 10);
  const sex = String(profile.sex || 'prefer_not_to_say').toLowerCase();
  const activity = String(profile.activity_level || 'sedentary').toLowerCase();
  const environment = String(profile.environment || 'indoors').toLowerCase();
  const pregnancy = String(profile.pregnancy_status || 'neither').toLowerCase();

  const adjustments = [];
  let baselineTotalWaterMl = 3200;
  let baselineFluidMl = 2560;

  if (sex === 'male') {
    baselineTotalWaterMl = 3700;
    baselineFluidMl = 2960;
    adjustments.push({
      factor: 'Baseline Intake (IOM Adult Male 19+)',
      change: `${baselineFluidMl} ml fluid`,
      details: 'Based on IOM reference of 3.7 L total water/day (80% fluid, 20% food)'
    });
  } else if (sex === 'female') {
    baselineTotalWaterMl = 2700;
    baselineFluidMl = 2160;
    adjustments.push({
      factor: 'Baseline Intake (IOM Adult Female 19+)',
      change: `${baselineFluidMl} ml fluid`,
      details: 'Based on IOM reference of 2.7 L total water/day (80% fluid, 20% food)'
    });
  } else {
    baselineTotalWaterMl = 3200;
    baselineFluidMl = 2560;
    adjustments.push({
      factor: 'Baseline Intake (Unspecified Sex General Reference)',
      change: `${baselineFluidMl} ml fluid`,
      details: 'Midpoint reference based on IOM adult guidelines (80% fluid, 20% food)'
    });
  }

  let currentFluidMl = baselineFluidMl;

  // Pregnancy / Lactation
  if (sex === 'female' || sex === 'prefer_not_to_say') {
    if (pregnancy === 'pregnant') {
      currentFluidMl += 300;
      adjustments.push({
        factor: 'Pregnancy Fluid Adjustment',
        change: '+300 ml',
        details: 'IOM recommendation for expanded blood volume & amniotic fluid (+300 ml)'
      });
    } else if (pregnancy === 'breastfeeding') {
      currentFluidMl += 880;
      adjustments.push({
        factor: 'Lactation / Breastfeeding Adjustment',
        change: '+880 ml',
        details: 'IOM recommendation to support milk production (+1.1 L total water / 880 ml fluid)'
      });
    }
  }

  // Activity
  const activityMap = {
    sedentary: [0, 'Sitting mostly, baseline metabolism'],
    lightly_active: [Math.round(baselineFluidMl * 0.10), 'Light daily movement & walking (+10%)'],
    moderately_active: [Math.round(baselineFluidMl * 0.20), 'Regular exercise / physical movement (+20%)'],
    highly_active: [Math.round(baselineFluidMl * 0.35), 'Frequent intense exercise / physical work (+35%)']
  };
  const [actAddMl, actDesc] = activityMap[activity] || activityMap.sedentary;
  if (actAddMl > 0) {
    currentFluidMl += actAddMl;
    adjustments.push({
      factor: `Activity Level (${activity.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())})`,
      change: `+${actAddMl} ml`,
      details: actDesc
    });
  }

  // Environment
  const envMap = {
    indoors: [0, 'Controlled indoor climate'],
    mixed: [150, 'Occasional outdoor thermal exposure (+150 ml)'],
    outdoors: [350, 'Increased perspiration loss from outdoor exposure (+350 ml)']
  };
  const [envAddMl, envDesc] = envMap[environment] || envMap.indoors;
  if (envAddMl > 0) {
    currentFluidMl += envAddMl;
    adjustments.push({
      factor: `Environment (${environment.charAt(0).toUpperCase() + environment.slice(1)})`,
      change: `+${envAddMl} ml`,
      details: envDesc
    });
  }

  const finalTargetMl = Math.round(currentFluidMl / 50) * 50;
  const estimatedTotalWaterMl = Math.round(finalTargetMl / 0.8);

  return {
    target_ml: finalTargetMl,
    target_l: (finalTargetMl / 1000).toFixed(2),
    total_water_ml: estimatedTotalWaterMl,
    total_water_l: (estimatedTotalWaterMl / 1000).toFixed(2),
    calculation_version: CALCULATION_VERSION,
    research_basis: RESEARCH_BASIS,
    is_estimate: true,
    disclaimer: 'This is an estimated daily hydration target based on dietary reference values, not a medically prescribed requirement. Individual fluid needs vary based on health, diet, activity, and climate.',
    profile_snapshot: {
      age,
      sex,
      activity_level: activity,
      environment,
      pregnancy_status: pregnancy
    },
    adjustments_breakdown: adjustments
  };
}
