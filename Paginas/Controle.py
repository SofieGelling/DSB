import streamlit as st
from Functies import (
    controle_data,
    missende_waarden,
    bereken_projectkosten
)

st.title("Datacontrole")

tab_projecturen, tab_werknemers, tab_project_budget, tab_koppeling = st.tabs([
    "Projecturen",
    "Werknemers",
    "Project & budgets",
    "Koppeling werknemers"
])

# PROJECTUREN
with tab_projecturen:
    if "projecturen" in st.session_state:
        controle_data(st.session_state["projecturen"], "projecturen")
        missende_waarden(st.session_state["projecturen"])
    else:
        st.info("Upload eerst de bestanden met projecturen.")

# WERKNEMERS
with tab_werknemers:
    if "werknemers" in st.session_state:
        controle_data(st.session_state["werknemers"], "werknemers")
        missende_waarden(st.session_state["werknemers"])
    else:
        st.info("Upload eerst de bestanden met werknemersgegevens.")

# PROJECT & BUDGETS
with tab_project_budget:
    if "project_budget" in st.session_state:
        controle_data(st.session_state["project_budget"], "project_budget")
        missende_waarden(st.session_state["project_budget"])
    else:
        st.info("Upload eerst de bestanden met projecten en budgets.")

# KOPPELING WERKNEMERS
with tab_koppeling:
    if (
        "projecturen" in st.session_state
        and "werknemers" in st.session_state
    ):
        kosten_data = bereken_projectkosten(
            st.session_state["projecturen"],
            st.session_state["werknemers"]
        )

        controle_koppeling = (
            kosten_data[
                [
                    "Consultant",
                    "Full Name",
                    "Residence",
                    "Gekozen land",
                    "Grade",
                    "Controle"
                ]
            ]
            .drop_duplicates()
            .rename(columns={
                "Consultant": "Persoon projecturen",
                "Full Name": "Gekoppelde werknemer"
            })
        )

        problemen = controle_koppeling[
            controle_koppeling["Controle"] != "OK"
        ]

        if problemen.empty:
            st.success("Alle werknemers zijn correct gekoppeld.")
        else:
            st.warning(
                f"Bij {len(problemen)} koppeling(en) is een probleem gevonden."
            )

        st.dataframe(
            controle_koppeling,
            hide_index=True,
            use_container_width=True
        )

    else:
        st.info(
            "Upload eerst zowel de projecturen als de werknemersgegevens."
        )