import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(
    page_title="ScienceNet - Red de Investigación Valdivia",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ----------------------------------------------------------------------------
# Estilo oscuro tipo "ScienceNet"
# ----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    .stApp { background-color: #0a0e1a; color: #e2e8f0; }
    [data-testid="stMetricValue"] { color: #2dd4bf; font-size: 28px; }
    [data-testid="stMetricLabel"] { color: #94a3b8; }
    h1, h2, h3 { color: #f1f5f9; }
    .stTextInput input { background-color: #131a2b; color: #e2e8f0; border: 1px solid #1e293b; }
    div[data-baseweb="select"] { background-color: #131a2b; }
    .perfil-card {
        background-color: #131a2b;
        border: 1px solid #1e293b;
        border-radius: 10px;
        padding: 18px;
    }
    .tag {
        display: inline-block;
        background-color: #1e293b;
        color: #2dd4bf;
        border-radius: 14px;
        padding: 3px 12px;
        margin: 3px 4px 3px 0;
        font-size: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

DISCIPLINA_COLORS = {
    "Enfermería": "#2dd4bf",
    "Bioquímica": "#8b5cf6",
    "Salud Pública": "#22c55e",
    "Medicina": "#ef4444",
    "Ciencias Básicas": "#9ca3af",
    "Ingeniería": "#f97316",
    "Ciencias Sociales": "#ec4899",
}

TIPO_COLORS = {
    "Contacto ocasional": "#9ca3af",
    "Proyecto conjunto": "#2dd4bf",
    "Coautoría": "#8b5cf6",
    "Colaboración frecuente": "#f97316",
}


# ----------------------------------------------------------------------------
# Datos
# ----------------------------------------------------------------------------
@st.cache_data
def load_data():
    investigadores = pd.read_csv("investigadores.csv")
    try:
        colaboraciones = pd.read_csv("colaboraciones.csv")
    except FileNotFoundError:
        colaboraciones = pd.DataFrame(columns=["Investigador_A", "Investigador_B", "Tipo"])
    return investigadores, colaboraciones


investigadores, colaboraciones = load_data()

# ----------------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------------
st.markdown("## 🔬 ScienceNet — Red de Investigación Valdivia")

busqueda = st.text_input("🔍 Buscar investigadora, institución, país o área...", label_visibility="collapsed", placeholder="🔍 Buscar investigadora, institución, país o área...")

# ----------------------------------------------------------------------------
# Filtros
# ----------------------------------------------------------------------------
with st.expander("⚙️ Filtros"):
    disciplinas_disp = sorted(investigadores["Disciplina"].dropna().unique())
    paises_disp = sorted(investigadores["Pais"].dropna().unique())
    f_disciplina = st.multiselect("Disciplina", disciplinas_disp)
    f_pais = st.multiselect("País", paises_disp)

df = investigadores.copy()
if busqueda:
    mask = (
        df["Nombre"].str.contains(busqueda, case=False, na=False)
        | df["Institucion"].str.contains(busqueda, case=False, na=False)
        | df["Pais"].str.contains(busqueda, case=False, na=False)
        | df["Disciplina"].str.contains(busqueda, case=False, na=False)
    )
    df = df[mask]
if f_disciplina:
    df = df[df["Disciplina"].isin(f_disciplina)]
if f_pais:
    df = df[df["Pais"].isin(f_pais)]

# ----------------------------------------------------------------------------
# KPIs
# ----------------------------------------------------------------------------
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Investigadoras/es", len(df))
k2.metric("Países", df["Pais"].nunique())
k3.metric("Instituciones", df["Institucion"].nunique())
k4.metric("Colaboraciones", len(colaboraciones))
k5.metric("Publicaciones", int(df["Publicaciones"].sum()))

st.divider()

# ----------------------------------------------------------------------------
# Layout: mapa | panel de análisis
# ----------------------------------------------------------------------------
map_col, side_col = st.columns([3, 1])

coords_lookup = {row["Nombre"]: (row["Lat"], row["Lon"]) for _, row in df.iterrows()}

with map_col:
    m = folium.Map(location=[10, -20], zoom_start=2, tiles="CartoDB dark_matter")

    # Líneas de colaboración
    for _, row in colaboraciones.iterrows():
        a, b, tipo = row["Investigador_A"], row["Investigador_B"], row["Tipo"]
        if a in coords_lookup and b in coords_lookup:
            color = TIPO_COLORS.get(tipo, "#64748b")
            dash = "6,6" if tipo == "Contacto ocasional" else None
            weight = 4 if tipo == "Colaboración frecuente" else 2
            folium.PolyLine(
                locations=[coords_lookup[a], coords_lookup[b]],
                color=color,
                weight=weight,
                dash_array=dash,
                opacity=0.8,
            ).add_to(m)

    # Marcadores + etiquetas
    for _, row in df.iterrows():
        color = DISCIPLINA_COLORS.get(row["Disciplina"], "#60a5fa")
        folium.CircleMarker(
            location=(row["Lat"], row["Lon"]),
            radius=9,
            color=color,
            weight=2,
            fill=True,
            fill_color=color,
            fill_opacity=0.85,
            tooltip=row["Nombre"],
        ).add_to(m)
        folium.Marker(
            location=(row["Lat"], row["Lon"]),
            icon=folium.DivIcon(
                html=f"""<div style="font-size:11px;color:#f1f5f9;font-weight:600;
                transform:translate(12px,-6px);white-space:nowrap;
                text-shadow:0 0 4px #000;">{row['Nombre']}</div>"""
            ),
        ).add_to(m)

    map_data = st_folium(m, width=None, height=550, returned_objects=["last_object_clicked"])

with side_col:
    st.markdown("#### 📊 Análisis de red")
    if len(colaboraciones) > 0:
        conteo = pd.concat([colaboraciones["Investigador_A"], colaboraciones["Investigador_B"]]).value_counts()
        ranking = conteo.reset_index()
        ranking.columns = ["Nombre", "Conexiones"]
        ranking = ranking.merge(investigadores[["Nombre", "Disciplina"]], on="Nombre", how="left")
        ranking = ranking.sort_values("Conexiones", ascending=False).head(6)
        max_con = ranking["Conexiones"].max()
        for i, r in enumerate(ranking.itertuples(), start=1):
            st.markdown(f"**{i}. {r.Nombre}**")
            st.caption(f"{r.Conexiones} conexiones · {r.Disciplina}")
            st.progress(r.Conexiones / max_con)
    else:
        st.caption("Aún no hay colaboraciones registradas.")

    st.markdown("#### Leyenda")
    for disc, color in DISCIPLINA_COLORS.items():
        st.markdown(
            f'<span style="color:{color};">●</span> {disc}',
            unsafe_allow_html=True,
        )

# ----------------------------------------------------------------------------
# Panel de perfil académico (al hacer clic en un marcador)
# ----------------------------------------------------------------------------
selected_name = None
if map_data and map_data.get("last_object_clicked"):
    clicked = map_data["last_object_clicked"]
    if clicked:
        lat, lon = clicked["lat"], clicked["lng"]
        tmp = df.copy()
        tmp["dist"] = (tmp["Lat"] - lat) ** 2 + (tmp["Lon"] - lon) ** 2
        nearest = tmp.sort_values("dist").iloc[0]
        if nearest["dist"] < 0.5:
            selected_name = nearest["Nombre"]

if selected_name:
    perfil = investigadores[investigadores["Nombre"] == selected_name].iloc[0]
    n_colabs = (
        (colaboraciones["Investigador_A"] == selected_name)
        | (colaboraciones["Investigador_B"] == selected_name)
    ).sum()

    st.divider()
    st.markdown(f"### 👤 Perfil académico: {perfil['Nombre']}")
    st.markdown(
        f"""
        <div class="perfil-card">
            <h3 style="margin-bottom:0;">{perfil['Nombre']}</h3>
            <p style="color:#94a3b8; margin-top:2px;">
                {perfil['Cargo']} · {perfil['Institucion']} · {perfil['Pais']}
            </p>
            <span class="tag">{perfil['Disciplina']}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("Publicaciones", int(perfil["Publicaciones"]))
    c2.metric("Proyectos", int(perfil["Proyectos"]))
    c3.metric("Colaboradores", int(n_colabs))
    st.markdown("**Biografía**")
    st.write(perfil["Biografia"])

# ----------------------------------------------------------------------------
# Tabla completa
# ----------------------------------------------------------------------------
st.divider()
st.markdown("### Listado completo")
st.dataframe(df.drop(columns=["Lat", "Lon"], errors="ignore"), use_container_width=True)
