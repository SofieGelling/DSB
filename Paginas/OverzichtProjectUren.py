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
    projecturen["Week"]
    .astype(str)
    .str.extract(r"(\d+)")[0],
    errors="coerce"
)

projecturen = projecturen.dropna(
    subset=["Week"]
)

projecturen["Week"] = (
    projecturen["Week"].astype(int)
)

uren_per_week = (
    projecturen
    .groupby(
        ["Project", "Week"]
    )["Hours"]
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
# KOSTEN PER PROJECT PER WEEK
# --------------------------------------------------

project_week_euro = st.session_state.get(
    "project_week_euro"
)

if project_week_euro is not None:

    project_week_euro = (
        project_week_euro.copy()
    )

    project_week_euro["Week"] = (
        pd.to_numeric(
            project_week_euro["Week"],
            errors="coerce"
        )
    )

    project_week_euro = (
        project_week_euro.dropna(
            subset=["Week"]
        )
    )

    project_week_euro["Week"] = (
        project_week_euro["Week"]
        .astype(int)
    )

    project_week_euro["project_match"] = (
        project_week_euro["Project"]
        .astype(str)
        .str.strip()
        .str.lower()
    )


# --------------------------------------------------
# TOTALE KOSTEN PER PROJECT
# --------------------------------------------------

totale_kosten = {}

if project_week_euro is not None:

    totale_kosten = (
        project_week_euro
        .groupby("project_match")["Kosten_EUR"]
        .sum()
        .to_dict()
    )


# --------------------------------------------------
# PROJECTURENOVERZICHT
# --------------------------------------------------

def maak_uren_overzicht():

    rijen = []

    for project in projecten:

        data = uren_per_week[
            uren_per_week["Project"] == project
        ]

        uren = dict(
            zip(
                data["Week"],
                data["Hours"]
            )
        )

        rij = {
            "Project": project
        }

        for week in weken:

            uur = uren.get(
                week,
                0
            )

            rij[str(week)] = (
                "0"
                if uur == 0
                else f"{uur:.0f}"
            )

        rijen.append(rij)

    return pd.DataFrame(rijen)


# --------------------------------------------------
# BUDGETOVERZICHT
# --------------------------------------------------

def maak_budget_overzicht(
    alleen_met_budget=True,
    extra_kolommen=None,
    alleen_waarschuwingen=False
):

    if extra_kolommen is None:
        extra_kolommen = []

    rijen = []

    for project in projecten:

        project_match = (
            str(project)
            .strip()
            .lower()
        )

        budget = budgetten.get(
            project_match,
            pd.NA
        )

        heeft_budget = (
            pd.notna(budget)
            and budget > 0
        )

        # Juiste tabel kiezen
        if (
            alleen_met_budget
            and not heeft_budget
        ):
            continue

        if (
            not alleen_met_budget
            and heeft_budget
        ):
            continue

        kosten = totale_kosten.get(
            project_match,
            pd.NA
        )

        # Totale percentage berekenen
        if (
            heeft_budget
            and pd.notna(kosten)
        ):
            percentage_totaal = (
                kosten / budget * 100
            )
        else:
            percentage_totaal = pd.NA

        # Alleen geel/rode projecten tonen
        if alleen_waarschuwingen:

            if (
                pd.isna(percentage_totaal)
                or percentage_totaal < 90
            ):
                continue

        rij = {
            "Project": project
        }

        # ----------------------------------------------
        # OPTIONELE KOLOMMEN
        # ----------------------------------------------

        if "Budget" in extra_kolommen:
            rij["Budget"] = (
                budget
                if heeft_budget
                else pd.NA
            )

        if "Kosten" in extra_kolommen:
            rij["Kosten"] = kosten

        if "Resterend" in extra_kolommen:

            if (
                heeft_budget
                and pd.notna(kosten)
            ):
                rij["Resterend"] = (
                    budget - kosten
                )
            else:
                rij["Resterend"] = pd.NA

        if "Percentage" in extra_kolommen:
            rij["Percentage"] = percentage_totaal


        # ----------------------------------------------
        # UREN PER WEEK
        # ----------------------------------------------

        uren_project = uren_per_week[
            uren_per_week["Project"] == project
        ]

        uren_dict = dict(
            zip(
                uren_project["Week"],
                uren_project["Hours"]
            )
        )


        # ----------------------------------------------
        # KOSTEN PER WEEK
        # ----------------------------------------------

        kosten_per_week = {}

        if project_week_euro is not None:

            project_kosten = (
                project_week_euro[
                    project_week_euro[
                        "project_match"
                    ] == project_match
                ]
            )

            kosten_per_week = dict(
                zip(
                    project_kosten["Week"],
                    project_kosten["Kosten_EUR"]
                )
            )


        # ----------------------------------------------
        # WEEKVAKJES
        # ----------------------------------------------

        cumulatieve_kosten = 0.0

        for week in weken:

            uur = uren_dict.get(
                week,
                0
            )

            # Project MET budget
            if heeft_budget:

                week_kosten = kosten_per_week.get(
                    week,
                    0
                )

                if pd.notna(week_kosten):
                    cumulatieve_kosten += float(
                        week_kosten
                    )

                if (
                    uur == 0
                    and cumulatieve_kosten == 0
                ):
                    waarde = "-"

                else:

                    percentage = (
                        cumulatieve_kosten
                        / budget
                        * 100
                    )

                    waarde = (
                        f"{percentage:.1f}%"
                    )

            # Project ZONDER budget
            else:

                waarde = (
                    "ACTIEF"
                    if uur > 0
                    else "-"
                )

            rij[str(week)] = waarde

        rijen.append(rij)

    return pd.DataFrame(rijen)


# --------------------------------------------------
# KLEUREN PROJECTUREN
# --------------------------------------------------

def kleur_uren(waarde):

    uren = float(waarde)

    if uren == 0:
        return (
            "background-color:white;"
            "color:#666;"
        )

    if uren <= 30:
        return (
            "background-color:#eaf4ff;"
            "color:#24435c;"
        )

    if uren <= 50:
        return (
            "background-color:#c9e3fa;"
            "color:#183b56;"
        )

    if uren <= 70:
        return (
            "background-color:#91c4ed;"
            "color:#123653;"
        )

    if uren <= 90:
        return (
            "background-color:#559bd0;"
            "color:white;"
        )

    return (
        "background-color:#21689d;"
        "color:white;"
    )


# --------------------------------------------------
# KLEUREN BUDGETPERCENTAGE PER WEEK
# --------------------------------------------------

def kleur_budgetpercentage(waarde):

    waarde = str(waarde)

    if waarde == "-":

        return (
            "background-color:white;"
            "color:#aaa;"
            "font-weight:normal;"
        )

    try:
        percentage = float(
            waarde.replace("%", "")
        )

    except:
        return ""

    # Onder 90% -> één vaste kleur blauw
    if percentage < 90:

        return (
            "background-color:#c9e3fa;"
            "color:#183b56;"
            "font-weight:normal;"
        )

    # 90 t/m 100 -> geel
    if percentage <= 100:

        return (
            "background-color:#fff1a8;"
            "color:#725600;"
            "font-weight:normal;"
        )

    # Boven 100 -> rood
    return (
        "background-color:#ffd6d6;"
        "color:#a40000;"
        "font-weight:normal;"
    )


# --------------------------------------------------
# KLEUR TOTALE PERCENTAGEKOLOM
# --------------------------------------------------

def kleur_percentage_kolom(waarde):

    if pd.isna(waarde):
        return ""

    percentage = float(waarde)

    if percentage < 90:

        return (
            "background-color:#c9e3fa;"
            "color:#183b56;"
            "font-weight:normal;"
        )

    if percentage <= 100:

        return (
            "background-color:#fff1a8;"
            "color:#725600;"
            "font-weight:normal;"
        )

    return (
        "background-color:#ffd6d6;"
        "color:#a40000;"
        "font-weight:normal;"
    )


# --------------------------------------------------
# PROJECT ZONDER BUDGET
# --------------------------------------------------

def kleur_zonder_budget(waarde):

    if waarde == "ACTIEF":

        return (
            "background-color:#c9e3fa;"
            "color:#c9e3fa;"
        )

    return (
        "background-color:white;"
        "color:white;"
    )


# --------------------------------------------------
# FORMATTING
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
    zonder_budget=False,
    volledige_hoogte=False
):

    if overzicht.empty:

        st.info(
            "Geen projecten in deze categorie."
        )
        return


    filter_key = f"{key}_filter"

    filter_projecten = (
        st.session_state.get(
            filter_key,
            []
        )
    )


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


    elif zonder_budget:

        stijl = (
            weergave.style
            .map(
                kleur_zonder_budget,
                subset=week_kolommen
            )
        )


    else:

        stijl = (
            weergave.style
            .map(
                kleur_budgetpercentage,
                subset=week_kolommen
            )
        )


    # Percentagekolom ook kleuren
    if "Percentage" in weergave.columns:

        stijl = stijl.map(
            kleur_percentage_kolom,
            subset=["Percentage"]
        )


    # Geld/percentage formatteren
    format_dict = {}

    for kolom in [
        "Budget",
        "Kosten",
        "Resterend"
    ]:

        if kolom in weergave.columns:
            format_dict[kolom] = geld_format


    if "Percentage" in weergave.columns:
        format_dict["Percentage"] = percentage_format


    if format_dict:

        stijl = stijl.format(
            format_dict
        )


    # Weekpercentages klein
    stijl = stijl.set_properties(
        subset=week_kolommen,
        **{
            "font-size": "8px",
            "font-weight": "normal",
            "text-align": "center",
            "padding": "1px"
        }
    )


    # ----------------------------------------------
    # GESELECTEERDE RIJ
    # ----------------------------------------------

    def markeer_rij(rij):

        if rij.name not in geselecteerde_rijen:

            return [
                ""
            ] * len(rij)


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
                width=130
            )
    }


    if "Budget" in weergave.columns:

        config["Budget"] = (
            st.column_config.Column(
                "Budget",
                width=90
            )
        )


    if "Kosten" in weergave.columns:

        config["Kosten"] = (
            st.column_config.Column(
                "Kosten",
                width=90
            )
        )


    if "Resterend" in weergave.columns:

        config["Resterend"] = (
            st.column_config.Column(
                "Resterend",
                width=90
            )
        )


    if "Percentage" in weergave.columns:

        config["Percentage"] = (
            st.column_config.Column(
                "Percentage",
                width=85
            )
        )


    for week in week_kolommen:

        config[week] = (
            st.column_config.TextColumn(
                week,
                width=45
            )
        )


    # ----------------------------------------------
    # HOOGTE TABEL
    # ----------------------------------------------

    if volledige_hoogte:

        tabel_hoogte = (
            38
            + len(weergave) * 29
        )

    else:

        tabel_hoogte = 450


    acties = st.container()


    selectie = st.dataframe(
        stijl,
        column_config=config,
        hide_index=True,
        use_container_width=True,
        height=tabel_hoogte,
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
        .iloc[
            gekozen_rijen
        ]["Project"]
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

                if len(
                    gekozen_projecten
                ) > 1:

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

    overzicht_uren = (
        maak_uren_overzicht()
    )

    st.caption(
        "Per project zie je het aantal geboekte uren per week."
    )

    toon_tabel(
        overzicht_uren,
        "tabel_projecturen",
        soort="uren"
    )


# --------------------------------------------------
# TAB PROJECTBUDGET
# --------------------------------------------------

with tab_budget:

    if project_week_euro is None:

        st.info(
            "Ga eerst naar Datacontrole → Koppeling werknemers "
            "om de projectkosten te berekenen."
        )


    # --------------------------------------------------
    # OPTIONELE KOLOMMEN
    # --------------------------------------------------

    gekozen_kolommen = st.multiselect(
        "Extra kolommen tonen",
        [
            "Budget",
            "Kosten",
            "Resterend",
            "Percentage"
        ],
        default=st.session_state.get(
            "budget_extra_kolommen",
            []
        ),
        key="budget_kolommen_keuze"
    )


    if st.button(
        "Kolommen toepassen",
        key="budget_kolommen_knop"
    ):

        st.session_state[
            "budget_extra_kolommen"
        ] = gekozen_kolommen

        st.rerun()


    extra_kolommen = (
        st.session_state.get(
            "budget_extra_kolommen",
            []
        )
    )


    st.divider()


    # --------------------------------------------------
    # PROJECTEN MET BUDGET
    # --------------------------------------------------

    st.subheader(
        "Projecten met vastgesteld budget"
    )


    if "budget_waarschuwingen" not in st.session_state:

        st.session_state[
            "budget_waarschuwingen"
        ] = False


    col1, col2 = st.columns(
        [1, 4]
    )


    with col1:

        if not st.session_state[
            "budget_waarschuwingen"
        ]:

            if st.button(
                "Toon alleen geel/rood"
            ):

                st.session_state[
                    "budget_waarschuwingen"
                ] = True

                st.rerun()

        else:

            if st.button(
                "Toon alle projecten"
            ):

                st.session_state[
                    "budget_waarschuwingen"
                ] = False

                st.rerun()


    with col2:

        if st.session_state[
            "budget_waarschuwingen"
        ]:

            st.warning(
                "Je ziet nu alleen projecten waarbij "
                "90% of meer van het budget is gebruikt."
            )


    st.caption(
        "De percentages in de weekvakjes zijn cumulatief. "
        "Onder 90% is blauw, 90–100% geel en boven 100% rood."
    )


    overzicht_met_budget = (
        maak_budget_overzicht(
            alleen_met_budget=True,
            extra_kolommen=extra_kolommen,
            alleen_waarschuwingen=(
                st.session_state[
                    "budget_waarschuwingen"
                ]
            )
        )
    )


    toon_tabel(
        overzicht_met_budget,
        "tabel_met_budget",
        soort="budget",
        volledige_hoogte=True
    )


    st.divider()


    # --------------------------------------------------
    # PROJECTEN ZONDER BUDGET
    # --------------------------------------------------

    st.subheader(
        "Projecten zonder vastgesteld budget"
    )

    st.caption(
        "Deze projecten hebben geen budget of een budget van €0. "
        "Een blauw vakje betekent dat in die week uren zijn geboekt."
    )


    overzicht_zonder_budget = (
        maak_budget_overzicht(
            alleen_met_budget=False,
            extra_kolommen=extra_kolommen
        )
    )


    toon_tabel(
        overzicht_zonder_budget,
        "tabel_zonder_budget",
        soort="budget",
        zonder_budget=True
    )