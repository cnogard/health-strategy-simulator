# Main Streamlit App

import streamlit as st
st.set_page_config(page_title="Health Strategy Simulator", layout="wide")

import pandas as pd
from simulator_core import generate_costs, simulate_investment_strategy
from recommendation_engine import generate_recommendation
from projected_health_risk import get_risk_insight

st.title("🗭 Health Strategy Simulator")

# Access control
with st.sidebar:
    st.header("🔐 Beta Access")
    code = st.text_input("Enter beta access code:", type="password")
    if code != "HSS_Beta_2025v1!":
        st.stop()

# Step 1 – Insurance and Profile
st.header("Step 1: Profile & Insurance")

age = st.number_input("Age", 18, 85, 30)
gender = st.selectbox("Gender", ["male", "female"])
health_status = st.selectbox("Health Status", ["healthy", "chronic", "high_risk"])
family_status = st.selectbox("Family Status", ["single", "family"])
dependents = st.number_input("Number of Dependents", 0, 10, 0)

dependent_ages = [st.number_input(f"Dependent #{i+1} Age", 0, 25, 5, key=f"dep_{i}") for i in range(dependents)]

partner_age = None
partner_health_status = None
if family_status == "family":
    partner_age = st.number_input("Partner Age", 18, 85, 30)
    partner_health_status = st.selectbox("Partner Health Status", ["healthy", "chronic", "high_risk"])

insurance_type = st.radio("Insurance Type", ["Employer-based", "Marketplace / Self-insured", "None"])

# Allow user to input or use national average premiums
st.subheader("📄 Insurance Premium Setup")
use_avg_premium = st.radio("Do you want to use national average premiums?", ["Yes", "No"], index=0)

if use_avg_premium == "Yes":
    if insurance_type == "Employer-based":
        employee_premium = 2000
        employer_premium = 6000
    elif insurance_type == "Marketplace / Self-insured":
        employee_premium = 6550
        employer_premium = 0
    else:
        employee_premium = 0
        employer_premium = 0
else:
    employee_premium = st.number_input("Employee Contribution ($/yr)", min_value=0, value=2000)
    employer_premium = st.number_input("Employer Contribution ($/yr)", min_value=0, value=6000 if insurance_type == "Employer-based" else 0)

# Allow user to input or use national average out-of-pocket costs
st.subheader("💸 Out-of-Pocket Cost Setup")
use_avg_oop = st.radio("Do you want to use national average out-of-pocket (OOP) costs?", ["Yes", "No"], index=0)

if use_avg_oop == "Yes":
    if insurance_type == "Employer-based":
        oop_pct = 0.15
    elif insurance_type == "Marketplace / Self-insured":
        oop_pct = 0.25
    else:
        oop_pct = 1.0
else:
    oop_pct = st.slider("Custom OOP % of Healthcare Cost", 0, 100, 25) / 100

# Premium inflation rate (moved from Step 2)
st.subheader("📈 Inflation Assumption")
premium_inflation = st.slider("Annual Premium Growth (%)", 0, 10, 5, help="Applies to premiums and OOP") / 100

# Restore care preferences if missing
st.subheader("Care Preferences")
with st.expander("🏥 Select Your Care Preferences", expanded=True):
    col1, col2 = st.columns(2)
    include_primary = col1.checkbox("Primary Care", value=True)
    include_chronic = col2.checkbox("Chronic Care", value=True)
    include_preventive = col1.checkbox("Preventive Care", value=True)
    include_surgical = col2.checkbox("Surgical Care", value=True)
    include_cancer = col1.checkbox("Cancer Care", value=True)
    include_mental = col2.checkbox("Mental Health", value=True)
    include_emergency = col1.checkbox("Emergency Care", value=True)
    include_eol = col2.checkbox("End-of-Life Care", value=True)
    include_maternity = col1.checkbox("Maternity Care", value=True)
    include_pediatric = col2.checkbox("Pediatric Care", value=True)

    care_prefs = {
        "include_primary": include_primary,
        "include_chronic": include_chronic,
        "include_preventive": include_preventive,
        "include_surgical": include_surgical,
        "include_cancer": include_cancer,
        "include_mental": include_mental,
        "include_emergency": include_emergency,
        "include_eol": include_eol,
        "include_maternity": include_maternity,
        "include_pediatric": include_pediatric
    }
    st.session_state.care_prefs = care_prefs

