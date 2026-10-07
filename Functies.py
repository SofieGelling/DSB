import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import re


def bestanden_inlezen(titel, uitleg, key):

    st.subheader(titel)
    st.write(uitleg)

    bestanden = st.file_uploader(
        f"Upload bestanden voor {titel}",
        type=["csv", "xlsx", "txt"],
        accept_multiple_files=True,
        key=key
    )

    if bestanden:
        datasets = []

        for bestand in bestanden:

            try:
                # CSV
                if bestand.name.endswith(".csv"):
                    df = pd.read_csv(bestand,sep=None,engine="python")

                # Excel
                elif bestand.name.endswith(".xlsx"):
                    df = pd.read_excel(bestand)

                # TXT
                elif bestand.name.endswith(".txt"):
                    df = pd.read_csv(
                        bestand,
                        sep=None,
                        engine="python"
                    )

                # Uit welk bestand komt iedere rij
                df["Bronbestand"] = bestand.name

                datasets.append(df)

            except Exception as fout:
                st.error(
                    f"Bestand '{bestand.name}' kon niet worden ingelezen: {fout}"
                )

        # Alleen samenvoegen als er minimaal één bestand goed is ingelezen
        if datasets:

            data = pd.concat(
                datasets,
                ignore_index=True
            )

            st.success(
                f"{len(datasets)} bestanden succesvol ingelezen."
            )

            st.write(
                f"Totaal aantal rijen: {len(data)}"
            )

            st.dataframe(data)

            return data

    return None

def inlezen_employee_bestanden(titel, uitleg, key):
    st.subheader(titel)
    st.write(uitleg)

    bestanden = st.file_uploader(
        f"Upload bestanden voor {titel}",
        type=["csv", "xlsx", "txt"],
        accept_multiple_files=True,
        key=key
    )

    if bestanden:
        datasets = []

        employee_kolommen = [
            "Work Location", "Full Name", "Empl. Nr", "Gender",
            "Residence", "Date of Birth", "Annual Salary",
            "Contract Start Date", "Contract End Date",
            "Grade", "Contract"
        ]

        for bestand in bestanden:
            try:
                naam = bestand.name
                naam_laag = naam.lower()

                if "tilburg" in naam_laag:
                    df = pd.read_csv(bestand, sep=";", header=None)
                    df = df.iloc[:, 1:]
                    df = df.dropna(axis=1, how="all")

                    if df.shape[1] != 11:
                        raise ValueError(
                            f"Tilburg-bestand heeft {df.shape[1]} kolommen in plaats van 11."
                        )

                    df.columns = [
                        "Full Name", "Empl. Nr", "Gender", "Residence",
                        "Date of Birth", "Annual Salary", "Work Location",
                        "Contract Start Date", "Contract End Date",
                        "Grade", "Contract"
                    ]

                elif "management" in naam_laag:
                    df = pd.read_csv(bestand, sep=";", skiprows=1)

                elif naam_laag.endswith(".xlsx"):
                    df = pd.read_excel(bestand)

                elif naam_laag.endswith((".csv", ".txt")):
                    df = pd.read_csv(bestand, sep=None, engine="python")

                df.columns = df.columns.astype(str).str.strip()
                df = df.loc[:, ~df.columns.str.startswith("Unnamed")]

                if "Row" in df.columns:
                    df = df.drop(columns=["Row"])

                df = df.rename(columns={
                    "Employee Nr": "Empl. Nr",
                    "Contract.": "Contract"
                })

                if "Full Name" not in df.columns or "Empl. Nr" not in df.columns:
                    raise ValueError(
                        f"Kolommen niet goed herkend. Gevonden kolommen: {list(df.columns)}"
                    )

                for kolom in employee_kolommen:
                    if kolom not in df.columns:
                        df[kolom] = None

                df = df[employee_kolommen]
                df["Bronbestand"] = naam
                datasets.append(df)

            except Exception as fout:
                st.error(f"Bestand '{bestand.name}' kon niet worden ingelezen: {fout}")

        if datasets:
            data = pd.concat(datasets, ignore_index=True)

            st.success(f"{len(datasets)} employee-bestanden succesvol ingelezen.")
            st.write(f"Totaal aantal werknemers: {len(data)}")
            st.dataframe(data)

            return data

    return None

