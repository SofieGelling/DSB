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
    st.subheader("Projectplanning per week")

    if "projecturen_schoon" in st.session_state:
        projecturen = st.session_state["projecturen_schoon"].copy()

        projecturen["Hours"] = pd.to_numeric(
            projecturen["Hours"], errors="coerce"
        ).fillna(0)

        projecturen["Week"] = (
            projecturen["Week"]
            .astype(str)
            .str.extract(r"(\d+)")[0]
        )

        projecturen["Week"] = pd.to_numeric(
            projecturen["Week"], errors="coerce"
        )

        projecturen = projecturen.dropna(subset=["Week"])
        projecturen["Week"] = projecturen["Week"].astype(int)

        uren_per_week = (
            projecturen
            .groupby(["Project", "Week"])["Hours"]
            .sum()
            .reset_index()
        )

        laatste_week = int(projecturen["Week"].max())
        weken = range(0, laatste_week + 1)
        projecten = sorted(projecturen["Project"].dropna().unique())

        rijen = []

        for project in projecten:
            data_project = uren_per_week[
                uren_per_week["Project"] == project
            ]

            actieve_weken = data_project[
                data_project["Hours"] > 0
            ]

            if actieve_weken.empty:
                startweek = None
                laatste_actieve_week = None
            else:
                startweek = int(actieve_weken["Week"].min())
                laatste_actieve_week = int(actieve_weken["Week"].max())

            uren_dict = dict(
                zip(data_project["Week"], data_project["Hours"])
            )

            rij = {
                "Project": project,
                "Start": startweek if startweek is not None else "-",
                "Laatste actief": (
                    laatste_actieve_week
                    if laatste_actieve_week is not None
                    else "-"
                ),
                "Totaal": round(data_project["Hours"].sum(), 1)
            }

            for week in weken:
                if startweek is None or week < startweek:
                    waarde = "NS"

                elif week > laatste_actieve_week:
                    waarde = "—"

                else:
                    uren = uren_dict.get(week, 0)

                    if uren == 0:
                        waarde = "0"
                    else:
                        waarde = f"{uren:.0f}"

                rij[f"W{week}"] = waarde

            rijen.append(rij)

        overzicht = pd.DataFrame(rijen)

        # Sorteren op startweek
        overzicht["_sort"] = pd.to_numeric(
            overzicht["Start"],
            errors="coerce"
        ).fillna(999)

        overzicht = (
            overzicht
            .sort_values("_sort")
            .drop(columns="_sort")
        )

        week_kolommen = [
            kolom for kolom in overzicht.columns
            if kolom.startswith("W")
        ]

        # Kleuren van de weekcellen
        def kleur_cel(waarde):
            if waarde == "NS":
                return "background-color: #eeeeee; color: #888888"

            if waarde == "0":
                return "background-color: #ffd6d6; color: #9b1c1c; font-weight: bold"

            if waarde == "—":
                return "background-color: #dddddd; color: #777777"

            return "background-color: #d9ecff; color: #123a5a; font-weight: bold"

        stijl = overzicht.style.applymap(
            kleur_cel,
            subset=week_kolommen
        )

        st.caption(
            "NS = nog niet gestart  |  "
            "Blauw = uren geboekt  |  "
            "Rood = 0 uur binnen actieve periode  |  "
            "— = geen activiteit meer na laatste geboekte week"
        )

        st.dataframe(
            stijl,
            hide_index=True,
            use_container_width=True,
            height=600
        )

    else:
        st.info("Controleer eerst de projecturendata bij Datacontrole.")