import streamlit as st
import pandas as pd

st.title("Overzicht projecturen")

if "projecturen_schoon" not in st.session_state:
    st.info("Controleer eerst de projecturendata bij Datacontrole.")
    st.stop()

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
weken = range(1, laatste_week + 1)
projecten = sorted(projecturen["Project"].dropna().unique())

rijen = []

for project in projecten:
    data_project = uren_per_week[
        uren_per_week["Project"] == project
    ]

    actieve_weken = data_project[data_project["Hours"] > 0]

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
        "Laatste": laatste_actieve_week if laatste_actieve_week is not None else "-"
    }

    for week in weken:
        if startweek is None or week < startweek:
            waarde = "NS"

        elif week > laatste_actieve_week:
            waarde = "NA"

        else:
            uren = uren_dict.get(week, 0)

            if uren == 0:
                waarde = "0"
            else:
                waarde = f"{uren:.0f}"

        rij[str(week)] = waarde

    rijen.append(rij)

overzicht = pd.DataFrame(rijen)

week_kolommen = [str(week) for week in weken]

def kleur_cel(waarde):

    # Nog niet gestart
    if waarde == "NS":
        return (
            "background-color: #f2f2f2; "
            "color: #f2f2f2;"
        )

    # Na laatste actieve week
    if waarde == "NA":
        return (
            "background-color: #dddddd; "
            "color: #dddddd;"
        )

    uren = float(waarde)

    # Geen uren
    if uren == 0:
        return (
            "background-color: #ffffff; "
            "color: #ffffff;"
        )

    # 1 - 30 uur
    elif uren <= 30:
        return (
            "background-color: #eaf4ff; "
            "color: #24435c;"
        )

    # 31 - 50 uur
    elif uren <= 50:
        return (
            "background-color: #c9e3fa; "
            "color: #183b56;"
        )

    # 51 - 70 uur
    elif uren <= 70:
        return (
            "background-color: #91c4ed; "
            "color: #123653;"
        )

    # 71 - 90 uur
    elif uren <= 90:
        return (
            "background-color: #559bd0; "
            "color: white;"
        )

    # Meer dan 90 uur
    else:
        return (
            "background-color: #21689d; "
            "color: white; "
            "font-weight: bold;"
        )

stijl = overzicht.style.map(
    kleur_cel,
    subset=week_kolommen
)

st.caption(
    "Lichtgrijs = nog niet gestart  ·  "
    "Wit = 0 uur  ·  "
    "Blauw = uren geboekt  ·  "
    "Donkerder blauw = meer uren  ·  "
    "Grijs = na laatste actieve week"
)

st.dataframe(
    stijl,
    hide_index=True,
    use_container_width=True,
    height=600
)