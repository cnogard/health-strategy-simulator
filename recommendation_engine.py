# AI recommendation logic

import streamlit as st
def generate_recommendation(profile, cost_df, surplus, insurance_type, capital_strategy):
    from projected_health_risk import get_risk_insight

    print("RISK INSIGHT:", get_risk_insight())

    age = profile.get("age")
    health_status = profile.get("health_status")
    partner_health = profile.get("partner_health_status")
    family = profile.get("family_status") == "family"

    total_shortfall = sum([x for x in surplus if x < 0])

    if "Capital - Total" in cost_df.columns and "Cumulative Cost" in cost_df.columns:
        capital_coverage_ratio = cost_df["Capital - Total"].iloc[-1] / cost_df["Cumulative Cost"].iloc[-1]
    else:
        capital_coverage_ratio = 0

    recs = []

    if insurance_type != "None":
        if health_status == "healthy" and age < 40 and capital_coverage_ratio > 0.8:
            recs.append("📉 You may not need full insurance coverage. Consider a catastrophic-only plan or ACA Bronze plan with capital-based savings.")
        elif health_status == "high_risk" or partner_health == "high_risk":
            recs.append("🛡️ High-risk detected. Retaining comprehensive insurance or supplementing with surgical and chronic bundles is advised.")
    else:
        recs.append("⚠️ No insurance detected. Make sure capital + care bundles are sufficient for expected needs.")

    if age < 40 and health_status == "healthy":
        recs.append("💡 Digital-first care (e.g., Mira, telehealth) and primary care subscriptions could reduce costs while maintaining access.")
    if family:
        recs.append("👨‍👩‍👧 Pediatric and family bundles should be considered for dependents or partner care planning.")
    if age > 50 and "include_surgical" in profile:
        recs.append("🛠️ Surgical bundles can reduce costs for procedures common in older age brackets.")

    if capital_coverage_ratio < 0.75:
        recs.append("📊 Consider increasing long-term capital allocation or raising your savings contributions.")
    elif capital_coverage_ratio > 1.2:
        recs.append("✅ Your capital strategy exceeds projected healthcare needs. You may be able to optimize for other life goals.")

    if "Healthcare Cost" in cost_df.columns and max(cost_df["Healthcare Cost"]) > 20000:
        recs.append("🚨 One or more years project catastrophic costs. Consider catastrophic insurance or HSA-backed savings.")

    print("RISK TRAJECTORY:", st.session_state.get("risk_trajectory"))
    print("MAX RISK:", st.session_state.get("max_risk"))

    # Add projected risk insight if available
    risk_insight = get_risk_insight()
    if risk_insight:
        recs.append("📉 " + risk_insight)

    return recs
