import streamlit as st
import pandas as pd
from Functies import overzicht_projecten

st.title("Overzicht projecturen")
tab_projecten, tab_uren = st.tabs(["Projecten", "Uren"])

# PROJECTEN
with tab_projecten:
    st.subheader("Uren per project")

    if "projecturen_schoon" in st.session_state:
        projecturen = st.session_state["projecturen_schoon"]
        overzicht_projecten(projecturen)
    else:
        st.info("Controleer eerst de projecturendata bij Datacontrole.")

# UREN
with tab_uren:
    st.subheader("Uren per project per week")

    if "projecturen_schoon" in st.session_state:
        projecturen = st.session_state["projecturen_schoon"].copy()

        projecturen["Hours"] = pd.to_numeric(
            projecturen["Hours"],
            errors="coerce"
        ).fillna(0)

        # Weeknummer numeriek maken
        projecturen["Week"] = (
            projecturen["Week"]
            .astype(str)
            .str.extract(r"(\d+)")[0]
        )

        projecturen["Week"] = pd.to_numeric(
            projecturen["Week"],
            errors="coerce"
        )

        projecturen = projecturen.dropna(subset=["Week"])
        projecturen["Week"] = projecturen["Week"].astype(int)

        # Uren per project per week optellen
        uren_per_week = (
            projecturen
            .groupby(["Week", "Project"])["Hours"]
            .sum()
            .reset_index()
        )

        # Omzetten zodat ieder project een aparte lijn wordt
        grafiek = uren_per_week.pivot(
            index="Week",
            columns="Project",
            values="Hours"
        )

        # Alle weken 0 t/m 51 tonen
        grafiek = grafiek.reindex(range(0, 52), fill_value=0)
        grafiek = grafiek.fillna(0)

        st.line_chart(grafiek)

    else:
        st.info("Controleer eerst de projecturendata bij Datacontrole.")