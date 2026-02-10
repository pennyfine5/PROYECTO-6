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
    top_k=8,
    recent_window=3,
    popular_past_window=10,
    decline_thresh=0.01
):
    df = df_games.copy()

    # ---- limpieza ----
    df[year_col] = pd.to_numeric(df[year_col], errors="coerce")
    df = df.dropna(subset=[year_col])
    df[year_col] = df[year_col].astype(int)

    df[sales_cols] = df[sales_cols].fillna(0)
    df["total_sales"] = df[sales_cols].sum(axis=1)

    # ---- totales ----
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

    # =========================
    # 📈 GRÁFICA 1: líneas
    # =========================
    fig_lines, ax = plt.subplots(figsize=(12, 5))
    for p in top_platforms:
        ax.plot(pivot.index, pivot[p], marker="o", label=p)

    ax.set_title(f"Ventas por año — Top {top_k} plataformas")
    ax.set_xlabel("Año")
    ax.set_ylabel("Ventas")
    ax.legend()
    ax.grid(alpha=0.3)

    # =========================
    # 📊 GRÁFICA 2: área acumulada
    # =========================
    fig_area, ax2 = plt.subplots(figsize=(12, 5))
    pivot[top_platforms].plot.area(ax=ax2, alpha=0.75)
    ax2.set_title("Participación anual por plataforma")
    ax2.set_xlabel("Año")
    ax2.set_ylabel("Ventas")

    # =========================
    # ⏳ GRÁFICA 3: timeline de vida
    # =========================
    platform_stats = []

    for p in pivot.columns:
        s = pivot[p]
        nz = s[s > 0]
        if nz.empty:
            continue

        first = int(nz.index.min())
        last = int(nz.index.max())
        peak = int(s.idxmax())

        platform_stats.append({
            "platform": p,
            "first": first,
            "peak": peak,
            "last": last,
            "total_sales": s.sum(),
            "years_active": last - first + 1,
            "years_to_peak": peak - first,
            "years_decline": last - peak
        })

    stats_df = (
        pd.DataFrame(platform_stats)
        .sort_values("total_sales", ascending=False)
        .reset_index(drop=True)
    )

    fig_timeline, ax3 = plt.subplots(figsize=(10, 6))

    for i, row in stats_df.head(top_k).iterrows():
        ax3.hlines(i, row["first"], row["last"], linewidth=6)
        ax3.plot(row["first"], i, "o")
        ax3.plot(row["peak"], i, "s")
        ax3.plot(row["last"], i, "x")

    ax3.set_yticks(range(top_k))
    ax3.set_yticklabels(stats_df.head(top_k)["platform"])
    ax3.set_title("Ciclo de vida de plataformas (first / peak / last)")
    ax3.set_xlabel("Año")
    ax3.grid(axis="x", alpha=0.3)

    # =========================
    # 📉 Plataformas en declive
    # =========================
    last_year = pivot.index.max()
    recent = pivot[pivot.index >= last_year - recent_window + 1].sum()

    decline_df = stats_df[
        (recent[stats_df["platform"]].values < decline_thresh) |
        (stats_df["years_decline"] > stats_df["years_to_peak"])
    ][["platform", "total_sales", "years_active", "years_decline"]]

    # =========================
    # 📌 métricas resumen
    # =========================
    summary = {
        "vida_media": stats_df["years_active"].mean(),
        "vida_mediana": stats_df["years_active"].median(),
        "años_hasta_pico_media": stats_df["years_to_peak"].mean(),
        "años_hasta_pico_mediana": stats_df["years_to_peak"].median(),
        "años_de_declive_media": stats_df["years_decline"].mean(),
    }

    return {
        "platform_total": platform_total,
        "pivot": pivot,
        "stats_df": stats_df,
        "decline_df": decline_df,
        "summary": summary,
        "fig_lines": fig_lines,
        "fig_area": fig_area,
        "fig_timeline": fig_timeline
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
results = platform_lifecycle_analysis(df_games, top_k=10)

st.subheader("📈 Ventas por año")
st.pyplot(results["fig_lines"])

st.subheader("📊 Participación anual")
st.pyplot(results["fig_area"])

st.subheader("⏳ Ciclo de vida de plataformas")
st.pyplot(results["fig_timeline"])

st.subheader("📉 Plataformas en declive")
st.dataframe(results["decline_df"])

st.subheader("📌 Estadísticas resumen")
st.json(results["summary"])
