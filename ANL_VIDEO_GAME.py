import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import numpy as np
df_games = pd.read_csv('V_GAMES.csv')
df_games.columns = df_games.columns.str.lower()

# Configuración de la página
st.set_page_config(
    page_title="Análisis de Videojuegos",
    page_icon="🎮",
    layout="wide"
)

# Título principal
st.title("🎮 Análisis de Videojuegos")
st.markdown("---")

# Cargar datos
@st.cache_data
def load_data():
    df = pd.read_csv('V_GAMES.csv')
    df.columns = df.columns.str.lower()  # Aplicar aquí
    df = df.dropna(subset=['name']).copy()
    return df

# Cargar los datos UNA SOLA VEZ
df_games = load_data()

# Sidebar para filtros
st.sidebar.header("Filtros")


games_per_year = df_games['year_of_release'].value_counts().sort_index()
plt.figure(figsize=(10,5))
plt.bar(games_per_year.index.astype(str), games_per_year.values)
plt.xlabel("Año de lanzamiento")
plt.ylabel("Número de juegos")
plt.title("Juegos lanzados por año")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()




#observa cómo varían las ventas de una plataforma a otra. Elige las plataformas con las mayores ventas totales y construye una distribución basada en los datos de cada año. Busca las plataformas que solían ser populares pero que ahora no tienen ventas. ¿Cuánto tardan generalmente las nuevas plataformas en aparecer y las antiguas en desaparecer?
# el rango de vida de una empresa es de 8 años en aparecer y desaparecer 4 de subida 4 de bajada.
def platform_lifecycle_analysis(df_games,
                                sales_cols = ['na_sales','eu_sales','jp_sales','other_sales'],
                                year_col = 'year_of_release',
                                platform_col = 'platform',
                                top_k = 6,
                                recent_window = 3,
                                popular_past_window = 10,
                                popular_top_pct = 0.2,
                                decline_sales_abs_thresh = 0.01):

    df = df_games.copy()

    
    if not np.issubdtype(df[year_col].dtype, np.integer):
        df[year_col] = pd.to_numeric(df[year_col], errors='coerce')
    df = df.dropna(subset=[year_col]).copy()
    df[year_col] = df[year_col].astype(int)

    
    for c in sales_cols:
        if c not in df.columns:
            raise ValueError(f"Falta columna de ventas: {c}")
    df[sales_cols] = df[sales_cols].fillna(0)

    
    if 'total_sales' not in df.columns:
        df['total_sales'] = df[sales_cols].sum(axis=1)

   
    platform_total = df.groupby(platform_col)['total_sales'].sum().sort_values(ascending=False)

   
    pivot = df.pivot_table(index=year_col, columns=platform_col, values='total_sales', aggfunc='sum', fill_value=0)
    pivot = pivot.sort_index()

    
    top_platforms = platform_total.head(top_k).index.tolist()

    plt.figure(figsize=(12,5))
    for p in top_platforms:
        if p in pivot.columns:
            plt.plot(pivot.index, pivot[p], marker='o', label=p)
    plt.title(f'Ventas por año — top {top_k} plataformas')
    plt.xlabel('Año')
    plt.ylabel('Ventas (total_sales)')
    plt.legend()
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.show()

    plt.figure(figsize=(12,5))
    pivot[top_platforms].fillna(0).plot.area(alpha=0.75, figsize=(12,5))
    plt.title(f'Participación anual (stacked area) — top {top_k} plataformas')
    plt.ylabel('Ventas')
    plt.xlabel('Año')
    plt.tight_layout()
    plt.show()

    last_year = pivot.index.max()
    recent_years = [y for y in range(last_year - recent_window + 1, last_year + 1)]
    start_past = max(pivot.index.min(), last_year - popular_past_window - recent_window)
    past_window = pivot.loc[start_past: last_year - recent_window] if start_past <= last_year - recent_window else pd.DataFrame()

    decline_candidates = pd.DataFrame(columns=['platform','past_avg_share','recent_sales','peak_sales'])

    if not past_window.empty:
        total_past = past_window.sum(axis=1)
        share_past = (past_window.div(total_past, axis=0)).mean().sort_values(ascending=False)
        cutoff_popular = share_past.quantile(1 - popular_top_pct)  # top X% threshold
        popular_platforms = share_past[share_past >= cutoff_popular].index.tolist()

        if set(recent_years).issubset(set(pivot.index)):
            recent_sales = pivot.loc[recent_years].sum()
        else:
            recent_sales = pivot.loc[pivot.index >= (last_year - recent_window + 1)].sum()

        for p in popular_platforms:
            rec = float(recent_sales.get(p,0.0))
            peak = float(pivot[p].max()) if p in pivot.columns else 0.0
            past_share = float(share_past.get(p,0.0))
            # condiciones de declive: ventas recientes muy bajas absolutas o respecto al pico
            if (rec < decline_sales_abs_thresh) or (peak>0 and rec/peak < 0.1):
                new_row = pd.DataFrame([{
                'platform': p,
                'past_avg_share': past_share,
                'recent_sales': rec,
                'peak_sales': peak
                }])

