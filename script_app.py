"""
Tablero de Control Interactivo - Base de Datos Estudiantil
Universidad Nacional de Colombia

App desarrollada en Python + Streamlit + Plotly.
Diseñada para explorar la base completa de +50.000 registros
(se incluye una muestra de datos parciales para pruebas).
"""

import pandas as pd
import plotly.express as px
import streamlit as st

# ----------------------------------------------------------------------------
# CONFIGURACIÓN GENERAL
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Tablero de Control - Base Estudiantil",
    page_icon="🎓",
    layout="wide",
)

DATA_PATH = "datos_prueba.xlsx"

# Edades poco plausibles (errores de digitación en la muestra, p.ej. 1126)
EDAD_MAX_PLAUSIBLE = 100


# ----------------------------------------------------------------------------
# CARGA Y LIMPIEZA DE DATOS
# ----------------------------------------------------------------------------
@st.cache_data
def cargar_datos(path: str) -> pd.DataFrame:
    df = pd.read_excel(path)

    # Normalizar textos (algunos vienen con espacios extra)
    cols_texto = df.select_dtypes(include="object").columns.tolist() + \
        df.select_dtypes(include="string").columns.tolist()
    for c in set(cols_texto):
        df[c] = df[c].astype(str).str.strip().replace({"nan": pd.NA, "None": pd.NA})

    # Corregir errores evidentes de captura en 'edad' (ej. 1126 en vez de 26)
    df.loc[df["edad"] > EDAD_MAX_PLAUSIBLE, "edad"] = pd.NA

    # Año de apertura, útil para segmentar por tiempo
    df["anio_apertura"] = df["apertura"].str.extract(r"(\d{4})").astype("Int64")

    # Relleno legible para categorías con nulos, sin perder el filtro "todos"
    for c in ["estado_civil", "estrato", "etnia", "tipcolegio"]:
        df[c] = df[c].fillna("No informa")

    return df


df_raw = cargar_datos(DATA_PATH)

st.title("🎓 Tablero de Control - Exploración de Base de Datos Estudiantil")
st.caption(
    "Los datos cargados son una muestra parcial (49 registros) con fines de demostración. "
    "La base real contiene más de 50.000 registros; basta con reemplazar el archivo en "
    "`data/datos_prueba_2_.xlsx` manteniendo la misma estructura de columnas para que el "
    "tablero funcione igual sobre el conjunto completo."
)

# ----------------------------------------------------------------------------
# FILTROS (barra lateral) - 5 controles interconectados
# ----------------------------------------------------------------------------
st.sidebar.header("🔎 Filtros")

# 1) Sede
sedes_sel = st.sidebar.multiselect(
    "Sede",
    options=sorted(df_raw["sede"].dropna().unique()),
    default=[],
    help="Selecciona una o varias sedes. Vacío = todas.",
)

# El resto de opciones se calculan sobre el subconjunto ya filtrado por sede,
# para que cada filtro solo muestre valores relevantes a la selección previa.
df_tmp = df_raw[df_raw["sede"].isin(sedes_sel)] if sedes_sel else df_raw

# 2) Facultad (depende de sede)
facultades_sel = st.sidebar.multiselect(
    "Facultad",
    options=sorted(df_tmp["facultad"].dropna().unique()),
    default=[],
    help="Depende de la(s) sede(s) elegidas. Vacío = todas.",
)
df_tmp = df_tmp[df_tmp["facultad"].isin(facultades_sel)] if facultades_sel else df_tmp

# 3) Nivel de formación
niveles_sel = st.sidebar.multiselect(
    "Nivel de formación",
    options=sorted(df_tmp["nivel"].dropna().unique()),
    default=[],
    help="Pregrado, maestría, doctorado, etc. Vacío = todos.",
)
df_tmp = df_tmp[df_tmp["nivel"].isin(niveles_sel)] if niveles_sel else df_tmp

# 4) Género
generos_sel = st.sidebar.multiselect(
    "Género",
    options=sorted(df_tmp["genero"].dropna().unique()),
    default=[],
    help="Vacío = todos.",
)
df_tmp = df_tmp[df_tmp["genero"].isin(generos_sel)] if generos_sel else df_tmp

# 5) Rango de edad
edad_min_data = int(df_tmp["edad"].min(skipna=True)) if df_tmp["edad"].notna().any() else 0
edad_max_data = int(df_tmp["edad"].max(skipna=True)) if df_tmp["edad"].notna().any() else 100
rango_edad = st.sidebar.slider(
    "Rango de edad",
    min_value=int(df_raw["edad"].min(skipna=True)),
    max_value=int(df_raw["edad"].max(skipna=True)),
    value=(edad_min_data, edad_max_data),
    help="Filtra estudiantes por edad (se excluyen valores no plausibles).",
)

# ----------------------------------------------------------------------------
# APLICAR TODOS LOS FILTROS
# ----------------------------------------------------------------------------
df = df_raw.copy()
if sedes_sel:
    df = df[df["sede"].isin(sedes_sel)]
