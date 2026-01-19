import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import numpy as np

# ----------------------------------
# CONFIGURACIÓN DE LA PÁGINA (PRIMERO)
# ----------------------------------
st.set_page_config(
    page_title="Análisis de Videojuegos",
    page_icon="🎮",
    layout="wide"
)

# ----------------------------------
# CARGA DE DATOS
# ----------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("V_GAMES.csv")
    df.columns = df.columns.str.lower()
    df = df.dropna(subset=["name"])
    return df

df_games = load_data()

# ----------------------------------
# TÍTULO
# ----------------------------------
st.title("🎮 Análisis de Videojuegos")
st.markdown("---")

# ----------------------------------
# GRÁFICA: JUEGOS POR AÑO
# ----------------------------------
st.subheader("Juegos lanzados por año")

games_per_year = (
    df_games["year_of_release"]
    .dropna()
    .astype(int)
    .value_counts()
    .sort_index()
)

fig, ax = plt.subplots(figsize=(10, 5))
ax.bar(games_per_year.index.astype(str), games_per_year.values)
ax.set_xlabel("Año de lanzamiento")
ax.set_ylabel("Número de juegos")
ax.set_title("Juegos lanzados por año")
plt.xticks(rotation=45)

st.pyplot(fig)

# ----------------------------------
# FUNCIÓN DE CICLO DE VIDA
# ----------------------------------
def platform_lifecycle_analysis(
    df_games,
    sales_cols=["na_sales", "eu_sales", "jp_sales", "other_sales"],
    year_col="year_of_release",
    platform_col="platform",
    top_k=6,
    recent_window=3,
    popular_past_window=10,
):

    df = df_games.copy()

    df[year_col] = pd.to_numeric(df[year_col], errors="coerce")
    df = df.dropna(subset=[year_col])
    df[year_col] = df[year_col].astype(int)

    df["sales_cols"] = df["sales_cols"].fillna(0)
    df["total_sales"] = df["sales_cols"].sum(axis=1)

    platform_total = (
        df.groupby(platform_col)["total_sales"]
        .sum()
        .sort_values(ascending=False)
    )

    pivot = df.pivot_table(
        index=year_col,
        columns=platform_col,
        values="total_sales",
        aggfunc="sum",
        fill_value=0
    ).sort_index()

    top_platforms = platform_total.head(top_k).index.tolist()

    # --------- LINE PLOT ----------
    fig1, ax1 = plt.subplots(figsize=(12, 5))
    for p in top_platforms:
        ax1.plot(pivot.index, pivot[p], marker="o", label=p)

    ax1.set_title(f"Ventas por año — Top {top_k} plataformas")
    ax1.set_xlabel("Año")
    ax1.set_ylabel("Ventas")
    ax1.legend()
    ax1.grid(alpha=0.3)

    # --------- AREA PLOT ----------
    fig2, ax2 = plt.subplots(figsize=(12, 5))
    pivot[top_platforms].plot.area(ax=ax2, alpha=0.75)
    ax2.set_title("Participación anual por plataforma")
    ax2.set_xlabel("Año")
    ax2.set_ylabel("Ventas")

    return {
        "platform_total": platform_total,
        "pivot": pivot,
        "top_platforms": top_platforms,
        "fig_sales": fig1,
        "fig_area": fig2
    }

# ----------------------------------
# EJECUCIÓN
# ----------------------------------
results = platform_lifecycle_analysis(
    df_games,
    top_k=10,
    recent_window=3,
    popular_past_window=10
)

# ----------------------------------
# MOSTRAR RESULTADOS
# ----------------------------------
st.subheader("Ventas por plataforma (Top 10)")
st.dataframe(results["platform_total"].head(10))

st.subheader("Ventas por año (líneas)")
st.pyplot(results["fig_sales"])

st.subheader("Participación anual (área)")
st.pyplot(results["fig_area"])