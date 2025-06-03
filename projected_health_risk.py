# Risk trajectory logic

import pandas as pd

# Function to simulate projected health risk
def projected_risk(age, health_status):
    base_risk = {
        "healthy": 0.2,
        "chronic": 0.5,
        "high_risk": 0.8
    }.get(health_status, 0.2)

    risk_by_year = []
    for i in range(0, 86 - age):  # simulate up to age 85
        aging_factor = 0.02 * i  # 2% risk increase per year
        total_risk = min(base_risk + aging_factor, 1.0)
        risk_by_year.append(total_risk)
    return risk_by_year

# Function to retrieve projected risk insight based on risk profile
def get_risk_insight(age=None, health_status=None):
    if age is None or health_status is None:
        return None

    risk_trajectory = projected_risk(age, health_status)
    risks = risk_trajectory
    max_risk = max(risks)
    rising_fast = risks[10] - risks[0] > 0.25

    if max_risk > 0.9:
        return "🚨 Your health risk is projected to reach critical levels. Consider both capital care and catastrophic insurance early."
    elif rising_fast:
        return "📊 Your risk profile is rising rapidly. A capital health investment strategy can reduce future financial strain."
    else:
        return "✅ Your risk progression is steady. Early investment may still yield high coverage and long-term flexibility."

# Optional: expose a utility to get both risk values and trajectory
def get_risk_trajectory(age, health_status):
    return projected_risk(age, health_status)s
