"""About Us — project scope, objectives, data sources and features."""

import pandas as pd
import streamlit as st

from core import (
    PASSAGES,
    disclaimer,
    require_auth,
    sidebar_note,
)


st.set_page_config(page_title="About Us", page_icon="ℹ️", layout="wide")
require_auth()
sidebar_note()

st.title("ℹ️ About ResaleReady")
disclaimer()

st.markdown("""
## The problem

Around twenty-five thousand HDB resale flats change hands in Singapore each
year, and for most buyers it is the largest financial commitment they will ever
make. The information needed to make that decision well is all public — but it
is scattered across four agencies, each publishing correctly and completely
within its own remit and none of them answering the question the buyer actually
has, which is *"given my situation, what can I afford, what will the government
give me, and what do I have to do next?"*

Specifically, a buyer must reconcile:

- **HDB** — eligibility schemes, the HDB Flat Eligibility letter, the Option to
  Purchase timeline, ethnic and PR quotas, the Minimum Occupation Period, the
  resale levy
- **CPF Board** — three separate grants with different ceilings and tiers, and
  the rules limiting how much CPF can be used on a flat with a short remaining
  lease
- **MAS** — loan-to-value limits, the Mortgage Servicing Ratio, the Total Debt
  Servicing Ratio
- **IRAS** — Buyer's Stamp Duty

The failure mode is not that any single page is unclear. It is that no page
brings them together, so buyers routinely discover a binding constraint late —
after they have already committed to a price.

## What this application does

ResaleReady consolidates those rulebooks into one place, applies them to a
profile the user supplies, checks the result against live transaction data, and
explains the outcome in plain language.

## Objectives

1. **Consolidate.** Bring the rules of four agencies, plus the national resale
   transaction dataset, into a single interface.
2. **Personalise.** Turn generic policy into a specific answer, using only
   non-personally-identifiable inputs.
3. **Explain.** Use a language model for what it is genuinely good at —
   interpretation, narrative, and answering follow-up questions — while keeping
   every dollar figure under deterministic control.
4. **Ground.** Cite a named official source for every substantive claim, so the
   user can verify rather than trust.
""")

st.divider()
st.markdown("## Features")

f1, f2 = st.columns(2)
with f1:
    st.markdown("""
    #### Use Case 1 — Budget & Grant Navigator
    - Grant-by-grant eligibility with the **reason** for each verdict, not just
      an amount
    - Live transaction data for the user's chosen towns and flat type, with
      quartiles and a twelve-month price trend
    - Affordability under the buyer's chosen loan type, with the **binding
      constraint** named
    - An interactive price slider that recomputes the full cost stack
    - A two-stage LLM chain producing a structured assessment and then a written
      briefing
    """)
with f2:
    st.markdown("""
    #### Use Case 2 — Ask the Resale Guide
    - Free-text questions answered from a curated corpus of official passages
    - Inline citations, with the source passages and their URLs exposed
    - **Profile carry-over**: answers are conditioned on the user's Navigator
      profile, so a general rule is applied to their specific case
    - Model-generated follow-up questions, clickable to continue the thread
    - Explicit refusal when the corpus does not cover the question, rather than
      an invented answer
    """)

st.divider()
st.markdown("## Data sources")

st.markdown("""
All sources are publicly accessible and official. Nothing is scraped from
commercial property portals, and no source requires authentication.
""")

st.dataframe(pd.DataFrame([
    {"Source": "data.gov.sg — HDB resale transactions",
     "Type": "Live API",
     "Used for": "Actual transacted prices, quartiles, twelve-month trend",
     "Detail": "Dataset d_8b84c4ee58e3cfc0ece0d773c8ca6abc, updated monthly, "
               "Open Data Licence"},
    {"Source": "HDB", "Type": "Policy parameters + knowledge base",
     "Used for": "EHG and Family Grant tables, eligibility schemes, HFE letter, "
                 "OTP timeline, ethnic quotas, MOP, resale levy",
     "Detail": "hdb.gov.sg and mynicehome.gov.sg"},
    {"Source": "CPF Board", "Type": "Policy parameters + knowledge base",
     "Used for": "Proximity Housing Grant amounts, CPF usage limits by "
                 "remaining lease, grant refund rules",
     "Detail": "cpf.gov.sg"},
    {"Source": "MAS / MND", "Type": "Policy parameters",
     "Used for": "75% loan-to-value limit, MSR 30%, TDSR 55%",
     "Detail": "LTV lowered to 75% w.e.f. 20 August 2024"},
    {"Source": "IRAS", "Type": "Policy parameters + knowledge base",
     "Used for": "Buyer's Stamp Duty bands",
     "Detail": "Rates w.e.f. 15 February 2023"},
]), hide_index=True, use_container_width=True)

st.caption(f"The knowledge base comprises {len(PASSAGES)} curated passages, each "
           "paraphrased from a named official source and carrying its URL.")

st.divider()
st.markdown("""
## Scope and limitations

This is a **prototype built for an educational assignment**. It is deliberately
bounded:

- It covers **resale flats bought on the open market only** — not Build-To-Order
  flats, Sale of Balance Flats, executive condominiums or private property.
- Policy parameters are **hard-coded as at August 2026** and do not update
  themselves. Housing policy changes frequently; the figures should be treated
  as illustrative.
- Affordability is modelled on **standard cases**. It does not handle the
  Fresh Start Housing Scheme, right-sizing for seniors, divorce or bereavement
  cases, non-citizen spouse arrangements, or applicants over fifty-five, all of
  which carry different rules.
- Cash over valuation, renovation and agent commission are **flagged but not
  modelled**, because they cannot be estimated from public data.
- The application collects **no personally identifiable information** and
  persists nothing beyond the browser session.

The authoritative answer on eligibility, grants and loan quantum comes from an
**HDB Flat Eligibility letter**. This application is a way to think the problem
through before applying for one — not a substitute for it.

## Author

Built as an individual capstone submission for the AI Champions Bootcamp
(Whole-of-Government, 2026).
""")
