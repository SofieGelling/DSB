import streamlit as st

from Functies import (
    controle_data,
    missende_waarden,
    bereken_projectkosten,
    kosten_per_project_week,
    kosten_naar_euro,
    vergelijk_kosten_met_budget
)

st.title("Datacontrole")

tab_projecturen, tab_werknemers, tab_project_budget, tab_koppeling = st.tabs([
    "Projecturen",
    "Werknemers",
    "Project & budgets",
    "Koppeling werknemers"
])


# --------------------------------------------------
# PROJECTUREN
# --------------------------------------------------

with tab_projecturen:

    if "projecturen" in st.session_state:

        controle_data(
            st.session_state["projecturen"],
            "projecturen"
        )

        missende_waarden(
            st.session_state["projecturen"]
        )

    else:
        st.info(
            "Upload eerst de bestanden met projecturen."
        )


# --------------------------------------------------
# WERKNEMERS
# --------------------------------------------------

with tab_werknemers:

    if "werknemers" in st.session_state:

        controle_data(
            st.session_state["werknemers"],
            "werknemers"
        )

        missende_waarden(
            st.session_state["werknemers"]
        )

    else:
        st.info(
            "Upload eerst de bestanden met werknemersgegevens."
        )


# --------------------------------------------------
# PROJECT & BUDGETS
# --------------------------------------------------

with tab_project_budget:

    if "project_budget" in st.session_state:

        controle_data(
            st.session_state["project_budget"],
            "project_budget"
        )

        missende_waarden(
            st.session_state["project_budget"]
        )

    else:
        st.info(
            "Upload eerst de bestanden met projecten en budgets."
        )


# --------------------------------------------------
# KOPPELING WERKNEMERS
# --------------------------------------------------

