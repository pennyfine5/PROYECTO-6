import streamlit as st
import pandas as pd
import plotly.express as px
df_games = pd.read_csv('V_GAMES.csv')

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
    # Limpieza básica
    df = df.dropna(subset=['Name']).copy()
    return df

# Cargar los datos
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



