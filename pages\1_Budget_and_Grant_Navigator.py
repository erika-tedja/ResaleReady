"""
USE CASE 1 — Budget & Grant Navigator

Pipeline:
  Stage 1  Form input (non-PII)
  Stage 2  Deterministic grant rules engine
  Stage 3  TOOL CALL: live transactions from data.gov.sg
  Stage 4  Deterministic affordability + cost engine
  Stage 5  LLM CALL A -> structured JSON assessment
  Stage 6  LLM CALL B -> plain-English briefing, conditioned on Stage 5 output

Stages 5 and 6 are a genuine chain: call B receives call A's JSON as input and
cannot run without it.
"""

import json

import pandas as pd
import streamlit as st

from core import (
    FLAT_TYPES,
    POLICY_SOURCES,
    Profile,
    TOWNS,
    complete,
    complete_json,
    disclaimer,
    full_assessment,
    llm_available,
    market_snapshot,
    monthly_median_series,
    output_is_safe,
    require_auth,
    sidebar_note,
)


st.set_page_config(page_title="Budget & Grant Navigator", page_icon="💰",
                   layout="wide")
require_auth()
sidebar_note()

st.title("💰 Budget & Grant Navigator")
disclaimer()

# --------------------------------------------------------------------------
# STAGE 1 — input form
# --------------------------------------------------------------------------

st.markdown("#### Tell us about your situation")
st.caption("None of this is personally identifiable, and nothing is stored "
           "after you close the browser tab.")

with st.form("profile"):
    c1, c2, c3 = st.columns(3)

    with c1:
        household = st.radio("Buying as", ["A couple or family", "A single"],
                             horizontal=False)
        citizenship = st.selectbox(
            "Citizenship of applicants",
            ["Both Singapore Citizens", "One SC, one Singapore PR",
             "Single Singapore Citizen"])
        first_timer = st.checkbox("First-timer applicant (no previous housing "
                                  "subsidy)", value=True)
        employed_12m = st.checkbox("Continuously employed for the past 12 months",
                                   value=True)

    with c2:
        monthly_income = st.number_input(
            "Average gross monthly household income (S$)",
            min_value=0, max_value=50000, value=6000, step=250)
        cpf_oa = st.number_input("Combined CPF Ordinary Account savings (S$)",
                                 min_value=0, max_value=1000000,
                                 value=60000, step=5000)
        cash_savings = st.number_input("Cash savings available (S$)",
                                       min_value=0, max_value=1000000,
                                       value=50000, step=5000)
        age_youngest = st.slider("Age of the youngest buyer", 21, 70, 32)

    with c3:
        flat_type = st.selectbox("Flat type you're looking at", FLAT_TYPES,
                                 index=2)
        towns = st.multiselect("Towns you're considering", TOWNS,
                               default=["BEDOK"], max_selections=3)
        proximity = st.selectbox(
            "Will you live with or near your parents / married child?",
            ["Neither", "Within 4km of them", "In the same flat as them"])
        loan_type = st.radio("Loan you intend to take", ["HDB loan", "Bank loan"],
                             horizontal=True)
        other_debt = st.number_input("Other monthly debt repayments (S$)",
                                     min_value=0, max_value=20000, value=0,
                                     step=100)

    submitted = st.form_submit_button("Assess my position", type="primary",
                                      use_container_width=True)

if not submitted and "assessment" not in st.session_state:
    st.info("Fill in the form above and select **Assess my position**.")
    st.stop()

if submitted:
    p = Profile(
        household="FAMILY" if household.startswith("A couple") else "SINGLE",
        citizenship={"Both Singapore Citizens": "SC_SC",
                     "One SC, one Singapore PR": "SC_SPR",
                     "Single Singapore Citizen": "SC_ONLY"}[citizenship],
        first_timer=first_timer,
        age_youngest=age_youngest,
        monthly_income=float(monthly_income),
        cpf_oa=float(cpf_oa),
        cash_savings=float(cash_savings),
        employed_12m=employed_12m,
        proximity={"Neither": "NONE", "Within 4km of them": "NEAR",
                   "In the same flat as them": "WITH"}[proximity],
        flat_type=flat_type,
        towns=towns or ["BEDOK"],
        loan_type="HDB" if loan_type == "HDB loan" else "BANK",
        other_monthly_debt=float(other_debt),
    )
    st.session_state["profile"] = p
    st.session_state.pop("briefing", None)

p: Profile = st.session_state["profile"]

# --------------------------------------------------------------------------
# STAGE 2 & 4 — deterministic engines
# --------------------------------------------------------------------------

assessment = full_assessment(p)
st.session_state["assessment"] = assessment
grants, aff, costs = assessment["grants"], assessment["affordability"], assessment["costs"]

st.divider()
st.markdown("### 1. Grants you qualify for")
st.caption("Calculated in Python from published policy tables — not generated "
           "by a language model.")

gcols = st.columns(4)
labels = {"EHG": "Enhanced CPF Housing Grant",
          "CHG": "CPF Housing Grant (Resale)",
          "PHG": "Proximity Housing Grant"}
