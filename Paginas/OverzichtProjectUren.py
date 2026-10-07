import streamlit as st
import pandas as pd

st.title("Overzicht projecten")


# --------------------------------------------------
# CONTROLEREN OF PROJECTUREN BESCHIKBAAR ZIJN
# --------------------------------------------------

if "projecturen_schoon" not in st.session_state:
    st.info("Controleer eerst de projecturendata bij Datacontrole.")
    st.stop()


projecturen = st.session_state["projecturen_schoon"].copy()


# --------------------------------------------------
# PROJECTUREN VOORBEREIDEN
# --------------------------------------------------

projecturen["Hours"] = pd.to_numeric(
    projecturen["Hours"],
    errors="coerce"
).fillna(0)

projecturen["Week"] = pd.to_numeric(
    projecturen["Week"].astype(str).str.extract(r"(\d+)")[0],
    errors="coerce"
)

projecturen = projecturen.dropna(subset=["Week"])

projecturen["Week"] = projecturen["Week"].astype(int)


uren_per_week = (
    projecturen
    .groupby(["Project", "Week"])["Hours"]
    .sum()
    .reset_index()
)


weken = range(
    1,
    int(projecturen["Week"].max()) + 1
)

week_kolommen = [
    str(w) for w in weken
]

projecten = sorted(
    projecturen["Project"]
    .dropna()
    .unique()
)


# --------------------------------------------------
# BUDGETDATA
# --------------------------------------------------

project_budget = st.session_state.get(
    "project_budget_schoon",
    st.session_state.get("project_budget")
)

budgetten = {}