def controle_data(data, naam):

    if data is None:
        st.info(f"Er is nog geen data ingelezen voor {naam}.")
        return
    # Aantal rijen weergeven 
    st.write(f"Aantal rijen: {len(data)}")

    # Bronbestand niet meenemen bij controle op duplicaten
    controle_kolommen = data.columns.tolist()
    if "Bronbestand" in controle_kolommen: controle_kolommen.remove("Bronbestand")

    # Dubbele rijen zoeken
    dubbele_rijen = data[data.duplicated(subset=controle_kolommen,keep=False)].copy()

    st.subheader("Dubbele rijen")
    if dubbele_rijen.empty:
        st.success("Geen dubbele rijen gevonden.")

        # Data ongewijzigd bewaren
        st.session_state[f"{naam}_schoon"] = data.copy()

    else:
        st.error(
            f"Er zijn {len(dubbele_rijen)} rijen gevonden "
            "die onderdeel zijn van een duplicaat. "
            "Voor de volgende stappen wordt per duplicaatgroep "
            "één rij behouden en worden de overige exemplaren verwijderd.")

        # Nummer geven aan iedere groep identieke rijen
        dubbele_rijen["Duplicaatgroep"] = (dubbele_rijen.groupby(controle_kolommen,dropna=False).ngroup() + 1)

        # Dezelfde dubbele rijen bij elkaar zetten
        dubbele_rijen = dubbele_rijen.sort_values("Duplicaatgroep")

        st.dataframe(
            dubbele_rijen[["Duplicaatgroep", "Bronbestand"] + controle_kolommen],
            use_container_width=True,
            hide_index=True)

        data_schoon = data.drop_duplicates(
            subset=controle_kolommen,
            keep="first").copy()

        aantal_verwijderd = len(data) - len(data_schoon)
        st.write(f"Er worden {aantal_verwijderd} dubbele rijen verwijderd.")

        # Opslaan 
        st.session_state[f"{naam}_schoon"] = data_schoon

def overzicht_projecten(projecturen):
    projecturen = projecturen.copy()
    projecturen["Week"] = pd.to_numeric(projecturen["Week"], errors="coerce")
    projecturen["Hours"] = pd.to_numeric(projecturen["Hours"], errors="coerce")
    projecturen = projecturen.dropna(subset=["Week", "Hours"])

    laatste_week = int(projecturen["Week"].max())

    uren_per_week = (
        projecturen
        .groupby(["Project", "Week"])["Hours"]
        .sum()
        .reset_index()
    )

    totaal_per_project = (
        uren_per_week
        .groupby("Project")["Hours"]
        .sum()
        .reset_index()
    )

    alle_projecten = totaal_per_project["Project"].tolist()

    geselecteerde_projecten = st.multiselect(
        "Selecteer projecten",
        options=alle_projecten,
        default=alle_projecten
    )

    totaal_per_project = totaal_per_project[
        totaal_per_project["Project"].isin(geselecteerde_projecten)
    ]

    sortering = st.selectbox(
        "Sorteer projecten op totaal aantal uren",
        ["Hoog naar laag", "Laag naar hoog"]
    )

    totaal_per_project = totaal_per_project.sort_values(
        "Hours",
        ascending=sortering == "Laag naar hoog"
    )

    projecten = totaal_per_project["Project"].tolist()

    if len(projecten) == 0:
        st.warning("Selecteer minimaal één project.")
        return

    # Opslaan welke grafiek groot moet worden
    if "groot_project" not in st.session_state:
        st.session_state["groot_project"] = None

    groot_project = st.session_state["groot_project"]

    # Grote grafiek
    if groot_project is not None:
        data_project = uren_per_week[
            uren_per_week["Project"] == groot_project
        ].sort_values("Week")

        totaal_uren = data_project["Hours"].sum()

        fig, ax = plt.subplots(figsize=(14, 5))

        ax.plot(
            data_project["Week"],
            data_project["Hours"],
            marker="o"
        )

        ax.set_title(
            f"{groot_project} - Totaal: {totaal_uren:.1f} uur"
        )
        ax.set_xlabel("Week")
        ax.set_ylabel("Aantal uur")
        ax.set_xlim(0, laatste_week)
        ax.grid(True)

        st.pyplot(fig)
        plt.close(fig)

        if st.button("Verklein", key="verklein"):
            st.session_state["groot_project"] = None
            st.rerun()

        st.divider()

    # Kleine grafieken, 3 naast elkaar
    for i in range(0, len(projecten), 3):
        drie_projecten = projecten[i:i+3]
        kolommen = st.columns(3)

        for j, project in enumerate(drie_projecten):
            with kolommen[j]:
                data_project = uren_per_week[
                    uren_per_week["Project"] == project
                ].sort_values("Week")

                totaal_uren = data_project["Hours"].sum()

                fig, ax = plt.subplots(figsize=(6, 4))

                ax.plot(
                    data_project["Week"],
                    data_project["Hours"],
                    marker="o"
                )

                ax.set_title(
                    f"{project}\nTotaal: {totaal_uren:.1f} uur"
                )
                ax.set_xlabel("Week")
                ax.set_ylabel("Aantal uur")
                ax.set_xlim(0, laatste_week)
                ax.grid(True)

                st.pyplot(fig, use_container_width=True)
                plt.close(fig)

                if st.button("🔍 Vergroot", key=f"vergroot_{project}"):
                    st.session_state["groot_project"] = project
                    st.rerun()

