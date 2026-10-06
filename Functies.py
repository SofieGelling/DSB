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

    data["Hours"] = pd.to_numeric(
        data["Hours"], errors="coerce"
    ).fillna(0)

    data["Week"] = pd.to_numeric(
        data["Week"].astype(str).str.extract(r"(\d+)")[0],
        errors="coerce"
    )

    data = data.dropna(subset=["Project", "Week", "Consultant"])
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

    # Employeegegevens koppelen
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

    # Land bepalen
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

    # Grade schoonmaken voor koppeling
    uren_per_persoon["grade_match"] = (
        uren_per_persoon["Grade"]
        .astype("string")
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
        .str.lower()
    )

    tarieven.columns = tarieven.columns.astype(str).str.strip()

    tarieven["grade_match"] = (
        tarieven["Grade"]
        .astype("string")
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
        .str.lower()
    )

    # Tarieven numeriek maken
    landen = ["Netherlands", "Belgium", "U.S.A.", "Norway"]

    for land in landen:
        if land in tarieven.columns:
            tarieven[land] = pd.to_numeric(
                tarieven[land],
                errors="coerce"
            )

    # Uurtarief per werknemer bepalen
    def zoek_uurtarief(rij):
        if pd.isna(rij["Full Name"]):
            return pd.Series([pd.NA, pd.NA, "Werknemer niet gevonden"])

        if pd.isna(rij["Grade"]) or str(rij["Grade"]).strip() == "":
            salaris = pd.to_numeric(rij["Annual Salary"], errors="coerce")
            contract = contract_factor(rij["Contract"])

        if pd.isna(salaris):
            return pd.Series([pd.NA, pd.NA, "Annual Salary ontbreekt"])

        if pd.isna(contract):
            return pd.Series([
                pd.NA,
                pd.NA,
                "Contract ontbreekt of is niet herkenbaar"])

        jaar_kosten = salaris * contract
        dag_kosten = jaar_kosten / 260
        uur_kosten = dag_kosten / 8

        valuta = {
            "Netherlands": "EUR",
            "Belgium": "EUR",
            "U.S.A.": "USD",
            "Norway": "NOK",
            "UK": "GBP"
        }.get(rij["Gekozen land"])

        return pd.Series([
            round(uur_kosten, 2),
            valuta,
            "OK - berekend uit Annual Salary"])

        land = rij["Gekozen land"]

        if land not in tarieven.columns:
            return pd.Series([
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
                "Grade niet gevonden in tarieventabel"
            ])

        tarief = match.iloc[0][land]

        if pd.isna(tarief):
            return pd.Series([
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
            "OK"
        ])

    uren_per_persoon[
        ["Uurtarief", "Valuta", "Controle"]
    ] = uren_per_persoon.apply(
        zoek_uurtarief,
        axis=1
    )

    return uren_per_persoon

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
                skiprows=1,   # rij 1 overslaan
                header=0,     # rij 2 wordt de header
                usecols="A:E"
            )

            # Onderste rij met valuta verwijderen
            data = data.dropna(subset=["Grade"]).copy()

            # '-' betekent geen tarief
            for land in ["Netherlands", "Belgium", "U.S.A.", "Norway"]:
                data[land] = pd.to_numeric(
                    data[land].replace("-", pd.NA),
                    errors="coerce"
                )

            data = data.reset_index(drop=True)

            st.success("Uurtarieven succesvol ingelezen.")
            st.dataframe(data, hide_index=True)

            return data

        except Exception as fout:
            st.error(
                f"Bestand '{bestand.name}' kon niet worden ingelezen: {fout}"
            )

    return None