with tab_koppeling:

    if (
        "projecturen" in st.session_state
        and "werknemers" in st.session_state
        and "uurtarieven" in st.session_state
    ):

        projecturen = st.session_state.get(
            "projecturen_schoon",
            st.session_state["projecturen"]
        )

        werknemers = st.session_state.get(
            "werknemers_schoon",
            st.session_state["werknemers"]
        )


        # --------------------------------------------------
        # KOSTEN BEREKENEN
        # --------------------------------------------------

        kosten_data = bereken_projectkosten(
            projecturen,
            werknemers,
            st.session_state["uurtarieven"]
        )

        st.session_state["kosten_data"] = kosten_data


        # --------------------------------------------------
        # CONTROLE KOPPELING WERKNEMERS
        # --------------------------------------------------

        st.subheader("Controle koppeling werknemers")

        controle_koppeling = (
            kosten_data[
                [
                    "Consultant",
                    "Full Name",
                    "Residence",
                    "Gekozen land",
                    "Grade",
                    "Annual Salary",
                    "Contract",
                    "Uurtarief",
                    "Valuta",
                    "Tariefbron",
                    "Controle"
                ]
            ]
            .drop_duplicates()
            .rename(
                columns={
                    "Consultant": "Persoon projecturen",
                    "Full Name": "Gekoppelde werknemer"
                }
            )
            .sort_values(
                "Persoon projecturen"
            )
        )

        problemen = controle_koppeling[
            controle_koppeling["Controle"] != "OK"
        ]

        if problemen.empty:

            st.success(
                "Alle werknemers zijn correct gekoppeld aan een uurtarief."
            )

        else:

            st.warning(
                f"Bij {len(problemen)} werknemer(s) moet de koppeling "
                "worden gecontroleerd."
            )

        st.dataframe(
            controle_koppeling,
            hide_index=True,
            use_container_width=True
        )


        # --------------------------------------------------
        # KOSTEN PER PERSOON
        # --------------------------------------------------

        st.subheader("Berekende kosten")

        kosten_overzicht = (
            kosten_data[
                [
                    "Project",
                    "Week",
                    "Consultant",
                    "Hours",
                    "Uurtarief",
                    "Valuta",
                    "Kosten"
                ]
            ]
            .sort_values(
                [
                    "Project",
                    "Week",
                    "Consultant"
                ]
            )
        )

        st.dataframe(
            kosten_overzicht,
            hide_index=True,
            use_container_width=True
        )


        # --------------------------------------------------
        # KOSTEN PER PROJECT PER WEEK
        # --------------------------------------------------

        st.subheader("Kosten per project per week")

        project_week_kosten = kosten_per_project_week(
            kosten_data
        )

        st.session_state["project_week_kosten"] = (
            project_week_kosten
        )

        st.dataframe(
            project_week_kosten,
            hide_index=True,
            use_container_width=True
        )


        # --------------------------------------------------
        # WISSELKOERSEN
        # --------------------------------------------------

        st.subheader("Wisselkoersen naar euro")

        col1, col2, col3 = st.columns(3)

        with col1:

            usd_naar_eur = st.number_input(
                "1 USD = ... EUR",
                min_value=0.0,
                value=0.86,
                step=0.01
            )

        with col2:

            nok_naar_eur = st.number_input(
                "1 NOK = ... EUR",
                min_value=0.0,
                value=0.085,
                step=0.001
            )

        with col3:

            gbp_naar_eur = st.number_input(
                "1 GBP = ... EUR",
                min_value=0.0,
                value=1.15,
                step=0.01
            )


        # --------------------------------------------------
        # ALLE KOSTEN OMZETTEN NAAR EURO
        # --------------------------------------------------

        kosten_euro = kosten_naar_euro(
            kosten_data,
            usd_naar_eur,
            nok_naar_eur,
            gbp_naar_eur
        )

        st.session_state["kosten_euro"] = kosten_euro


        # --------------------------------------------------
        # KOSTEN PER PROJECT PER WEEK IN EURO
        # --------------------------------------------------

        st.subheader(
            "Kosten per project per week in euro"
        )

        project_week_euro = (
            kosten_euro
            .groupby(
                [
                    "Project",
                    "Week"
                ],
                as_index=False
            )
            .agg(
                Uren=("Hours", "sum"),
                Kosten_EUR=("Kosten_EUR", "sum")
            )
        )

        project_week_euro["Kosten_EUR"] = (
            project_week_euro[
                "Kosten_EUR"
            ].round(2)
        )

        project_week_euro = (
            project_week_euro.sort_values(
                [
                    "Project",
                    "Week"
                ]
            )
        )

        st.session_state[
            "project_week_euro"
        ] = project_week_euro

        st.dataframe(
            project_week_euro,
            hide_index=True,
            use_container_width=True
        )


        # --------------------------------------------------
        # PROJECTKOSTEN VERSUS BUDGET
        # --------------------------------------------------

        st.subheader(
            "Projectkosten versus budget"
        )

        if "project_budget" in st.session_state:

            project_budget = (
                st.session_state.get(
                    "project_budget_schoon",
                    st.session_state[
                        "project_budget"
                    ]
                )
            )

            budget_overzicht = (
                vergelijk_kosten_met_budget(
                    project_week_euro,
                    project_budget
                )
            )

            st.session_state[
                "budget_overzicht"
            ] = budget_overzicht

            st.dataframe(
                budget_overzicht,
                hide_index=True,
                use_container_width=True
            )

        else:

            st.info(
                "Upload eerst de project- en budgetgegevens."
            )


    else:

        ontbreekt = []

        if "projecturen" not in st.session_state:
            ontbreekt.append(
                "projecturen"
            )

        if "werknemers" not in st.session_state:
            ontbreekt.append(
                "werknemers"
            )

        if "uurtarieven" not in st.session_state:
            ontbreekt.append(
                "uurtarieven"
            )

        st.info(
            "Upload eerst: "
            + ", ".join(ontbreekt)
            + "."
        )