
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Mapa de Red Científica Valdivia", layout="wide")

st.title("🌐 Plataforma de Red de Investigación - Valdivia")
st.write("Visualización de colaboradores y ecosistema científico regional.")

# Cargar datos
@st.cache_data
def load_data():
    return pd.read_csv('red_investigacion_limpia.csv')

df = load_data()

# Buscador
nombre_buscado = st.text_input("Buscar investigador por nombre:")
if nombre_buscado:
    df = df[df['Nombre'].str.contains(nombre_buscado, case=False)]

# Coordenadas de referencia
coords_inst = {
    "Universidad Santo Tomás": [-39.818, -73.245],
    "Universitat de Barcelona": [41.385, 2.173],
    "Universitat de les Illes Balears": [39.637, 2.648],
    "Universidad Católica de la Santísima Concepción": [-36.758, -73.064],
    "Universidad Mayor": [-33.437, -70.650],
    "Universidad Adventista de Chile": [-36.565, -72.096],
    "Viña del Mar University": [-33.015, -71.551],
    "San Sebastián University": [-39.825, -73.250]
}

# Mapa
m = folium.Map(location=[-39.81, -73.23], zoom_start=6)
for _, row in df.iterrows():
    inst = row['Institucion']
    if inst in coords_inst:
        folium.CircleMarker(
            location=coords_inst[inst],
            radius=8,
            popup=f"{row['Nombre']} ({inst})",
            color="blue",
            fill=True
        ).add_to(m)

st_folium(m, width=1000, height=500)
st.dataframe(df)