if st.button("Run Step 1"):
    st.session_state.step1_submitted = True
    st.session_state.step2_submitted = False
    st.session_state.step3_submitted = False
    st.session_state.step4_submitted = False

    profile = {
        "age": age,
        "gender": gender,
        "health_status": health_status,
        "family_status": family_status,
        "num_dependents": dependents,
        "dependent_ages": dependent_ages,
        "partner_age": partner_age,
        "partner_health_status": partner_health_status
    }

    care_prefs = st.session_state.get("care_prefs", {})

    cost_df = generate_costs(profile, care_prefs)
    total_premium = employee_premium + employer_premium
    premiums = [total_premium * ((1 + premium_inflation) ** i) for i in range(len(cost_df))]
    cost_df["Premiums"] = premiums
    cost_df["OOP Cost"] = cost_df["Healthcare Cost"] * oop_pct
    cost_df["Healthcare Cost"] = cost_df["OOP Cost"] + cost_df["Premiums"]

    st.session_state.cost_df = cost_df
    st.session_state.profile = profile
    st.session_state.insurance_type = insurance_type
    st.session_state.employee_premium = employee_premium
    st.session_state.employer_premium = employer_premium
    st.session_state.oop_pct = oop_pct
    st.session_state.premium_inflation = premium_inflation


    # Display first-year cost breakdown for context
    first_year = 0
    st.markdown("### 📊 Year 1 Cost Breakdown:")
    st.markdown(f"- **Base Premiums**: ${employee_premium + employer_premium:,.0f}")
    st.markdown(f"- **Out-of-Pocket Share**: {oop_pct * 100:.1f}% of medical costs")
    st.markdown(f"- **Total Year 1 Cost (estimated)**: ${cost_df['Healthcare Cost'].iloc[first_year]:,.0f}")

    # Line chart for immediate feedback
    st.line_chart(cost_df.set_index("Age")["Healthcare Cost"])
    st.success("Step 1 complete.")

    # Projected health risk
    from projected_health_risk import get_risk_trajectory
    st.session_state["risk_trajectory"] = get_risk_trajectory(age, health_status)


# --- Step 2: Financial Capacity ---
if "cost_df" in st.session_state and not st.session_state.get("step2_submitted"):

    st.header("Step 2: Financial Capacity")

    cost_df = st.session_state.cost_df
    insurance_type = st.session_state.insurance_type
    profile = st.session_state.profile
    oop_first_year = round(cost_df["OOP Cost"].iloc[0], 2)
    premium_first_year = round(cost_df["Premiums"].iloc[0], 2)
    net_income_monthly = 0

    with st.form("finance_form"):
        st.markdown("### 💵 Income & Tax Estimation")
        monthly_income = st.number_input("Monthly Gross Income ($)", 0, value=5000)
        est_tax_rate = st.slider("Estimated Tax Rate (%)", 0.0, 50.0, 25.0) / 100
        net_income_monthly = monthly_income * (1 - est_tax_rate)
        net_income_annual = net_income_monthly * 12
        income_growth = st.slider("Income Growth (%)", 0.0, 10.0, 2.0) / 100

        # Free cash reminder
        if insurance_type == "Marketplace / Self-insured":
            available_cash = net_income_monthly - (premium_first_year / 12) - (oop_first_year / 12)
        else:
            available_cash = net_income_monthly - (oop_first_year / 12)

        st.markdown(f"💬 **Available Monthly Cash for Expenses:** ${available_cash:,.0f} "
                    f"(after estimated premiums and OOP in year 1)")

        st.markdown("### 🧾 Monthly Fixed Commitments")
        monthly_expenses = st.number_input("Monthly Household Expenses ($)", 0, value=2500,
                                           help="Should not exceed available cash above.")
        debt_monthly_payment = st.number_input("Monthly Debt Payment ($)", 0, value=500)

        st.markdown("### 💾 Savings Profile")
        savings_start = st.number_input("Current Savings Balance ($)", 0, value=10000)
        savings_growth = st.slider("Expected Savings Growth (%)", 0.0, 10.0, 3.0) / 100
        annual_contrib = st.number_input("Annual Savings Contribution ($)", 0, value=3000)
        savings_goals = st.multiselect(
            "What is your savings primarily for?",
            ["Home", "Education", "Vacations", "Retirement", "Health", "Rainy Day"],
            default=["Retirement", "Health"]
        )

        st.markdown("### 🏦 401(k) Contributions")
        contrib_401k_employee = st.number_input("Annual Employee 401(k) Contribution ($)", min_value=0, value=4000)
        contrib_401k_employer = st.number_input("Annual Employer 401(k) Match ($)", min_value=0, value=2000)
        growth_401k = st.slider("401(k) Growth Rate (%)", 0.0, 10.0, 5.0) / 100

        submit2 = st.form_submit_button("Run Step 2")

    if submit2:
        years = len(cost_df)
        income_proj = [net_income_annual * ((1 + income_growth) ** i) for i in range(years)]

        savings_proj = []
        current = savings_start
        for i in range(years):
            current *= (1 + savings_growth)
            current += annual_contrib
            savings_proj.append(current)

        # 401(k) simulation
        proj_401k = []
        value_401k = 0
        for i in range(years):
            value_401k *= (1 + growth_401k)
            value_401k += contrib_401k_employee + contrib_401k_employer
            proj_401k.append(value_401k)

        st.session_state.monthly_income = monthly_income
        st.session_state.net_income_annual = net_income_annual
        st.session_state.income_growth = income_growth
        st.session_state.monthly_expenses = monthly_expenses
        st.session_state.debt_monthly_payment = debt_monthly_payment
        st.session_state.savings_start = savings_start
        st.session_state.savings_growth = savings_growth
        st.session_state.annual_contrib = annual_contrib
        st.session_state.savings_goals = savings_goals
        st.session_state.contrib_401k_employee = contrib_401k_employee
        st.session_state.contrib_401k_employer = contrib_401k_employer
        st.session_state.growth_401k = growth_401k
        st.session_state.income_proj = income_proj
        st.session_state.savings_proj = savings_proj
        st.session_state.proj_401k = proj_401k
        st.session_state.step2_submitted = True


