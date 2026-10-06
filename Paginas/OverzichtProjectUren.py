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

# Vanaf week 1, dus geen W0
weken = range(1, laatste_week + 1)

projecten = sorted(
    projecturen["Project"].dropna().unique()
)

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
        "Totaal uren": round(data_project["Hours"].sum(), 1)
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

# ---------------------------------------------------------
# SORTERING
# ---------------------------------------------------------

sortering = st.selectbox(
    "Sorteer projecten op",
    [
        "Startweek",
        "Totaal uren - hoog naar laag",
        "Totaal uren - laag naar hoog",
        "Laatste activiteit",
        "Projectnaam"
    ]
)

if sortering == "Startweek":
    overzicht["_sort"] = pd.to_numeric(
        overzicht["Start"], errors="coerce"
    ).fillna(999)

    overzicht = (
        overzicht
        .sort_values("_sort")
        .drop(columns="_sort")
    )

elif sortering == "Totaal uren - hoog naar laag":
    overzicht = overzicht.sort_values(
        "Totaal uren",
        ascending=False
    )

elif sortering == "Totaal uren - laag naar hoog":
    overzicht = overzicht.sort_values(
        "Totaal uren",
        ascending=True
    )

elif sortering == "Laatste activiteit":
    overzicht["_sort"] = pd.to_numeric(
        overzicht["Laatste actief"],
        errors="coerce"
    ).fillna(999)

    overzicht = (
        overzicht
        .sort_values("_sort")
        .drop(columns="_sort")
    )

else:
    overzicht = overzicht.sort_values("Project")

week_kolommen = [
    kolom for kolom in overzicht.columns
    if kolom.startswith("W")
]

# ---------------------------------------------------------
# KLEUREN
# ---------------------------------------------------------

def kleur_cel(waarde):

    if waarde == "NS":
        return "background-color: #eeeeee; color: #888888"

    if waarde == "—":
        return "background-color: #dddddd; color: #888888"

    uren = float(waarde)

    if uren == 0:
        return "background-color: #ffffff; color: #666666"

    elif uren <= 30:
        return "background-color: #eaf4ff; color: #123a5a"

    elif uren <= 50:
        return "background-color: #cfe8ff; color: #123a5a"

    elif uren <= 70:
        return "background-color: #8fc7f5; color: #0b3150"

    elif uren <= 90:
        return "background-color: #4a98d1; color: white"

    else:
        return "background-color: #17649a; color: white; font-weight: bold"

stijl = overzicht.style.map(
    kleur_cel,
    subset=week_kolommen
)

st.caption(
    "NS = nog niet gestart  |  "
    "0 = geen uren geboekt  |  "
    "1–30 = lichtblauw  |  "
    "31–50  |  51–70  |  71–90  |  "
    ">90 = donkerblauw  |  "
    "— = na laatste actieve week"
)

st.dataframe(
    stijl,
    hide_index=True,
    use_container_width=True,
    height=650
)