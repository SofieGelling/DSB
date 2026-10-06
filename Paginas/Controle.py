import streamlit as st
from Functies import controle_data, missende_waarden


st.title("Datacontrole")
tab_projecturen, tab_werknemers, tab_project_budget = st.tabs(["Projecturen","Werknemers","Project & budgets"])

# ------------------------------------------------------------------------------------------------------------
# PROJECTUREN
# ------------------------------------------------------------------------------------------------------------

with tab_projecturen:
    if "projecturen" in st.session_state:
        controle_data(st.session_state["projecturen"],"projecturen"),
        missende_waarden(st.session_state["projecturen"])

    else:
        st.info("Upload eerst de bestanden met projecturen.")


# ------------------------------------------------------------------------------------------------------------
# WERKNEMERS
# ------------------------------------------------------------------------------------------------------------

with tab_werknemers:
    if "werknemers" in st.session_state:
        controle_data(st.session_state["werknemers"],"werknemers"),
        missende_waarden(st.session_state["werknemers"])

    else:
        st.info("Upload eerst de bestanden met werknemersgegevens.")


# -------------------------------------------------------------------------------------------------------------
# PROJECT & BUDGETS
# ------------------------------------------------------------------------------------------------------------

with tab_project_budget:
    if "project_budget" in st.session_state:
        controle_data(st.session_state["project_budget"],"project_budget"),
        missende_waarden(st.session_state["project_budget"])

    else:
        st.info("Upload eerst de bestanden met projecten en budgets.")