def missende_waarden(data):

    st.subheader("Missende waarden")

    # Kopie maken zodat we de originele data niet aanpassen
    controle_data = data.copy()

    budget_kolommen = ["Budget_NL€", "Budget_BE€"]

    # ---------------------------------------------------------
    # NORMALE MISSENDE WAARDEN
    # ---------------------------------------------------------

    # Budgetkolommen niet afzonderlijk als fout tellen
    normale_kolommen = [
        kolom for kolom in controle_data.columns
        if kolom not in budget_kolommen
    ]

    missende_per_kolom = (
        controle_data[normale_kolommen]
        .isna()
        .sum()
    )

    # Alleen kolommen waar echt waarden ontbreken
    missende_per_kolom = missende_per_kolom[
        missende_per_kolom > 0
    ]

    # Rijen waarin een gewone waarde ontbreekt
    rijen_missend = controle_data[
        controle_data[normale_kolommen]
        .isna()
        .any(axis=1)
    ]


    # ---------------------------------------------------------
    # BUDGETCONTROLE
    # ---------------------------------------------------------

    rijen_budget_missend = pd.DataFrame()

    # Alleen uitvoeren als beide budgetkolommen bestaan
    if all(kolom in controle_data.columns for kolom in budget_kolommen):

        budget_fout = (
            controle_data["Budget_NL€"].isna()
            &
            controle_data["Budget_BE€"].isna()
        )

        rijen_budget_missend = controle_data[budget_fout]


    # ---------------------------------------------------------
    # RESULTAAT TONEN
    # ---------------------------------------------------------

    if missende_per_kolom.empty and rijen_budget_missend.empty:

        st.success("Er zijn geen missende waarden gevonden.")

    else:

        st.warning("Er zijn missende waarden gevonden.")

        # Overzicht normale missende waarden
        if not missende_per_kolom.empty:

            st.write("Aantal missende waarden per kolom:")

            st.dataframe(
                missende_per_kolom
                .reset_index()
                .rename(
                    columns={
                        "index": "Kolom",
                        0: "Aantal missende waarden"
                    }
                )
            )

            st.write("Rijen met missende waarden:")

            st.dataframe(rijen_missend)


        # Budgetcontrole
        if not rijen_budget_missend.empty:

            st.write(
                "Rijen waarbij zowel Budget_NL€ als Budget_BE€ ontbreekt:"
            )

            st.dataframe(rijen_budget_missend)

