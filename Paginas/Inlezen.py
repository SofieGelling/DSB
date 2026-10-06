import streamlit as st
import pandas as pd

from Functies import bestanden_inlezen, inlezen_employee_bestanden


st.title("Data inlezen")


# PROJECTUREN
projecturen = bestanden_inlezen(
    titel="Projecturen",
    uitleg="Upload hieronder de bestanden met projecturen. "
           "De bestanden worden automatisch samengevoegd.",
    key="projecturen_upload"
)

if projecturen is not None:
    st.session_state["projecturen"] = projecturen


# WERKNEMERS
werknemers = inlezen_employee_bestanden(
    titel="Werknemers",
    uitleg="Upload hieronder de bestanden met werknemersgegevens.",
    key="werknemers_upload")

if werknemers is not None:
    st.session_state["werknemers"] = werknemers


# PROJECT & BUDGETS
project_budget = bestanden_inlezen(
    titel="Project & budgets",
    uitleg="Upload hieronder de bestanden met project- en budgetgegevens.",
    key="project_budget_upload"
)

if project_budget is not None:
    st.session_state["project_budget"] = project_budget