# Step 3 – Expense vs Income Summary
if st.session_state.get("step2_submitted") and not st.session_state.get("step3_submitted"):
    st.header("Step 3: Expense vs. Income Overview")

    cost_df = st.session_state.cost_df
    income_proj = st.session_state.income_proj
    savings_proj = st.session_state.savings_proj
    proj_401k = st.session_state.proj_401k
    monthly_expenses = st.session_state.monthly_expenses
    debt_monthly_payment = st.session_state.debt_monthly_payment
    income_growth = st.session_state.income_growth

    years = len(cost_df)

    # Inflation-adjusted expenses
    household = [monthly_expenses * 12 * ((1 + income_growth) ** i) for i in range(years)]
    debt = [debt_monthly_payment * 12 * ((1 + income_growth) ** i) for i in range(years)]
    premiums = cost_df["Premiums"].tolist()
    oop = cost_df["OOP Cost"].tolist()
    healthcare = [premiums[i] + oop[i] for i in range(years)]

    total_exp = [household[i] + debt[i] + healthcare[i] for i in range(years)]
    total_income = [income_proj[i] + savings_proj[i] for i in range(years)]

    surplus = [total_income[i] - total_exp[i] for i in range(years)]

    # Save to session
    st.session_state.surplus = surplus

    df_compare = pd.DataFrame({
        "Age": cost_df["Age"],
        "Household Expenses": household,
        "Debt Payments": debt,
        "Premiums": premiums,
        "OOP": oop,
        "Total Healthcare": healthcare,
        "Total Expenses": total_exp,
        "Income + Savings": total_income,
        "Surplus/Deficit": surplus
    })

    st.session_state.step3_submitted = True
    st.session_state.expense_df = df_compare

    st.write("### 📊 Financial Overview by Age")
    st.dataframe(df_compare.set_index("Age"))



    # Charts Section in Step 3

    st.write("### 📈 Surplus/Deficit vs. Income and Total Expenses")
    chart_data = df_compare.set_index("Age")[["Surplus/Deficit", "Total Expenses", "Income + Savings"]]
    st.line_chart(chart_data)

    st.write("### 🏥 Healthcare vs. Total Expenses")
    chart_health = df_compare.set_index("Age")[["Total Healthcare", "Total Expenses"]]
    st.line_chart(chart_health)