for i, (key, label) in enumerate(labels.items()):
    amt, reason = grants["grants"][key]
    with gcols[i]:
        st.metric(label, f"${amt:,.0f}")
        st.caption(reason)
with gcols[3]:
    st.metric("**Total grants**", f"${grants['total']:,.0f}")
    st.caption("Credited to your CPF Ordinary Account, and repayable with "
               "accrued interest when you sell.")

# --------------------------------------------------------------------------
# STAGE 3 — TOOL CALL: live market data
# --------------------------------------------------------------------------

st.divider()
st.markdown("### 2. What these flats actually sell for")

with st.spinner("Querying live HDB transaction data from data.gov.sg…"):
    snapshot = market_snapshot(p.towns, p.flat_type, months_back=12)

if not snapshot["by_town"]:
    st.warning("No transactions found for that combination in the last 12 "
               "months, or the data.gov.sg service is unavailable. The "
               "affordability figures below still apply.")
    median_price = None
else:
    rows = []
    for town, s in snapshot["by_town"].items():
        rows.append({
            "Town": town, "Transactions": s["n_transactions"],
            "25th percentile": f"${s['p25']:,.0f}",
            "Median": f"${s['median']:,.0f}",
            "75th percentile": f"${s['p75']:,.0f}",
            "Range": f"${s['min']:,.0f} – ${s['max']:,.0f}",
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

    medians = [s["median"] for s in snapshot["by_town"].values()]
    median_price = sum(medians) / len(medians)

    trend = monthly_median_series(snapshot["pooled"])
    if not trend.empty:
        st.caption(f"Median monthly price, {p.flat_type} flats in "
                   f"{', '.join(p.towns)}")
        st.line_chart(trend.set_index("Month"), height=240)

    st.caption("Source: HDB resale transactions, data.gov.sg "
               "(dataset d_8b84c4ee58e3cfc0ece0d773c8ca6abc), last 12 months.")

# --------------------------------------------------------------------------
# STAGE 4 display — affordability
# --------------------------------------------------------------------------

st.divider()
st.markdown("### 3. What you can afford")

a1, a2, a3 = st.columns(3)
a1.metric("Maximum supportable price", f"${aff['max_price']:,.0f}")
a2.metric("Maximum loan", f"${aff['max_loan']:,.0f}",
          help=f"{aff['tenure_years']}-year tenure at "
               f"{aff['interest_rate'] * 100:.1f}%, limited by "
               f"{aff['servicing_rule']}")
a3.metric("Binding constraint", aff["binding_constraint"])

if median_price:
    st.markdown("#### If you bought at the median price for your towns")
    target = st.slider("Purchase price to test (S$)",
                       min_value=int(median_price * 0.6),
                       max_value=int(median_price * 1.5),
                       value=int(median_price), step=5000)
    costs = full_assessment(p, target_price=float(target))["costs"]
    st.session_state["assessment"]["costs"] = costs

b1, b2, b3, b4 = st.columns(4)
b1.metric("Loan", f"${costs['loan']:,.0f}")
b2.metric("Monthly instalment", f"${costs['monthly_instalment']:,.0f}",
          f"{costs['instalment_as_pct_income']:.0f}% of income")
b3.metric("Total cash you need", f"${costs['total_cash_required']:,.0f}")
b4.metric("Cash shortfall", f"${costs['cash_shortfall']:,.0f}",
          delta_color="inverse")

with st.expander("Full cost breakdown"):
    st.dataframe(pd.DataFrame([
        {"Item": "Purchase price", "Amount": f"${costs['price']:,.0f}"},
        {"Item": "Less: housing loan", "Amount": f"-${costs['loan']:,.0f}"},
        {"Item": "Downpayment", "Amount": f"${costs['downpayment']:,.0f}"},
        {"Item": "Grants applied", "Amount": f"${costs['grants_applied']:,.0f}"},
        {"Item": "CPF OA drawn down", "Amount": f"${costs['cpf_oa_used']:,.0f}"},
        {"Item": "Buyer's stamp duty", "Amount": f"${costs['stamp_duty']:,.0f}"},
        {"Item": "Legal / conveyancing (est.)", "Amount": f"${costs['legal_fees']:,.0f}"},
        {"Item": "**Total cash required**",
         "Amount": f"**${costs['total_cash_required']:,.0f}**"},
    ]), hide_index=True, use_container_width=True)
    st.caption("Excludes cash over valuation, renovation, agent commission and "
               "the option fees, which are all cash items. See the Guide for "
               "the full checklist.")

# --------------------------------------------------------------------------
# STAGES 5 & 6 — the LLM chain
# --------------------------------------------------------------------------

st.divider()
st.markdown("### 4. Your personalised briefing")

if not llm_available():
    st.error("No LLM API key is configured, so the written briefing is "
             "unavailable. Everything above is unaffected — it is computed "
             "without a language model.")
    st.stop()

facts = {
    "household": p.household,
    "first_timer": p.first_timer,
    "monthly_income": p.monthly_income,
    "cpf_oa": p.cpf_oa,
    "cash_savings": p.cash_savings,
    "flat_type": p.flat_type,
    "towns": p.towns,
    "loan_type": p.loan_type,
    "age_youngest": p.age_youngest,
    "grants": {k: v[0] for k, v in grants["grants"].items()},
    "grants_total": grants["total"],
    "max_price": round(aff["max_price"]),
    "max_loan": round(aff["max_loan"]),
    "binding_constraint": aff["binding_constraint"],
    "target_price": round(costs["price"]),
    "monthly_instalment": round(costs["monthly_instalment"]),
    "instalment_pct_income": round(costs["instalment_as_pct_income"], 1),
    "total_cash_required": round(costs["total_cash_required"]),
    "cash_shortfall": round(costs["cash_shortfall"]),
    "market_median": round(median_price) if median_price else None,
}

ANALYST_SYSTEM = """You are an analyst for a Singapore public-information \
service on HDB resale flats. You are given a set of figures that have ALREADY \
been computed by a verified rules engine. You must not recompute, contradict or \
invent any number.

Assess the buyer's position and return JSON with exactly these keys:
  verdict      one of "comfortable", "workable", "stretched", "not_yet"
  headline     one sentence, under 25 words, summarising the position
  risks        array of 2-4 objects, each {"risk": str, "why": str}
  actions      array of 3-4 short imperative next steps, most important first
  overlooked   one thing this specific buyer is most likely to have missed

Judge "stretched" if the instalment exceeds 25% of income or there is a cash \
shortfall. Judge "not_yet" if the maximum supportable price is well below the \
market median for their chosen towns."""

BRIEFING_SYSTEM = """You are writing to a member of the public in Singapore who \
is thinking about buying an HDB resale flat.

You are given (a) verified figures and (b) a structured assessment produced by \
an earlier analysis step. Turn them into a briefing of 200-300 words.

Rules:
- Use only the numbers supplied. Never introduce a figure of your own.
- Plain English. No jargon without a short gloss. Singapore spelling.
- Open with where they stand, then the risks, then what to do next.
- You are providing information, not financial advice. Do not tell them whether \
to buy, and do not recommend specific properties or financial products.
- End with one line reminding them the figures are estimates and that an HDB \
Flat Eligibility letter gives the authoritative answer.
- Do not use headings. Write flowing paragraphs."""

if st.button("Generate my briefing", type="primary") or "briefing" in st.session_state:
    if "briefing" not in st.session_state:
        # ---- LLM CALL A: structured assessment
        with st.spinner("Analysing your position…"):
            analysis = complete_json(
                ANALYST_SYSTEM,
                f"<verified_figures>\n{json.dumps(facts, indent=2)}\n</verified_figures>",
                schema_keys=["verdict", "headline", "risks", "actions", "overlooked"],
                temperature=0.1,
            )
        if analysis is None:
            st.error("The analysis step did not return a valid result. "
                     "Please try again.")
            st.stop()
        st.session_state["analysis"] = analysis

        # ---- LLM CALL B: narrative, conditioned on call A's output
        with st.spinner("Writing your briefing…"):
            briefing = complete(
                BRIEFING_SYSTEM,
                f"<verified_figures>\n{json.dumps(facts, indent=2)}\n</verified_figures>\n\n"
                f"<structured_assessment>\n{json.dumps(analysis, indent=2)}\n</structured_assessment>",
                temperature=0.4, max_tokens=800,
            )
        if not briefing or not output_is_safe(briefing):
            st.error("The briefing could not be generated safely. Please try again.")
            st.stop()
        st.session_state["briefing"] = briefing

    analysis = st.session_state["analysis"]
    verdict_style = {"comfortable": "✅", "workable": "🟢",
                     "stretched": "🟠", "not_yet": "🔴"}
    st.markdown(f"#### {verdict_style.get(analysis['verdict'], '•')} "
                f"{analysis['headline']}")

    st.markdown(st.session_state["briefing"])

    r1, r2 = st.columns(2)
    with r1:
        st.markdown("**Main risks**")
        for r in analysis["risks"]:
            st.markdown(f"- **{r['risk']}** — {r['why']}")
    with r2:
        st.markdown("**Your next steps**")
        for i, a in enumerate(analysis["actions"], 1):
            st.markdown(f"{i}. {a}")

    st.info(f"**Most commonly missed:** {analysis['overlooked']}")

    # Hand the profile to Use Case 2.
    st.session_state["profile_summary"] = {
        "household": p.household, "first_timer": p.first_timer,
        "flat_type": p.flat_type, "towns": p.towns, "loan_type": p.loan_type,
        "age_youngest": p.age_youngest, "proximity": p.proximity,
        "grants_total": grants["total"], "target_price": round(costs["price"]),
        "cash_shortfall": round(costs["cash_shortfall"]),
    }
    st.success("✅ Your profile has been saved to this session. Answers in "
               "**Ask the Resale Guide** will now be tailored to it.")
    st.page_link("pages/2_Ask_the_Resale_Guide.py",
                 label="Ask a question about your situation", icon="💬")

with st.expander("Policy parameters and sources used on this page"):
    st.dataframe(pd.DataFrame(
        [{"Parameter": k, "Source": v} for k, v in POLICY_SOURCES.items()]),
        hide_index=True, use_container_width=True)
