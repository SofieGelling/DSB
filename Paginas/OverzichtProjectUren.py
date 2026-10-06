import streamlit as st
import pandas as pd

st.title("Overzicht projecturen")

if "projecturen_schoon" not in st.session_state:
    st.info("Controleer eerst de projecturendata bij Datacontrole.")
    st.stop()

projecturen = st.session_state["projecturen_schoon"].copy()

# Dataset met projecten en budgetten zoeken
project_budget = None

for waarde in st.session_state.values():
    if isinstance(waarde, pd.DataFrame):
        if (
            "Project" in waarde.columns
            and ("Budget_NL€" in waarde.columns or "Budget_BE€" in waarde.columns)
        ):
            project_budget = waarde.copy()
            break

if project_budget is None:
    st.info("Lees eerst het bestand met projecten en budgetten in.")
    st.stop()

# Projectnamen gelijk maken voor koppeling
projecturen["project_match"] = (
    projecturen["Project"]
    .astype(str)
    .str.strip()
    .str.lower()
)

project_budget["project_match"] = (
    project_budget["Project"]
    .astype(str)
    .str.strip()
    .str.lower()
)

# Budgetkolommen aanwezig maken
if "Budget_NL€" not in project_budget.columns:
    project_budget["Budget_NL€"] = pd.NA

if "Budget_BE€" not in project_budget.columns:
    project_budget["Budget_BE€"] = pd.NA

project_budget["Budget_NL€"] = pd.to_numeric(
    project_budget["Budget_NL€"], errors="coerce"
)

project_budget["Budget_BE€"] = pd.to_numeric(
    project_budget["Budget_BE€"], errors="coerce"
)

# NL-budget gebruiken, anders BE-budget
project_budget["Project budget"] = (
    project_budget["Budget_NL€"]
    .fillna(project_budget["Budget_BE€"])
)

budget_per_project = (
    project_budget
    .groupby("project_match")["Project budget"]
    .max()
)

# Uren en weken
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
    .groupby(["Project", "project_match", "Week"])["Hours"]
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

    project_match = (
        data_project["project_match"].iloc[0]
        if not data_project.empty else ""
    )

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
        "Project budget": budget_per_project.get(project_match, pd.NA),
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
            waarde = "0" if uren == 0 else f"{uren:.0f}"

        rij[str(week)] = waarde

    rijen.append(rij)

overzicht = pd.DataFrame(rijen)
week_kolommen = [str(week) for week in weken]

# Kleuren uren
def kleur_cel(waarde):
    if waarde == "NS":
        return "background-color: #f2f2f2; color: #f2f2f2"

    if waarde == "NA":
        return "background-color: #dddddd; color: #dddddd"

    uren = float(waarde)

    if uren == 0:
        return "background-color: #ffffff; color: #666666; font-weight: bold"
    elif uren <= 30:
        return "background-color: #eaf4ff; color: #24435c"
    elif uren <= 50:
        return "background-color: #c9e3fa; color: #183b56"
    elif uren <= 70:
        return "background-color: #91c4ed; color: #123653"
    elif uren <= 90:
        return "background-color: #559bd0; color: white"
    else:
        return "background-color: #21689d; color: white; font-weight: bold"

# Budget €0 rood
def kleur_budget(waarde):
    if pd.isna(waarde):
        return ""

    if waarde == 0:
        return (
            "background-color: #ffd6d6; "
            "color: #a40000; "
            "font-weight: bold"
        )

    return ""

def format_budget(waarde):
    if pd.isna(waarde):
        return "-"

    bedrag = f"{waarde:,.0f}".replace(",", ".")
    return f"€ {bedrag}"

stijl = (
    overzicht.style
    .map(kleur_cel, subset=week_kolommen)
    .map(kleur_budget, subset=["Project budget"])
    .format({"Project budget": format_budget})
    .set_properties(
        subset=week_kolommen,
        **{
            "font-size": "9px",
            "text-align": "center",
            "padding": "1px"
        }
    )
)

kolom_config = {
    "Project": st.column_config.TextColumn(
        "Project",
        width=120
    ),
    "Project budget": st.column_config.Column(
        "Budget",
        width=90
    ),
    "Start": st.column_config.TextColumn(
        "Start",
        width=50
    ),
    "Laatste": st.column_config.TextColumn(
        "Laatste",
        width=55
    )
}

for week in week_kolommen:
    kolom_config[week] = st.column_config.TextColumn(
        week,
        width=33
    )

st.caption(
    "Lichtgrijs = nog niet gestart  ·  "
    "Wit = 0 uur  ·  "
    "Donkerder blauw = meer uren  ·  "
    "Grijs = na laatste actieve week  ·  "
    "Rood budget = projectbudget €0"
)

st.dataframe(
    stijl,
    column_config=kolom_config,
    hide_index=True,
    use_container_width=True,
    height=600,
    row_height=28
)