# Core simulation logic

import pandas as pd

def generate_costs(profile, care_preferences):
    age_start = profile["age"]
    age_end = 85
    base_cost = 2000
    costs = []

    dependent_ages = profile.get("dependent_ages", [])

    for year_index, user_age in enumerate(range(age_start, age_end + 1)):
        risk_multiplier = {
            "healthy": 1.0,
            "chronic": 1.5,
            "high_risk": 2.0
        }.get(profile["health_status"], 1.0)

        age_factor = 1 + 0.03 * (user_age - age_start)
        family_factor = 1 + 0.5 * profile["num_dependents"] if profile["family_status"] == "family" else 1

        cost = base_cost * risk_multiplier * age_factor * family_factor

        care_costs = 0
        if care_preferences.get("include_primary"):
            care_costs += 500
        if care_preferences.get("include_surgical"):
            care_costs += 1500
        if care_preferences.get("include_cancer"):
            care_costs += 2000
        if care_preferences.get("include_pediatric"):
            care_costs += 1000 if profile["family_status"] == "family" else 0
        if care_preferences.get("include_maternity"):
            care_costs += 1200 if profile["family_status"] == "family" else 0

        total_cost = cost + care_costs
        costs.append({
            "Age": user_age,
            "Healthcare Cost": total_cost
        })

    return pd.DataFrame(costs)


def simulate_investment_strategy(cost_df: pd.DataFrame, investment_rate: float, contribution, savings_start=0) -> pd.DataFrame:
    investment_value = savings_start
    investment_growth = []
    for i, row in cost_df.iterrows():
        annual_contribution = contribution[i] if isinstance(contribution, list) else contribution
        investment_value = (investment_value + annual_contribution) * (1 + investment_rate)
        investment_growth.append(investment_value)
    cost_df["investment_value"] = investment_growth
    cost_df["Capital - Total"] = cost_df.get("Capital - Short", 0) + cost_df.get("Capital - Mid", 0) + cost_df.get("Capital - Long", 0)
    return cost_df
