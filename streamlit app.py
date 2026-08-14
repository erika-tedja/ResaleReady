"""ResaleReady — HDB resale flat navigator. Entry point / home page."""

import streamlit as st

from core import (
    disclaimer,
    require_auth,
    sidebar_note,
)


st.set_page_config(page_title="ResaleReady", page_icon="🏠", layout="wide")

require_auth()
sidebar_note()

st.title("🏠 ResaleReady")
st.subheader("Making sense of buying an HDB resale flat in Singapore")

disclaimer(expanded=True)

st.markdown("""
Buying a resale flat means holding several separate government rulebooks in
your head at once — HDB's eligibility schemes, CPF's grant tiers and usage
limits, MAS's loan rules, IRAS's stamp duty bands — and then working out what
any of it means for the flat you actually want.

ResaleReady pulls those rules together, applies them to your situation, checks
them against **live transaction data from data.gov.sg**, and explains the result
in plain language.
""")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    #### 💰 Budget & Grant Navigator
    Tell it about your household and it works out every grant you qualify for
    and why, how much you can borrow, what the flats you're looking at actually
    sell for, and how much cash you need to find. Then it writes you a
    personalised briefing.

    *Uses live HDB transaction data.*
    """)
    st.page_link("pages/1_Budget_and_Grant_Navigator.py",
                 label="Open the Navigator", icon="💰")

with col2:
    st.markdown("""
    #### 💬 Ask the Resale Guide
    Ask anything about the purchase process — HFE letters, the option period,
    ethnic quotas, CPF limits on older flats, stamp duty — and get an answer
    grounded in official sources, with citations.

    *If you've used the Navigator, answers are tailored to your profile.*
    """)
    st.page_link("pages/2_Ask_the_Resale_Guide.py",
                 label="Open the Guide", icon="💬")

st.divider()

st.markdown("""
##### How to use this
Start with the **Budget & Grant Navigator** to build your profile, then move to
**Ask the Resale Guide** — it will remember your situation and answer against it.

The **About Us** and **Methodology** pages set out the scope, the data sources,
and how the application is built, including its defences against prompt
injection.
""")

if st.session_state.get("profile_summary"):
    st.success("✅ Your profile from the Navigator is loaded and will be used "
               "to personalise answers in the Guide.")
