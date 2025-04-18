import pandas as pd
import streamlit as st
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt

# ----- CHARGEMENT & TRANSFORMATION DES DONNÉES -----

# Charger le fichier CSV
my_df = pd.read_csv('main_data.csv')

# Remplacer les mois français par leurs numéros
mois_num = {
    'Décembre': 12,
    'Janvier': 1,
    'Février': 2,
    'Mars': 3,
    'Avril': 4
}
my_df['month'] = my_df['month'].replace(mois_num)
my_df['month'] = my_df['month'].astype(int)

# Créer une colonne datetime (si tous les composants sont présents)
my_df['datetime'] = pd.to_datetime({
    'year': 2023,  # ou une année générique/fictive si pas d'année réelle
    'month': my_df['month'],
    'day': my_df['day']
}, errors='coerce')

# ----- PRÉPARATION DU DATAFRAME POUR LE DASHBOARD -----

df = my_df[['datetime', 'month', 'day', 'hour', 'PM2.5', 'PM10', 'CO', 'O3', 'TEMP', 'PRES', 'DEWP', 'station']].copy()
df['date'] = df['datetime'].dt.strftime('%d/%m')

# ----- CONFIGURATION STREAMLIT -----

st.set_page_config(page_title="Kaikai Air Quality Dashboard",
                   page_icon="bar_chart:",
                   layout="wide")

# ----- SIDEBAR -----

st.sidebar.image("https://www.emploisenegal.com/sites/emploisenegal.com/files/styles/medium/public/logo/logotype_nom_4_300323.png?itok=_BSF9Sjy")
st.sidebar.header("Filter:")

# Nettoyer les valeurs de station pour enlever les NaN et chaînes vides ou invalides
stations_clean = df["station"].dropna()
stations_clean = stations_clean[~stations_clean.astype(str).str.lower().isin(['nan', 'none', ''])].unique()

# Multiselect avec uniquement les stations valides
st_filter = st.sidebar.multiselect(
    "Location Name:",
    options=sorted(stations_clean),
    default=sorted(stations_clean)
)

month_filter = st.sidebar.multiselect(
    "Month:",
    options=sorted(df["month"].unique()),
    default=sorted(df["month"].unique())
)

temp_filter = st.sidebar.slider(
    "Temperature °C:",
    min_value=float(df["TEMP"].min()),
    max_value=float(df["TEMP"].max())
)

# Filtrage
df_selection = df.query(
    "station == @st_filter & month == @month_filter & TEMP >= @temp_filter"
)

# ----- KPIs -----

st.title(":bar_chart: Kaikai Air Quality Dashboard")
st.markdown("##")

day_count = df_selection["date"].nunique()
average_temp = round(df_selection["TEMP"].mean(), 1)
average_CO2 = round(df_selection["CO"].mean(), 2)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Days in Total", day_count)
col2.metric("Average Temp °C", average_temp)
col3.metric("Average CO2", average_CO2)
col4.metric("PM2.5/PM10/CO2", "50/60/700⚠️")

st.markdown("---")

# ----- CHARTS -----

grouped = df_selection.groupby(['month', 'station'])[['PM2.5', 'PM10', 'CO', 'O3']].mean().reset_index()

fig = px.line(grouped, x="month", y="PM2.5", color="station", markers=True,
              title='Average PM2.5 Particles').update_layout(xaxis_title="Month", yaxis_title="PM2.5 (μg/m³)")

fig2 = px.line(grouped, x="month", y="PM10", color="station", markers=True,
               title='Average PM10 Particles').update_layout(xaxis_title="Month", yaxis_title="PM10 (μg/m³)")

left_column, right_column = st.columns(2)
left_column.plotly_chart(fig, use_container_width=True)
right_column.plotly_chart(fig2, use_container_width=True)

# Autres graphiques (CO, O3)
fig3 = px.line(grouped, x="month", y="CO", color="station", markers=True,
               title='Average CO2 (Carbon Dioxide)').update_layout(xaxis_title="Month", yaxis_title="CO (μg/m³)")

fig4 = px.bar(grouped, x='month', y='O3', color="station",
              title='Average TEMP Concentration').update_layout(xaxis_title="Month", yaxis_title="O3 (μg/m³)")

left_column, right_column = st.columns(2)
left_column.plotly_chart(fig3, use_container_width=True)
right_column.plotly_chart(fig4, use_container_width=True)

st.write("""
    <div style='text-align:center;'>
        <h5>The higher values of PM2.5, PM10, CO2, and TEMP, the worse air quality.</h5>
    </div>
    """, unsafe_allow_html=True)

# ----- TITRE -----
st.markdown("---")
st.subheader("📈 Pollutants Over Time & 🌡️ Température / Humidité")

