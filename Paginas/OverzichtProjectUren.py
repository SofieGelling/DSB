import streamlit as st
import pandas as pd

st.title("Overzicht projecten")

if "projecturen_schoon" not in st.session_state:
    st.info("Controleer eerst de projecturendata bij Datacontrole.")
    st.stop()

projecturen = st.session_state["projecturen_schoon"].copy()

# Uren en weken voorbereiden
projecturen["Hours"] = pd.to_numeric(projecturen["Hours"], errors="coerce").fillna(0)
projecturen["Week"] = pd.to_numeric(
    projecturen["Week"].astype(str).str.extract(r"(\d+)")[0],
    errors="coerce"
)
projecturen = projecturen.dropna(subset=["Week"])
projecturen["Week"] = projecturen["Week"].astype(int)

uren_per_week = (
    projecturen.groupby(["Project", "Week"])["Hours"]
    .sum()
    .reset_index()
)

weken = range(1, int(projecturen["Week"].max()) + 1)
week_kolommen = [str(w) for w in weken]
projecten = sorted(projecturen["Project"].dropna().unique())

# Projectbudget zoeken
project_budget = None

for waarde in st.session_state.values():
    if isinstance(waarde, pd.DataFrame):
        if "Project" in waarde.columns and (
            "Budget_NL€" in waarde.columns or "Budget_BE€" in waarde.columns
        ):
            project_budget = waarde.copy()
            break

budgetten = {}

if project_budget is not None:
    project_budget["project_match"] = (
        project_budget["Project"].astype(str).str.strip().str.lower()
    )

    for kolom in ["Budget_NL€", "Budget_BE€"]:
        if kolom not in project_budget.columns:
            project_budget[kolom] = pd.NA
        project_budget[kolom] = pd.to_numeric(
            project_budget[kolom], errors="coerce"
        )

    project_budget["Budget"] = (
        project_budget["Budget_NL€"]
        .fillna(project_budget["Budget_BE€"])
    )

    budgetten = (
        project_budget
        .drop_duplicates("project_match")
        .set_index("project_match")["Budget"]
        .to_dict()
    )


def maak_overzicht(status=False, met_budget=False):
    rijen = []

    for project in projecten:
        data = uren_per_week[uren_per_week["Project"] == project]
        actief = data[data["Hours"] > 0]

        start = int(actief["Week"].min()) if not actief.empty else None
        laatste = int(actief["Week"].max()) if not actief.empty else None
        uren = dict(zip(data["Week"], data["Hours"]))

        rij = {"Project": project}

        if met_budget:
            key = str(project).strip().lower()
            rij["Budget"] = budgetten.get(key, pd.NA)

        rij["Start"] = start if start is not None else "-"
        rij["Laatste"] = laatste if laatste is not None else "-"

        for week in weken:
            if start is None or week < start or week > laatste:
                waarde = "NA"
            else:
                uur = uren.get(week, 0)

                if status:
                    waarde = "ACTIEF" if uur > 0 else "0"
                else:
                    waarde = "0" if uur == 0 else f"{uur:.0f}"

            rij[str(week)] = waarde

        rijen.append(rij)

    return pd.DataFrame(rijen)


def kleur_uren(waarde):
    if waarde == "NA":
        return "background-color:#e5e5e5;color:#e5e5e5"

    uren = float(waarde)

    if uren == 0:
        return "background-color:white;color:#666;font-weight:bold"
    if uren <= 30:
        return "background-color:#eaf4ff;color:#24435c"
    if uren <= 50:
        return "background-color:#c9e3fa;color:#183b56"
    if uren <= 70:
        return "background-color:#91c4ed;color:#123653"
    if uren <= 90:
        return "background-color:#559bd0;color:white"

    return "background-color:#21689d;color:white;font-weight:bold"


def kleur_status(waarde):
    if waarde == "ACTIEF":
        return "background-color:#c9e3fa;color:#c9e3fa"
    if waarde == "0":
        return "background-color:white;color:white"
    return "background-color:#e5e5e5;color:#e5e5e5"


def kleur_budget(waarde):
    if pd.notna(waarde) and waarde == 0:
        return "background-color:#ffd6d6;color:#a40000;font-weight:bold"
    return ""


def budget_format(waarde):
    if pd.isna(waarde):
        return "-"
    return f"€ {waarde:,.0f}".replace(",", ".")


def toon_tabel(overzicht, stijl, key, budget=False):
    config = {
        "Project": st.column_config.TextColumn("Project", width=120),
        "Start": st.column_config.TextColumn("Start", width=50),
        "Laatste": st.column_config.TextColumn("Laatste", width=55)
    }

    if budget:
        config["Budget"] = st.column_config.Column("Budget", width=85)

    for week in week_kolommen:
        config[week] = st.column_config.TextColumn(week, width=33)

    selectie = st.dataframe(
        stijl,
        column_config=config,
        hide_index=True,
        use_container_width=True,
        height=600,
        row_height=28,
        on_select="rerun",
        selection_mode="single-row",
        key=key
    )

    if selectie.selection.rows:
        rij = selectie.selection.rows[0]
        st.session_state["geselecteerd_project"] = overzicht.iloc[rij]["Project"]
        st.switch_page("Paginas/OverzichtProjectBezetting.py")


tab_uren, tab_budget = st.tabs(["Projecturen", "Projectbudget"])

with tab_uren:
    overzicht = maak_overzicht()

    stijl = (
        overzicht.style
        .map(kleur_uren, subset=week_kolommen)
        .set_properties(
            subset=week_kolommen,
            **{"font-size": "9px", "text-align": "center", "padding": "1px"}
        )
    )

    st.caption(
        "Per project zie je het aantal geboekte uren per week. "
        "Wit betekent 0 uur; hoe donkerder blauw, hoe meer uren zijn geboekt."
    )

    toon_tabel(overzicht, stijl, "tabel_projecturen")


with tab_budget:
    overzicht = maak_overzicht(status=True, met_budget=True)

    stijl = (
        overzicht.style
        .map(kleur_status, subset=week_kolommen)
        .map(kleur_budget, subset=["Budget"])
        .format({"Budget": budget_format})
    )

    st.caption(
        "Dit overzicht toont het projectbudget en in welke weken aan het project is gewerkt. "
        "Lichtblauw betekent dat er uren zijn geboekt, wit betekent 0 uur binnen de actieve "
        "projectperiode en grijs ligt buiten de actieve periode. "
        "Een ontbrekend budget betekent dat het project niet voorkomt in het projecten- en "
        "budgetoverzicht. Een budget van €0 betekent dat het budget nog niet is vastgesteld."
    )

    toon_tabel(overzicht, stijl, "tabel_projectbudget", budget=True)