def maak_naam_match(naam):
    if pd.isna(naam):
        return ""

    naam = str(naam).lower()
    naam = naam.replace("\xa0", " ").strip()
    naam = naam.lstrip(";").strip()

    # Alles na komma of streepje verwijderen
    naam = re.split(r"[,–—-]", naam)[0]

    # Dubbele spaties verwijderen
    naam = " ".join(naam.split())

    return naam

def contract_factor(contract):
    if pd.isna(contract):
        return pd.NA

    contract = str(contract).upper().replace("FTE", "").strip()

    try:
        return float(contract)
    except:
        return pd.NA

def bereken_projectkosten(projecturen, employees, uurtarieven):
    data = projecturen.copy()
    werknemers = employees.copy()
    tarieven = uurtarieven.copy()

    # Hours numeriek maken
    data["Hours"] = pd.to_numeric(
        data["Hours"],
        errors="coerce"
    ).fillna(0)

    # Weeknummer numeriek maken
    data["Week"] = pd.to_numeric(
        data["Week"].astype(str).str.extract(r"(\d+)")[0],
        errors="coerce"
    )

    data = data.dropna(
        subset=["Project", "Week", "Consultant"]
    )

    data["Week"] = data["Week"].astype(int)

    # Namen in beide bestanden schoonmaken
    data["naam_match"] = data["Consultant"].apply(maak_naam_match)
    werknemers["naam_match"] = werknemers["Full Name"].apply(maak_naam_match)

    # Uren per project, week en persoon
    uren_per_persoon = (
        data.groupby(
            ["Project", "Week", "naam_match"],
            as_index=False
        )
        .agg(
            Consultant=("Consultant", "first"),
            Hours=("Hours", "sum")
        )
    )

    # Werknemersgegevens koppelen
    employee_info = werknemers[
        [
            "naam_match",
            "Full Name",
            "Residence",
            "Grade",
            "Annual Salary",
            "Contract"
        ]
    ].drop_duplicates("naam_match")

    uren_per_persoon = uren_per_persoon.merge(
        employee_info,
        on="naam_match",
        how="left"
    )

    # --------------------------------------------------
    # LAND BEPALEN
    # --------------------------------------------------

    def bepaal_land(residence):
        if pd.isna(residence):
            return pd.NA

        residence = str(residence).strip().upper()

        if residence.endswith(", BE"):
            return "Belgium"

        elif residence.endswith(", UK"):
            return "UK"

        elif residence.endswith(", NO"):
            return "Norway"

        elif residence.endswith(", US") or residence.endswith(", USA"):
            return "U.S.A."

        else:
            return "Netherlands"

    uren_per_persoon["Gekozen land"] = (
        uren_per_persoon["Residence"].apply(bepaal_land)
    )

    # --------------------------------------------------
    # GRADE SCHOONMAKEN
    # --------------------------------------------------

    uren_per_persoon["grade_match"] = (
        uren_per_persoon["Grade"]
        .astype("string")
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
        .str.lower()
    )

    tarieven.columns = (
        tarieven.columns
        .astype(str)
        .str.strip()
    )

    tarieven["grade_match"] = (
        tarieven["Grade"]
        .astype("string")
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
        .str.lower()
    )

    # Tarieven numeriek maken
    landen = [
        "Netherlands",
        "Belgium",
        "U.S.A.",
        "Norway"
    ]

    for land in landen:
        if land in tarieven.columns:
            tarieven[land] = pd.to_numeric(
                tarieven[land],
                errors="coerce"
            )

    # --------------------------------------------------
    # CONTRACTFACTOR
    # --------------------------------------------------

    def contract_factor(contract):
        if pd.isna(contract):
            return pd.NA

        contract = (
            str(contract)
            .upper()
            .replace("FTE", "")
            .strip()
        )

        try:
            return float(contract)
        except:
            return pd.NA

    # --------------------------------------------------
    # UURTARIEF BEPALEN
    # --------------------------------------------------

    def zoek_uurtarief(rij):

        # Werknemer helemaal niet gevonden
        if pd.isna(rij["Full Name"]):
            return pd.Series([
                pd.NA,
                pd.NA,
                pd.NA,
                "Werknemer niet gevonden"
            ])

        land = rij["Gekozen land"]

        if pd.isna(land):
            return pd.Series([
                pd.NA,
                pd.NA,
                pd.NA,
                "Residence ontbreekt"
            ])

        # ----------------------------------------------
        # GEEN GRADE -> SALARIS GEBRUIKEN
        # ----------------------------------------------

        if pd.isna(rij["Grade"]) or str(rij["Grade"]).strip() == "":

            salaris = pd.to_numeric(
                rij["Annual Salary"],
                errors="coerce"
            )

            contract = contract_factor(
                rij["Contract"]
            )

            if pd.isna(salaris):
                return pd.Series([
                    pd.NA,
                    pd.NA,
                    pd.NA,
                    "Annual Salary ontbreekt"
                ])

            if pd.isna(contract):
                return pd.Series([
                    pd.NA,
                    pd.NA,
                    pd.NA,
                    "Contract ontbreekt of is niet herkenbaar"
                ])

            # Salaris omrekenen naar uurtarief
            jaar_kosten = salaris * contract
            dag_kosten = jaar_kosten / 260
            uur_kosten = dag_kosten / 8

            valuta = {
                "Netherlands": "EUR",
                "Belgium": "EUR",
                "U.S.A.": "USD",
                "Norway": "NOK",
                "UK": "GBP"
            }.get(land)

            return pd.Series([
                round(uur_kosten, 2),
                valuta,
                "Annual Salary + Contract",
                "OK"
            ])

        # ----------------------------------------------
        # WEL GRADE -> TARIEVENTABEL GEBRUIKEN
        # ----------------------------------------------

        if land not in tarieven.columns:
            return pd.Series([
                pd.NA,
                pd.NA,
                pd.NA,
                f"Geen tariefkolom voor {land}"
            ])

        match = tarieven[
            tarieven["grade_match"] == rij["grade_match"]
        ]

        if match.empty:
            return pd.Series([
                pd.NA,
                pd.NA,
                pd.NA,
                "Grade niet gevonden in tarieventabel"
            ])

        tarief = match.iloc[0][land]

        if pd.isna(tarief):
            return pd.Series([
                pd.NA,
                pd.NA,
                pd.NA,
                f"Geen tarief voor {rij['Grade']} in {land}"
            ])

        valuta = {
            "Netherlands": "EUR",
            "Belgium": "EUR",
            "U.S.A.": "USD",
            "Norway": "NOK"
        }.get(land)

        return pd.Series([
            tarief,
            valuta,
            "Grade + land",
            "OK"
        ])

    # Uurtarief bepalen
    uren_per_persoon[
        [
            "Uurtarief",
            "Valuta",
            "Tariefbron",
            "Controle"
        ]
    ] = uren_per_persoon.apply(
        zoek_uurtarief,
        axis=1
    )

    # --------------------------------------------------
    # KOSTEN PER PERSOON PER WEEK
    # --------------------------------------------------

    uren_per_persoon["Kosten"] = (
        uren_per_persoon["Hours"]
        * pd.to_numeric(
            uren_per_persoon["Uurtarief"],
            errors="coerce"
        )
    )

    uren_per_persoon["Kosten"] = (
        uren_per_persoon["Kosten"].round(2)
    )

    return uren_per_persoon