# Concatenar con el DataFrame existente
                decline_candidates = pd.concat([decline_candidates, new_row], ignore_index=True)

    decline_candidates = decline_candidates.sort_values('past_avg_share', ascending=False)

    platform_stats = []
    for p in pivot.columns:
        s = pivot[p]
        nz = s[s>0]
        if nz.empty:
            continue
        first = int(nz.index.min())
        last = int(nz.index.max())
        peak_year = int(s.idxmax())
        years_active = last - first + 1
        years_to_peak = peak_year - first
        years_from_peak_to_last = last - peak_year
        total_sales_p = float(s.sum())
        platform_stats.append({
            'platform': p,
            'first_year': first,
            'peak_year': peak_year,
            'last_year': last,
            'years_active': years_active,
            'years_to_peak': years_to_peak,
            'years_from_peak_to_last': years_from_peak_to_last,
            'total_sales': total_sales_p
        })
    platform_stats_df = pd.DataFrame(platform_stats).sort_values('total_sales', ascending=False).reset_index(drop=True)

    if not platform_stats_df.empty:
        time_to_peak_med = platform_stats_df['years_to_peak'].median()
        time_to_peak_mean = platform_stats_df['years_to_peak'].mean()
        lifespan_med = platform_stats_df['years_active'].median()
        lifespan_mean = platform_stats_df['years_active'].mean()
        decline_med = platform_stats_df['years_from_peak_to_last'].median()
        decline_mean = platform_stats_df['years_from_peak_to_last'].mean()
    else:
        time_to_peak_med = time_to_peak_mean = lifespan_med = lifespan_mean = decline_med = decline_mean = np.nan

    topN = platform_stats_df.head(top_k)['platform'].tolist()
    if topN:
        plt.figure(figsize=(10,6))
        for i,p in enumerate(topN):
            row = platform_stats_df[platform_stats_df['platform']==p].iloc[0]
            plt.hlines(y=i, xmin=row['first_year'], xmax=row['last_year'], linewidth=6)
            plt.plot(row['first_year'], i, 'o', label='first' if i==0 else "", markersize=6)
            plt.plot(row['peak_year'], i, 's', markersize=6)
            plt.plot(row['last_year'], i, 'x', markersize=6)
        plt.yticks(range(len(topN)), topN)
        plt.xlabel('Año')
        plt.title(f'Timeline: life (first, peak, last) — top {top_k} plataformas')
        plt.grid(axis='x', alpha=0.3)
        plt.tight_layout()
        plt.show()

    summary_stats = {
        'time_to_peak_median': time_to_peak_med,
        'time_to_peak_mean': time_to_peak_mean,
        'lifespan_median': lifespan_med,
        'lifespan_mean': lifespan_mean,
        'decline_median': decline_med,
        'decline_mean': decline_mean
    }

    results = {
        'platform_total': platform_total,
        'pivot': pivot,
        'top_platforms': top_platforms,
        'decline_candidates': decline_candidates,
        'platform_stats_df': platform_stats_df,
        'summary_stats': summary_stats
    }

    return results


df_filtered = df_games[df_games['year_of_release'] >= 2012].copy()

results = platform_lifecycle_analysis(df_filtered, top_k=8, recent_window=3, popular_past_window=10)

results = platform_lifecycle_analysis(df_games, top_k=31, recent_window=3, popular_past_window=10)

print("\nTop plataformas por ventas totales:")
print(results['platform_total'].head(12))

print("\nPlataformas candidatas en declive (fueron populares pero ahora con ventas muy bajas):")
display(results['decline_candidates'])

print("\nResumen de vida (primeras 20 por ventas):")
display(results['platform_stats_df'].head(20))

print("\nEstadísticas resumen (medianas/medias):")
print(results['summary_stats'])