# Step 4 – Capital Care Investment & Recommendations
if st.session_state.get("step3_submitted") and not st.session_state.get("step4_submitted"):
    st.header("Step 4: Capital Health Investment & Strategy")

    surplus = st.session_state.surplus
    cost_df = st.session_state.cost_df
    profile = st.session_state.profile

    st.markdown("### 📊 Surplus vs. Cost Analysis")
    chart_df = pd.DataFrame({
        "Age": cost_df["Age"],
        "Surplus": surplus,
        "Healthcare Cost": cost_df["Healthcare Cost"]
    }).set_index("Age")

    st.line_chart(chart_df)

    st.markdown("### 🧠 Align Financial Goals with Healthcare Needs")
    capital_invest_toggle = st.radio(
        "You should align your financial goals to your healthcare needs. Do you want to evaluate how a dedicated Capital Care Investment strategy can help you meet your short, mid, and long-term objectives?",
        ["No", "Yes"]
    )

    allocate_from_savings = 0
    new_fund_contribution = 0

    if capital_invest_toggle == "Yes":
        st.markdown("#### 💰 Capital Fund Source")
        fund_source = st.radio("Would you like to allocate funds from savings or income?",
                               ["From Existing Savings", "From Monthly Income"])

        # Initialize default values
        allocate_from_savings = 0
        new_fund_contribution = 0

        if fund_source == "From Existing Savings":
            allocate_from_savings = st.slider("% of Current Savings to Allocate", 0, 100, 20)
        else:
            new_fund_contribution = st.number_input("Monthly Contribution to Capital Health Fund ($)", min_value=0,
                                                    value=200)

            # Free cash check
            net_income_monthly = st.session_state.net_income_annual / 12
            monthly_expenses = st.session_state.monthly_expenses
            debt_payment = st.session_state.debt_monthly_payment
            monthly_oop = cost_df["OOP Cost"].iloc[0] / 12

            free_cash = net_income_monthly - monthly_expenses - debt_payment - monthly_oop
            st.markdown(f"💡 Estimated Free Cash: **${free_cash:,.0f}/month**")
            if new_fund_contribution > free_cash:
                st.warning(
                    "⚠️ Your planned capital fund contribution exceeds your estimated available monthly cash. Please review your inputs.")

        st.session_state.capital_fund_source = fund_source
        st.session_state.capital_from_savings_pct = allocate_from_savings
        st.session_state.capital_monthly_contrib = new_fund_contribution

        st.markdown("#### 💼 Capital Investment Allocation")
        short_term = st.slider("% Short-Term Investment", 0, 100, 10)
        mid_term = st.slider("% Mid-Term Investment", 0, 100 - short_term, 20)
        long_term = 100 - short_term - mid_term
        st.markdown(f"📈 Long-Term Investment automatically set to: **{long_term}%**")

        cap_alloc = {
            "short": short_term / 100,
            "mid": mid_term / 100,
            "long": long_term / 100
        }
        st.session_state.cap_alloc = cap_alloc

    submit4 = st.button("Generate AI Recommendations")
    if submit4:
        from recommendation_engine import generate_recommendation
        from projected_health_risk import get_risk_insight

        st.session_state.step4_submitted = True

        surplus = st.session_state.surplus
        final_df = st.session_state.cost_df
        recs = generate_recommendation(
            profile=profile,
            cost_df=final_df,
            surplus=surplus,
            insurance_type=st.session_state.insurance_type,
            capital_strategy=st.session_state.cap_alloc if capital_invest_toggle == "Yes" else {}
        )

        # Append risk-based insight
        risk_insight = get_risk_insight(profile["age"], profile["health_status"])
        if risk_insight:
            recs.append("🧠 " + risk_insight)

        st.subheader("🧭 Personalized Recommendations")
        for rec in recs:
            st.markdown(f"- {rec}")

        trajectory = st.session_state["risk_trajectory"]

        # ✅ Show Risk Chart here
        import matplotlib.pyplot as plt

        if "risk_trajectory" in st.session_state:
            st.markdown("### 📉 Projected Health Risk Over Time")

            trajectory = st.session_state["risk_trajectory"]
            num_years = len(trajectory)

            age_values = cost_df["Age"].iloc[:num_years].astype(int).tolist()
            risk_values = pd.Series(trajectory).astype(float).tolist()

            # Identify the critical age where risk hits or exceeds 0.9
            try:
                critical_index = next(i for i, val in enumerate(risk_values) if val >= 0.9)
                critical_age = age_values[critical_index]
            except StopIteration:
                critical_index = None
                critical_age = None

            # Plotting
            fig, ax = plt.subplots(figsize=(10, 4))

            ax.plot(age_values, risk_values, color='black', linewidth=2, label="Risk Score")

            # Color fill for risk zones
            ax.fill_between(age_values, risk_values, 0, where=[r < 0.5 for r in risk_values], color='green', alpha=0.2,
                            label="Low Risk")
            ax.fill_between(age_values, risk_values, 0, where=[0.5 <= r < 0.9 for r in risk_values], color='orange',
                            alpha=0.2, label="Moderate Risk")
            ax.fill_between(age_values, risk_values, 0, where=[r >= 0.9 for r in risk_values], color='red', alpha=0.2,
                            label="High Risk")

            if critical_age is not None:
                ax.axvline(x=critical_age, color='red', linestyle='--', linewidth=2,
                           label=f"Critical Age: {critical_age}")
                ax.text(critical_age + 0.5, 0.92, f"⚠️ Age {critical_age}", color='red', fontsize=10)

            ax.set_xlabel("Age")
            ax.set_ylabel("Risk Level")
            ax.set_ylim([0, 1.05])
            ax.set_title("Projected Health Risk Trajectory")
            ax.legend(loc="upper left")

            st.pyplot(fig)

# Reset logic if Step 1 changes
if st.session_state.get("step1_changed"):
    st.session_state.step2_submitted = False
    st.session_state.step3_submitted = False
    st.session_state.step4_submitted = False