# 🎯 Sélection commune (à l'extérieur des colonnes)


pollutants = ['PM2.5', 'PM10', 'CO', 'O3']
selected_pollutants = st.multiselect(
    '🧪 Sélectionne les polluants à afficher :', 
    pollutants, 
    default=['PM2.5', 'PM10']
)

# Nettoyage des noms de station
stations_clean = df_selection['station'].dropna()
stations_clean = stations_clean[~stations_clean.astype(str).str.lower().isin(['nan', 'none', ''])]
stations = stations_clean.unique()

selected_station = st.selectbox(
    '📍 Sélectionne une station :', 
    sorted(stations)
)

# Filtrer les données pour la station choisie
station_data = df_selection[df_selection['station'] == selected_station]


# 📊 Organisation des 2 graphiques côte à côte
col1, col2 = st.columns(2)

# ----- GRAPHIQUES CÔTE À CÔTE AVEC ALIGNEMENT -----

col1, col2 = st.columns(2)

# ----- GRAPHIQUE 1 : POLLUTANTS OVER TIME -----
with col1:
    sns.set_style("white")
    fig_pollutants, ax_pollutants = plt.subplots(figsize=(6, 4))  # Hauteur fixe pour alignement

    for pollutant in selected_pollutants:
        sns.lineplot(
            data=station_data,
            x='datetime',
            y=pollutant,
            label=pollutant,
            ax=ax_pollutants,
            ci=None,
            linewidth=0.6
        )

    ax_pollutants.set_xlabel('Date')
    ax_pollutants.set_ylabel('Niveau de pollution (μg/m³)')
    ax_pollutants.legend(loc='upper left', bbox_to_anchor=(1, 1))
    sns.despine()

    st.pyplot(fig_pollutants)

# ----- GRAPHIQUE 2 : TEMP / DEWP OVER TIME -----
with col2:
    fig_meteo_plotly = px.line(
        station_data,
        x='datetime',
        y=['TEMP', 'DEWP'],
        labels={'value': 'Mesure', 'variable': 'Variable'},
        template='plotly_white'
    )

    fig_meteo_plotly.update_traces(mode='lines+markers')
    fig_meteo_plotly.update_layout(
        title=f"Évolution Température / Humidité - {selected_station}",
        legend_title_text='Paramètre',
        yaxis_title='Valeur',
        xaxis_title='Date',
        hovermode='x unified',
        height=400  # Même hauteur que le graphique de gauche
    )

    st.plotly_chart(fig_meteo_plotly, use_container_width=True)



# ----- CARTE INTERACTIVE -----

px.set_mapbox_access_token("pk.eyJ1IjoibW91c3RhcGhhLWthaWthaSIsImEiOiJjbTlsa3R1amswMDJ3MmpzZTQweTd0ZnF0In0.IQznUtUfizojQwA2CxlWbw")

data = {
    "Location Name": [
        "Université de Thiès", "Ecole Elhadj Mbaye Diop, Ouakam, Dakar",
        "Ecole Elémentaire Ndiangué, Richard-Toll", "Lycée Technique André Peytavin, Saint-Louis",
        "Lycée de Bargny, Rufisque", "Lycée Cheikh Mouhamadou Moustapha Mbacké, Diourbel",
        "Ecole Elhadj Mbaye Diop (Multimedia), Ouakam, Dakar", "kaikai_office(indoor)",
        "Ecole Notre Dame des Victoires, Diourbel", "Station de référence, Pikine"
    ],
    "Latitude": [14.794498, 14.720079, 16.457985, 16.019319, 14.694865, 14.661614, 14.720079, 14.733916, 14.653855, 14.744458],
    "Longitude": [-16.961053, -17.490598, -15.705461, -16.490593, -17.224226, -16.231110, -17.490598, -17.495694, -16.230600, -17.401711],
    "PM2.5": [54, 61, 72, 50, 66, 68, 61, 55, 69, 60]
}

df_coords = pd.DataFrame(data)

fig_map = px.scatter_mapbox(
    df_coords,
    lat="Latitude",
    lon="Longitude",
    hover_name="Location Name",
    hover_data=["PM2.5"],
    size="PM2.5",
    color="PM2.5",
    color_continuous_scale="OrRd",
    zoom=10.4,
    center={"lat": 14.75, "lon": -17.23},
    size_max=40,
    height=600,
    mapbox_style="satellite-streets"
)
fig_map.update_traces(marker=dict(color='red'))
fig_map.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

st.markdown("## 🌍 Carte interactive des stations avec niveaux de PM2.5")
st.plotly_chart(fig_map)

# ----- MASQUER LES ÉLÉMENTS STREAMLIT PAR DÉFAUT -----

hide_st_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)