def kosten_per_project_week(kosten_data):
    overzicht = (
        kosten_data
        .dropna(subset=["Kosten", "Valuta"])
        .groupby(
            ["Project", "Week", "Valuta"],
            as_index=False
        )
        .agg(
            Uren=("Hours", "sum"),
            Kosten=("Kosten", "sum")
        )
    )

    overzicht["Kosten"] = overzicht["Kosten"].round(2)

    return overzicht

def kosten_naar_euro(
    kosten_data,
    usd_naar_eur,
    nok_naar_eur,
    gbp_naar_eur
):
    data = kosten_data.copy()

    wisselkoersen = {
        "EUR": 1.0,
        "USD": usd_naar_eur,
        "NOK": nok_naar_eur,
        "GBP": gbp_naar_eur
    }

    data["Wisselkoers naar EUR"] = (
        data["Valuta"].map(wisselkoersen)
    )

    data["Kosten_EUR"] = (
        data["Kosten"]
        * data["Wisselkoers naar EUR"]
    ).round(2)

    return data

def vergelijk_kosten_met_budget(project_week_euro, project_budget):
    kosten = project_week_euro.copy()
    budgetten = project_budget.copy()

    # Projectnamen opschonen voor koppeling
    kosten["project_match"] = (
        kosten["Project"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    budgetten["project_match"] = (
        budgetten["Project"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    # Totale kosten per project
    kosten_per_project = (
        kosten
        .groupby(
            ["Project", "project_match"],
            as_index=False
        )
        .agg(
            Totale_kosten_EUR=("Kosten_EUR", "sum")
        )
    )

    # Budgetkolommen numeriek maken
    budgetten["Budget_NL€"] = pd.to_numeric(
        budgetten["Budget_NL€"],
        errors="coerce"
    )

    budgetten["Budget_BE€"] = pd.to_numeric(
        budgetten["Budget_BE€"],
        errors="coerce"
    )

    # NL-budget gebruiken, anders BE-budget
    budgetten["Budget"] = (
        budgetten["Budget_NL€"]
        .fillna(budgetten["Budget_BE€"])
    )

    budget_info = (
        budgetten[
            [
                "project_match",
                "Budget"
            ]
        ]
        .drop_duplicates("project_match")
    )

    overzicht = kosten_per_project.merge(
        budget_info,
        on="project_match",
        how="left"
    )

    # Resterend budget
    overzicht["Resterend_budget"] = (
        overzicht["Budget"]
        - overzicht["Totale_kosten_EUR"]
    )

    # Percentage budget gebruikt
    overzicht["Budget_gebruikt_%"] = (
        overzicht["Totale_kosten_EUR"]
        / overzicht["Budget"]
        * 100
    )

    overzicht["Budget_gebruikt_%"] = (
        overzicht["Budget_gebruikt_%"]
        .round(1)
    )

    # Status bepalen
    def bepaal_status(rij):
        if pd.isna(rij["Budget"]):
            return "Budget ontbreekt"

        if rij["Budget"] == 0:
            return "Budget niet vastgesteld"

        if rij["Totale_kosten_EUR"] > rij["Budget"]:
            return "Budget overschreden"

        if rij["Budget_gebruikt_%"] >= 90:
            return "Bijna budget bereikt"

        return "OK"

    overzicht["Status"] = overzicht.apply(
        bepaal_status,
        axis=1
    )

    overzicht["Totale_kosten_EUR"] = (
        overzicht["Totale_kosten_EUR"].round(2)
    )

    overzicht["Resterend_budget"] = (
        overzicht["Resterend_budget"].round(2)
    )

    return overzicht[
        [
            "Project",
            "Budget",
            "Totale_kosten_EUR",
            "Resterend_budget",
            "Budget_gebruikt_%",
            "Status"
        ]
    ]

def inlezen_uurtarieven(titel, uitleg, key):
    st.subheader(titel)
    st.write(uitleg)

    bestand = st.file_uploader(
        f"Upload bestand voor {titel}",
        type=["xlsx"],
        key=key
    )

    if bestand is not None:
        try:
            data = pd.read_excel(
                bestand,
                sheet_name="Rates",
                skiprows=1,
                header=0,
                usecols="A:E"
            )

            # Rij onderaan met valuta verwijderen
            data = data.dropna(subset=["Grade"]).copy()

            # '-' omzetten naar lege waarde
            for land in [
                "Netherlands",
                "Belgium",
                "U.S.A.",
                "Norway"
            ]:
                data[land] = pd.to_numeric(
                    data[land].replace("-", pd.NA),
                    errors="coerce"
                )

            data = data.reset_index(drop=True)

            st.success(
                "Uurtarieven succesvol ingelezen."
            )

            st.dataframe(
                data,
                hide_index=True,
                use_container_width=True
            )

            return data

        except Exception as fout:
            st.error(
                f"Bestand '{bestand.name}' kon niet worden ingelezen: {fout}"
            )

    return None
