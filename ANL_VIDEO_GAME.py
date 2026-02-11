import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go


# ----------------------------------
# CONFIGURACIÓN DE LA PÁGINA
# ----------------------------------
st.set_page_config(
    page_title="Análisis de Videojuegos",
    page_icon="🎮",
    layout="wide"
)

plt.style.use("seaborn-v0_8-darkgrid")

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
# TÍTULO + FILTROS
# ----------------------------------
st.title("🎮 Análisis de Videojuegos")
st.markdown("---")

fig = px.bar(
    sales_by_region, 
    x="region", 
    y="sales",
    color="region",
    title="Ventas por región"
)

st.plotly_chart(fig, use_container_width=True)
st.sidebar.header("🎮 Filtros")

year_min = int(df_games["year_of_release"].min())
year_max = int(df_games["year_of_release"].max())

year_range = st.sidebar.slider(
    "Rango de años",
    year_min,
    year_max,
    (2000, year_max)
)

platforms = sorted(df_games["platform"].dropna().unique())
selected_platforms = st.sidebar.multiselect(
    "Plataformas",
    platforms,
    default=platforms[:5]
)

# ----------------------------------
# FILTRADO
# ----------------------------------
df_filtered = df_games[
    (df_games["year_of_release"].between(year_range[0], year_range[1])) &
    (df_games["platform"].isin(selected_platforms))
]

if df_filtered.empty:
    st.warning("⚠️ No hay datos para los filtros seleccionados")
    st.stop()

# ----------------------------------
# KPIs
# ----------------------------------
total_sales = df_filtered[["na_sales", "eu_sales", "jp_sales", "other_sales"]].sum().sum()
total_games = df_filtered["name"].nunique()
total_platforms = df_filtered["platform"].nunique()

c1, c2, c3 = st.columns(3)
c1.metric("🎮 Juegos", f"{total_games:,}")
c2.metric("🕹️ Plataformas", total_platforms)
c3.metric("💰 Ventas totales", f"{total_sales:.2f} M")

# ----------------------------------
# GRÁFICA: JUEGOS POR AÑO
# ----------------------------------
st.subheader("📆 Juegos lanzados por año")

games_per_year = (
    df_filtered["year_of_release"]
    .dropna()
    .astype(int)
    .value_counts()
    .sort_index()
)

fig, ax = plt.subplots(figsize=(10, 5))
ax.bar(games_per_year.index.astype(str), games_per_year.values)
ax.set_xlabel("Año")
ax.set_ylabel("Número de juegos")
ax.set_title("Juegos lanzados por año")
plt.xticks(rotation=45)

st.pyplot(fig)

# ----------------------------------
# FUNCIÓN: CICLO DE VIDA DE PLATAFORMAS
# ----------------------------------
@st.cache_data
def platform_lifecycle_analysis(
    df,
    sales_cols=["na_sales", "eu_sales", "jp_sales", "other_sales"],
    year_col="year_of_release",
    platform_col="platform",
    top_k=10,
    recent_window=3,
    decline_thresh=0.01
):
    df = df.copy()

    df[year_col] = pd.to_numeric(df[year_col], errors="coerce")
    df = df.dropna(subset=[year_col])
    df[year_col] = df[year_col].astype(int)

    df[sales_cols] = df[sales_cols].fillna(0)
    df["total_sales"] = df[sales_cols].sum(axis=1)

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

    # 📈 Ventas por año
    fig_lines, ax1 = plt.subplots(figsize=(12, 5))
    for p in top_platforms:
        ax1.plot(pivot.index, pivot[p], marker="o", label=p)

    ax1.set_title("Ventas anuales — Top plataformas")
    ax1.set_xlabel("Año")
    ax1.set_ylabel("Ventas")
    ax1.legend()
    ax1.grid(alpha=0.3)

    # 📊 Área acumulada
    fig_area, ax2 = plt.subplots(figsize=(12, 5))
    pivot[top_platforms].plot.area(ax=ax2, alpha=0.75)
    ax2.set_title("Participación anual por plataforma")
    ax2.set_xlabel("Año")
    ax2.set_ylabel("Ventas")

    # ⏳ Ciclo de vida
    stats = []

    for p in pivot.columns:
        s = pivot[p]
        nz = s[s > 0]
        if nz.empty:
            continue

        stats.append({
            "platform": p,
            "first": int(nz.index.min()),
            "peak": int(s.idxmax()),
            "last": int(nz.index.max()),
            "total_sales": s.sum(),
            "years_active": int(nz.index.max() - nz.index.min() + 1),
            "years_to_peak": int(s.idxmax() - nz.index.min()),
            "years_decline": int(nz.index.max() - s.idxmax())
        })

    stats_df = pd.DataFrame(stats).sort_values("total_sales", ascending=False)

    fig_timeline, ax3 = plt.subplots(figsize=(10, 6))


    top_stats = stats_df.head(top_k).reset_index(drop=True)

    
    for i, row in top_stats.iterrows():
        ax3.hlines(i, row["first"], row["last"], linewidth=6)
        ax3.plot(row["first"], i, "o")
        ax3.plot(row["peak"], i, "s")
        ax3.plot(row["last"], i, "x")

    ax3.set_yticks(range(len(top_stats)))
    ax3.set_yticklabels(top_stats["platform"])
    ax3.set_title("Ciclo de vida de plataformas")
    ax3.set_xlabel("Año")
    ax3.grid(axis="x", alpha=0.3)

    last_year = pivot.index.max()
    recent = pivot[pivot.index >= last_year - recent_window + 1].sum()

    decline_df = stats_df[
        (recent[stats_df["platform"]].values < decline_thresh) |
        (stats_df["years_decline"] > stats_df["years_to_peak"])
    ][["platform", "total_sales", "years_active", "years_decline"]]

    summary = {
        "vida_media": round(stats_df["years_active"].mean(), 2),
        "vida_mediana": round(stats_df["years_active"].median(), 2),
        "años_hasta_pico_media": round(stats_df["years_to_peak"].mean(), 2),
        "años_de_declive_media": round(stats_df["years_decline"].mean(), 2),
    }

    return fig_lines, fig_area, fig_timeline, decline_df, summary, platform_total

# ----------------------------------
# EJECUCIÓN
# ----------------------------------
fig_lines, fig_area, fig_timeline, decline_df, summary, platform_total = (
    platform_lifecycle_analysis(df_filtered)
)

# ----------------------------------
# VISUALIZACIÓN
# ----------------------------------
st.subheader("📈 Ventas por año")
st.pyplot(fig_lines)

st.subheader("📊 Participación anual")
st.pyplot(fig_area)

st.subheader("⏳ Ciclo de vida de plataformas")
st.pyplot(fig_timeline)

st.subheader("📉 Plataformas en declive")
st.dataframe(decline_df)

st.subheader("📌 Estadísticas resumen")
st.json(summary)

# ----------------------------------
# INSIGHT AUTOMÁTICO
# ----------------------------------
top_platform = platform_total.idxmax()
top_sales = platform_total.max()

st.info(
    f"🎯 La plataforma dominante fue **{top_platform}** "
    f"con **{top_sales:.2f} millones** de unidades vendidas."
)
