import streamlit as st
import pandas as pd

st.title("Overzicht projecten")

if "projecturen_schoon" not in st.session_state:
    st.info("Controleer eerst de projecturendata bij Datacontrole.")
    st.stop()

projecturen = st.session_state["projecturen_schoon"].copy()

# Data voorbereiden
projecturen["Hours"] = pd.to_numeric(projecturen["Hours"], errors="coerce").fillna(0)
projecturen["Week"] = pd.to_numeric(
    projecturen["Week"].astype(str).str.extract(r"(\d+)")[0],
    errors="coerce"
)
projecturen = projecturen.dropna(subset=["Week"])
projecturen["Week"] = projecturen["Week"].astype(int)

uren_per_week = (
    projecturen.groupby(["Project", "Week"])["Hours"]
    .sum().reset_index()
)

weken = range(1, int(projecturen["Week"].max()) + 1)
week_kolommen = [str(w) for w in weken]
projecten = sorted(projecturen["Project"].dropna().unique())

# Budgetdata zoeken
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
        project_budget.drop_duplicates("project_match")
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
            rij["Budget"] = budgetten.get(
                str(project).strip().lower(), pd.NA
            )

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


def selectie_ophalen(key):
    try:
        return st.session_state[key]["selection"]["rows"]
    except:
        return []


def toon_tabel(overzicht, key, soort="uren", budget=False):
    filter_key = f"{key}_filter"
    filter_projecten = st.session_state.get(filter_key, [])

    # Bij vergelijken alleen geselecteerde projecten tonen
    if filter_projecten:
        weergave = overzicht[
            overzicht["Project"].isin(filter_projecten)
        ].reset_index(drop=True)
        widget_key = f"{key}_vergelijk"
    else:
        weergave = overzicht.reset_index(drop=True)
        widget_key = f"{key}_alles"

    geselecteerde_rijen = selectie_ophalen(widget_key)

    # Styling
    if soort == "uren":
        stijl = weergave.style.map(kleur_uren, subset=week_kolommen)
    else:
        stijl = (
            weergave.style
            .map(kleur_status, subset=week_kolommen)
            .map(kleur_budget, subset=["Budget"])
            .format({"Budget": budget_format})
        )

    stijl = stijl.set_properties(
        subset=week_kolommen,
        **{
            "font-size": "9px",
            "text-align": "center",
            "padding": "1px"
        }
    )

    # Blauwe rand rond geselecteerde rij
    def markeer_rij(rij):
        if rij.name not in geselecteerde_rijen:
            return [""] * len(rij)

        opmaak = [
            "border-top:2px solid #2878b5;"
            "border-bottom:2px solid #2878b5;"
        ] * len(rij)

        opmaak[0] += "border-left:2px solid #2878b5;"
        opmaak[-1] += "border-right:2px solid #2878b5;"
        return opmaak

    stijl = stijl.apply(markeer_rij, axis=1)

    config = {
        "Project": st.column_config.TextColumn("Project", width=120),
        "Start": st.column_config.TextColumn("Start", width=50),
        "Laatste": st.column_config.TextColumn("Laatste", width=55)
    }

    if budget:
        config["Budget"] = st.column_config.Column("Budget", width=85)

    for week in week_kolommen:
        config[week] = st.column_config.TextColumn(week, width=33)

    # Deze container staat boven de tabel
    acties = st.container()

    selectie = st.dataframe(
        stijl,
        column_config=config,
        hide_index=True,
        use_container_width=True,
        height=600,
        row_height=28,
        on_select="rerun",
        selection_mode="multi-row",
        key=widget_key
    )

    gekozen_rijen = selectie.selection.rows

    gekozen_projecten = (
        weergave.iloc[gekozen_rijen]["Project"].tolist()
        if gekozen_rijen else []
    )

    # Opties boven tabel
    with acties:
        if filter_projecten:
            col1, col2 = st.columns([4, 1])

            with col1:
                st.info(
                    f"Je vergelijkt {len(filter_projecten)} projecten."
                )

            with col2:
                if st.button("Toon alles", key=f"{key}_alles_knop"):
                    st.session_state[filter_key] = []
                    st.rerun()

        if gekozen_projecten:
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                project_keuze = st.selectbox(
                    "Project bekijken",
                    gekozen_projecten,
                    key=f"{key}_project_keuze"
                )

            with col2:
                st.write("")
                st.write("")

                if st.button("Bekijk project", key=f"{key}_bekijk"):
                    st.session_state["geselecteerd_project"] = project_keuze
                    st.switch_page(
                        "Paginas/OverzichtProjectBezetting.py"
                    )

            with col3:
                st.write("")
                st.write("")

                if len(gekozen_projecten) > 1:
                    if st.button(
                        "Vergelijk selectie",
                        key=f"{key}_vergelijk_knop"
                    ):
                        st.session_state[filter_key] = gekozen_projecten
                        st.rerun()


tab_uren, tab_budget = st.tabs([
    "Projecturen",
    "Projectbudget"
])

with tab_uren:
    overzicht = maak_overzicht()

    st.caption(
        "Per project zie je het aantal geboekte uren per week. "
        "Wit betekent 0 uur; hoe donkerder blauw, hoe meer uren zijn geboekt. "
        "Selecteer één of meerdere projecten om ze te bekijken of te vergelijken."
    )

    toon_tabel(
        overzicht,
        "tabel_projecturen",
        soort="uren"
    )


with tab_budget:
    overzicht = maak_overzicht(
        status=True,
        met_budget=True
    )

    st.caption(
        "Dit overzicht toont het projectbudget en in welke weken aan het project is gewerkt. "
        "Lichtblauw betekent dat er uren zijn geboekt, wit betekent 0 uur en grijs ligt "
        "buiten de actieve projectperiode. Een ontbrekend budget betekent dat het project "
        "niet voorkomt in het projecten- en budgetoverzicht. Een budget van €0 betekent "
        "dat het budget nog niet is vastgesteld."
    )

    toon_tabel(
        overzicht,
        "tabel_projectbudget",
        soort="budget",
        budget=True
    )