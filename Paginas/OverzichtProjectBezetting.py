import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("Projectbezetting")

st.markdown("""
<style>
div[data-testid="stMetricValue"] {
    font-size: 2.2rem;
}
div[data-testid="stMetricLabel"] {
    font-size: 1rem;
}
</style>
""", unsafe_allow_html=True)

if "projecturen_schoon" not in st.session_state:
    st.info("Controleer eerst de projecturendata bij Datacontrole.")
    st.stop()

projecturen = st.session_state["projecturen_schoon"].copy()

employees = None
for waarde in st.session_state.values():
    if isinstance(waarde, pd.DataFrame):
        if "Full Name" in waarde.columns and "Grade" in waarde.columns:
            employees = waarde.copy()
            break

if employees is None:
    st.info("Lees eerst de employee-bestanden in.")
    st.stop()

# Namen gelijk maken voor vergelijking
projecturen["naam_match"] = (
    projecturen["Consultant"]
    .astype(str)
    .str.strip()
    .str.lower()
)

employees["naam_match"] = (
    employees["Full Name"]
    .astype(str)
    .str.strip()
    .str.lower()
)

projecturen["Hours"] = pd.to_numeric(
    projecturen["Hours"],
    errors="coerce"
).fillna(0)

# Grade en naam toevoegen aan projecturen
data = projecturen.merge(
    employees[["naam_match", "Full Name", "Grade"]]
    .drop_duplicates("naam_match"),
    on="naam_match",
    how="left"
)

data["Grade"] = (
    data["Grade"]
    .replace(r"^\s*$", pd.NA, regex=True)
    .fillna("No grade")
)

data["Full Name"] = data["Full Name"].fillna(data["Consultant"])

projecten = sorted(data["Project"].dropna().unique())

gekozen_project = st.session_state.pop(
    "geselecteerd_project",
    None
)

if gekozen_project in projecten:
    index = projecten.index(gekozen_project)
else:
    index = 0

project = st.selectbox(
    "Kies een project",
    projecten,
    index=index
)

project_data = data[data["Project"] == project].copy()

st.subheader(f"Overzicht {project}")

# Algemene KPI's
totaal_uren = project_data["Hours"].sum()
aantal_consultants = project_data["Consultant"].nunique()
aantal_weken = project_data["Week"].nunique()

col1, col2, col3 = st.columns(3)
col1.metric("Totaal uren", f"{totaal_uren:.1f}")
col2.metric("Consultants", aantal_consultants)
col3.metric("Projectweken", aantal_weken)

# Uren per grade per week
uren_grade_week = (
    project_data
    .groupby(["Week", "Grade"])["Hours"]
    .sum()
    .reset_index()
)

weken = sorted(project_data["Week"].dropna().unique())
grades = sorted(project_data["Grade"].dropna().unique())

combinaties = pd.MultiIndex.from_product(
    [weken, grades],
    names=["Week", "Grade"]
).to_frame(index=False)

uren_grade_week = combinaties.merge(
    uren_grade_week,
    on=["Week", "Grade"],
    how="left"
)

uren_grade_week["Hours"] = uren_grade_week["Hours"].fillna(0)

# Gemiddelde uren per week per grade
samenvatting_grade = (
    uren_grade_week
    .groupby("Grade")["Hours"]
    .agg(
        Gemiddeld_per_week="mean",
        Totaal_uren="sum"
    )
    .reset_index()
    .sort_values("Gemiddeld_per_week", ascending=False)
)

aantal_per_grade = (
    project_data
    .groupby("Grade")["Full Name"]
    .nunique()
    .reset_index(name="Aantal consultants")
)

samenvatting_grade = samenvatting_grade.merge(
    aantal_per_grade,
    on="Grade",
    how="left"
)

samenvatting_grade["Gemiddeld_per_week"] = (
    samenvatting_grade["Gemiddeld_per_week"].round(1)
)

samenvatting_grade["Totaal_uren"] = (
    samenvatting_grade["Totaal_uren"].round(1)
)

st.subheader("Gemiddeld aantal uren per week per grade")

st.dataframe(
    samenvatting_grade.rename(columns={
        "Gemiddeld_per_week": "Gem. uur/week",
        "Totaal_uren": "Totaal uren"
    }),
    hide_index=True,
    use_container_width=True
)

# Grafiek uren per grade per week
st.subheader("Uren per grade per week")

grade_week_pivot = uren_grade_week.pivot(
    index="Week",
    columns="Grade",
    values="Hours"
)

st.bar_chart(grade_week_pivot)

# Consultants binnen project
st.subheader("Consultants binnen het project")

consultants = (
    project_data
    .groupby(["Full Name", "Grade"])["Hours"]
    .sum()
    .reset_index()
    .sort_values("Hours", ascending=False)
    .rename(columns={
        "Full Name": "Consultant",
        "Hours": "Totaal uren"
    })
)

st.dataframe(
    consultants,
    hide_index=True,
    use_container_width=True
)

# Details per week
with st.expander("Bekijk details per week"):
    detail = (
        project_data
        .groupby(["Week", "Full Name", "Grade"])["Hours"]
        .sum()
        .reset_index()
        .sort_values(["Week", "Grade", "Full Name"])
        .rename(columns={
            "Full Name": "Consultant",
            "Hours": "Uren"
        })
    )

    st.dataframe(
        detail,
        hide_index=True,
        use_container_width=True
    )