if project_budget is not None:

    project_budget = project_budget.copy()

    project_budget["project_match"] = (
        project_budget["Project"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    for kolom in [
        "Budget_NL€",
        "Budget_BE€"
    ]:

        if kolom not in project_budget.columns:
            project_budget[kolom] = pd.NA

        project_budget[kolom] = pd.to_numeric(
            project_budget[kolom],
            errors="coerce"
        )

    project_budget["Budget"] = (
        project_budget["Budget_NL€"]
        .fillna(
            project_budget["Budget_BE€"]
        )
    )

    budgetten = (
        project_budget
        .drop_duplicates("project_match")
        .set_index("project_match")["Budget"]
        .to_dict()
    )


# --------------------------------------------------
# BEREKENDE KOSTEN
# --------------------------------------------------

budget_overzicht = st.session_state.get(
    "budget_overzicht"
)

kosten_info = {}

if budget_overzicht is not None:

    budget_overzicht = budget_overzicht.copy()

    budget_overzicht["project_match"] = (
        budget_overzicht["Project"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    kosten_info = (
        budget_overzicht
        .drop_duplicates("project_match")
        .set_index("project_match")
        .to_dict("index")
    )


# --------------------------------------------------
# OVERZICHT MAKEN
# --------------------------------------------------

def maak_overzicht(status=False, met_budget=False):

    rijen = []

    for project in projecten:

        data = uren_per_week[
            uren_per_week["Project"] == project
        ]

        actief = data[
            data["Hours"] > 0
        ]

        start = (
            int(actief["Week"].min())
            if not actief.empty
            else None
        )

        laatste = (
            int(actief["Week"].max())
            if not actief.empty
            else None
        )

        uren = dict(
            zip(
                data["Week"],
                data["Hours"]
            )
        )

        project_match = (
            str(project)
            .strip()
            .lower()
        )

        rij = {
            "Project": project
        }


        # ----------------------------------------------
        # BUDGET EN KOSTEN
        # ----------------------------------------------

        if met_budget:

            rij["Budget"] = budgetten.get(
                project_match,
                pd.NA
            )

            info = kosten_info.get(
                project_match,
                {}
            )

            rij["Kosten"] = info.get(
                "Totale_kosten_EUR",
                pd.NA
            )

            rij["Resterend"] = info.get(
                "Resterend_budget",
                pd.NA
            )

            rij["Gebruikt %"] = info.get(
                "Budget_gebruikt_%",
                pd.NA
            )

            rij["Status"] = info.get(
                "Status",
                "Nog niet berekend"
            )


        rij["Start"] = (
            start
            if start is not None
            else "-"
        )

        rij["Laatste"] = (
            laatste
            if laatste is not None
            else "-"
        )


        # ----------------------------------------------
        # WEEKSTATUS
        # ----------------------------------------------

        for week in weken:

            if (
                start is None
                or week < start
                or week > laatste
            ):
                waarde = "NA"

            else:

                uur = uren.get(
                    week,
                    0
                )

                if status:

                    waarde = (
                        "ACTIEF"
                        if uur > 0
                        else "0"
                    )

                else:

                    waarde = (
                        "0"
                        if uur == 0
                        else f"{uur:.0f}"
                    )

            rij[str(week)] = waarde

        rijen.append(rij)

    return pd.DataFrame(rijen)


# --------------------------------------------------
# KLEUREN UREN
# --------------------------------------------------

def kleur_uren(waarde):

    if waarde == "NA":
        return (
            "background-color:#e5e5e5;"
            "color:#e5e5e5"
        )

    uren = float(waarde)

    if uren == 0:
        return (
            "background-color:white;"
            "color:#666;"
            "font-weight:bold"
        )

    if uren <= 30:
        return (
            "background-color:#eaf4ff;"
            "color:#24435c"
        )

    if uren <= 50:
        return (
            "background-color:#c9e3fa;"
            "color:#183b56"
        )

    if uren <= 70:
        return (
            "background-color:#91c4ed;"
            "color:#123653"
        )

    if uren <= 90:
        return (
            "background-color:#559bd0;"
            "color:white"
        )

    return (
        "background-color:#21689d;"
        "color:white;"
        "font-weight:bold"
    )


# --------------------------------------------------
# KLEUREN WEEKSTATUS
# --------------------------------------------------

def kleur_status_week(waarde):

    if waarde == "ACTIEF":
        return (
            "background-color:#c9e3fa;"
            "color:#c9e3fa"
        )

    if waarde == "0":
        return (
            "background-color:white;"
            "color:white"
        )

    return (
        "background-color:#e5e5e5;"
        "color:#e5e5e5"
    )


# --------------------------------------------------
# KLEUREN BUDGET
# --------------------------------------------------

def kleur_budget(waarde):

    if (
        pd.notna(waarde)
        and waarde == 0
    ):
        return (
            "background-color:#ffd6d6;"
            "color:#a40000;"
            "font-weight:bold"
        )

    return ""


# --------------------------------------------------
# KLEUREN STATUS
# --------------------------------------------------

def kleur_projectstatus(waarde):

    if waarde == "Budget overschreden":
        return (
            "background-color:#ffd6d6;"
            "color:#a40000;"
            "font-weight:bold"
        )

    if waarde == "Bijna budget bereikt":
        return (
            "background-color:#fff1c2;"
            "font-weight:bold"
        )

    if waarde in [
        "Budget ontbreekt",
        "Budget niet vastgesteld",
        "Nog niet berekend"
    ]:
        return (
            "background-color:#eeeeee;"
            "color:#666"
        )

    if waarde == "OK":
        return (
            "background-color:#dff2df;"
            "color:#245b24"
        )

    return ""


# --------------------------------------------------
# FORMAT GELDBEDRAGEN
# --------------------------------------------------

def geld_format(waarde):

    if pd.isna(waarde):
        return "-"

    return (
        f"€ {waarde:,.0f}"
        .replace(",", ".")
    )


def percentage_format(waarde):

    if pd.isna(waarde):
        return "-"

    return f"{waarde:.1f}%"


# --------------------------------------------------
# SELECTIE OPHALEN
# --------------------------------------------------

def selectie_ophalen(key):

    try:
        return st.session_state[
            key
        ]["selection"]["rows"]

    except:
        return []


# --------------------------------------------------
# TABEL TONEN
# --------------------------------------------------

def toon_tabel(
    overzicht,
    key,
    soort="uren",
    budget=False
):

    filter_key = f"{key}_filter"

    filter_projecten = (
        st.session_state.get(
            filter_key,
            []
        )
    )


    # Alleen geselecteerde projecten
    if filter_projecten:

        weergave = overzicht[
            overzicht["Project"].isin(
                filter_projecten
            )
        ].reset_index(drop=True)

        widget_key = (
            f"{key}_vergelijk"
        )

    else:

        weergave = overzicht.reset_index(
            drop=True
        )

        widget_key = (
            f"{key}_alles"
        )


    geselecteerde_rijen = (
        selectie_ophalen(
            widget_key
        )
    )


    # ----------------------------------------------
    # STYLING
    # ----------------------------------------------

    if soort == "uren":

        stijl = (
            weergave.style
            .map(
                kleur_uren,
                subset=week_kolommen
            )
        )

    else:

        stijl = (
            weergave.style
            .map(
                kleur_status_week,
                subset=week_kolommen
            )
            .map(
                kleur_budget,
                subset=["Budget"]
            )
            .map(
                kleur_projectstatus,
                subset=["Status"]
            )
            .format(
                {
                    "Budget": geld_format,
                    "Kosten": geld_format,
                    "Resterend": geld_format,
                    "Gebruikt %": percentage_format
                }
            )
        )


    stijl = stijl.set_properties(
        subset=week_kolommen,
        **{
            "font-size": "9px",
            "text-align": "center",
            "padding": "1px"
        }
    )


    # ----------------------------------------------
    # GESELECTEERDE RIJ MARKEREN
    # ----------------------------------------------

    def markeer_rij(rij):

        if rij.name not in geselecteerde_rijen:
            return [""] * len(rij)

        opmaak = [
            "border-top:2px solid #2878b5;"
            "border-bottom:2px solid #2878b5;"
        ] * len(rij)

        opmaak[0] += (
            "border-left:2px solid #2878b5;"
        )

        opmaak[-1] += (
            "border-right:2px solid #2878b5;"
        )

        return opmaak


    stijl = stijl.apply(
        markeer_rij,
        axis=1
    )


    # ----------------------------------------------
    # KOLOMCONFIGURATIE
    # ----------------------------------------------

    config = {

        "Project":
            st.column_config.TextColumn(
                "Project",
                width=120
            ),

        "Start":
            st.column_config.TextColumn(
                "Start",
                width=50
            ),

        "Laatste":
            st.column_config.TextColumn(
                "Laatste",
                width=55
            )
    }


    if budget:

        config["Budget"] = (
            st.column_config.Column(
                "Budget",
                width=90
            )
        )

        config["Kosten"] = (
            st.column_config.Column(
                "Kosten",
                width=90
            )
        )

        config["Resterend"] = (
            st.column_config.Column(
                "Resterend",
                width=95
            )
        )

        config["Gebruikt %"] = (
            st.column_config.Column(
                "Gebruikt %",
                width=80
            )
        )

        config["Status"] = (
            st.column_config.TextColumn(
                "Status",
                width=150
            )
        )


    for week in week_kolommen:

        config[week] = (
            st.column_config.TextColumn(
                week,
                width=33
            )
        )


    # Container boven tabel
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


    gekozen_rijen = (
        selectie.selection.rows
    )


    gekozen_projecten = (

        weergave
        .iloc[gekozen_rijen]["Project"]
        .tolist()

        if gekozen_rijen

        else []
    )


    # ----------------------------------------------
    # ACTIES
    # ----------------------------------------------

    with acties:

        if filter_projecten:

            col1, col2 = st.columns(
                [4, 1]
            )

            with col1:

                st.info(
                    f"Je vergelijkt "
                    f"{len(filter_projecten)} projecten."
                )

            with col2:

                if st.button(
                    "Toon alles",
                    key=f"{key}_alles_knop"
                ):

                    st.session_state[
                        filter_key
                    ] = []

                    st.rerun()


        if gekozen_projecten:

            col1, col2, col3 = (
                st.columns(
                    [2, 1, 1]
                )
            )

            with col1:

                project_keuze = (
                    st.selectbox(
                        "Project bekijken",
                        gekozen_projecten,
                        key=(
                            f"{key}_project_keuze"
                        )
                    )
                )

            with col2:

                st.write("")
                st.write("")

                if st.button(
                    "Bekijk project",
                    key=f"{key}_bekijk"
                ):

                    st.session_state[
                        "geselecteerd_project"
                    ] = project_keuze

                    st.switch_page(
                        "Paginas/OverzichtProjectBezetting.py"
                    )

            with col3:

                st.write("")
                st.write("")

                if (
                    len(
                        gekozen_projecten
                    ) > 1
                ):

                    if st.button(
                        "Vergelijk selectie",
                        key=(
                            f"{key}_vergelijk_knop"
                        )
                    ):

                        st.session_state[
                            filter_key
                        ] = gekozen_projecten

                        st.rerun()


# --------------------------------------------------
# TABS
# --------------------------------------------------

tab_uren, tab_budget = st.tabs([
    "Projecturen",
    "Projectbudget"
])


# --------------------------------------------------
# TAB PROJECTUREN
# --------------------------------------------------

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


# --------------------------------------------------
# TAB PROJECTBUDGET
# --------------------------------------------------

with tab_budget:

    if budget_overzicht is None:

        st.info(
            "Ga eerst naar Datacontrole → Koppeling werknemers "
            "om de projectkosten te berekenen."
        )

    overzicht = maak_overzicht(
        status=True,
        met_budget=True
    )

    st.caption(
        "Hier zie je per project het budget, de berekende kosten tot nu toe, "
        "het resterende budget en het percentage dat al is gebruikt. "
        "Lichtblauw betekent dat in die week uren zijn geboekt. "
        "Een rood statusveld betekent dat het budget is overschreden."
    )

    toon_tabel(
        overzicht,
        "tabel_projectbudget",
        soort="budget",
        budget=True
    )