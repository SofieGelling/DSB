import streamlit as st
import pandas as pd

# streamlit run /Users/sofiegellings/Documents/DSB/App.py

pagina_inlezen = st.Page("Paginas/Inlezen.py",
    title="Upload",
    icon="📂",
    default=True)

pagina_controle = st.Page("Paginas/Controle.py",
    title="Datacontrole",
    icon="🔍")

pagina_overzicht = st.Page("Paginas/OverzichtProjectUren.py",
    title="Overzicht project uren",
    icon="🔍")

pagina_KPI = st.Page("Paginas/OverzichtProjectBezetting.py",
    title="Overzicht project bezettingen",
    icon="🔍")

pagina = st.navigation([
    pagina_inlezen,
    pagina_controle,
    pagina_overzicht,
    pagina_KPI,
    ])