if facultades_sel:
    df = df[df["facultad"].isin(facultades_sel)]
if niveles_sel:
    df = df[df["nivel"].isin(niveles_sel)]
if generos_sel:
    df = df[df["genero"].isin(generos_sel)]
df = df[
    df["edad"].isna()
    | df["edad"].between(rango_edad[0], rango_edad[1])
]

st.sidebar.markdown("---")
st.sidebar.metric("Registros filtrados", f"{len(df):,}".replace(",", "."))

if df.empty:
    st.warning("No hay registros que coincidan con los filtros seleccionados. Ajusta los filtros para ver resultados.")
    st.stop()

# ----------------------------------------------------------------------------
# INDICADORES CLAVE (KPIs)
# ----------------------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Estudiantes", f"{len(df):,}".replace(",", "."))
col2.metric("Edad promedio", f"{df['edad'].mean():.1f} años" if df["edad"].notna().any() else "N/D")
col3.metric(
    "Promedio académico",
    f"{df['prom_academico_actual'].mean():.2f}" if df["prom_academico_actual"].notna().any() else "N/D",
)
col4.metric("Programas curriculares", df["programa_curricular"].nunique())

st.markdown("---")

# ----------------------------------------------------------------------------
# VISUALIZACIONES (4) - todas reaccionan a los filtros aplicados arriba
# ----------------------------------------------------------------------------
fila1_col1, fila1_col2 = st.columns(2)

# 1) Distribución de estudiantes por facultad (barras horizontales)
with fila1_col1:
    st.subheader("Estudiantes por facultad")
    conteo_facultad = (
        df.groupby("facultad", observed=True)
        .size()
        .reset_index(name="estudiantes")
        .sort_values("estudiantes", ascending=True)
    )
    fig_facultad = px.bar(
        conteo_facultad,
        x="estudiantes",
        y="facultad",
        orientation="h",
        text="estudiantes",
        color="estudiantes",
        color_continuous_scale="Blues",
    )
    fig_facultad.update_layout(
        showlegend=False, coloraxis_showscale=False, height=420,
        margin=dict(l=10, r=10, t=10, b=10),
    )
    st.plotly_chart(fig_facultad, use_container_width=True)

# 2) Composición por género y nivel de formación (barras apiladas 100%)
with fila1_col2:
    st.subheader("Género según nivel de formación")
    conteo_genero_nivel = (
        df.groupby(["nivel", "genero"], observed=True)
        .size()
        .reset_index(name="estudiantes")
    )
    fig_genero = px.bar(
        conteo_genero_nivel,
        x="nivel",
        y="estudiantes",
        color="genero",
        barmode="stack",
        text="estudiantes",
    )
    fig_genero.update_layout(
        height=420, margin=dict(l=10, r=10, t=10, b=10),
        legend_title_text="Género",
        xaxis_title="Nivel", yaxis_title="Estudiantes",
    )
    st.plotly_chart(fig_genero, use_container_width=True)

fila2_col1, fila2_col2 = st.columns(2)

# 3) Distribución de edades (histograma)
with fila2_col1:
    st.subheader("Distribución de edades")
    fig_edad = px.histogram(
        df.dropna(subset=["edad"]),
        x="edad",
        nbins=20,
        color_discrete_sequence=["#2C7BE5"],
    )
    fig_edad.update_layout(
        height=420, margin=dict(l=10, r=10, t=10, b=10),
        xaxis_title="Edad", yaxis_title="Estudiantes", bargap=0.05,
    )
    st.plotly_chart(fig_edad, use_container_width=True)

# 4) Promedio académico por estrato (diagrama de caja)
with fila2_col2:
    st.subheader("Promedio académico por estrato")
    df_prom = df.dropna(subset=["prom_academico_actual"]).copy()
    orden_estrato = sorted(
        df_prom["estrato"].unique(),
        key=lambda x: (x == "No informa", x),
    )
    fig_prom = px.box(
        df_prom,
        x="estrato",
        y="prom_academico_actual",
        color="estrato",
        category_orders={"estrato": orden_estrato},
        points="outliers",
    )
    fig_prom.update_layout(
        height=420, margin=dict(l=10, r=10, t=10, b=10), showlegend=False,
        xaxis_title="Estrato", yaxis_title="Promedio académico actual",
    )
    st.plotly_chart(fig_prom, use_container_width=True)

# ----------------------------------------------------------------------------
# TABLA DE DETALLE (opcional, para inspección fina)
# ----------------------------------------------------------------------------
with st.expander("📋 Ver datos filtrados en detalle"):
    st.dataframe(df, use_container_width=True, height=350)
    st.download_button(
        "Descargar selección actual (CSV)",
        data=df.to_csv(index=False).encode("utf-8-sig"),
        file_name="estudiantes_filtrados.csv",
        mime="text/csv",
    )
