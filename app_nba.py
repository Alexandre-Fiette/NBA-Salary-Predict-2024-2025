import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import joblib

# ==========================================
# 1. CONFIGURATION
# ==========================================
st.set_page_config(page_title="NBA Oracle", page_icon="🔮", layout="wide")

# ==========================================
# 2. CHARGEMENT & FUSION
# ==========================================
@st.cache_data
def load_data():
    try:
        # 1. Chargement des prédictions (IA 2024)
        df = pd.read_csv('nba_predictions.csv')
        
        # 2. Chargement des salaires futurs (2025-26)
        try:
            df_future = pd.read_csv('salaries2025.csv', encoding='latin-1', sep=None, engine='python')
            
            # Nettoyage Colonne '2025-26'
            target_col = '2025-26' 
            # Si ta colonne a un autre nom dans ton fichier, change-le ici (ex: 'Salary 2025')
            
            if target_col in df_future.columns:
                col_futur = df_future[target_col].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False)
                df_future['Salary_Next_Year'] = pd.to_numeric(col_futur, errors='coerce')
                
                # Fusion
                df = pd.merge(df, df_future[['Player', 'Salary_Next_Year']], on='Player', how='left')
                df['Salary_Next_Year'] = df['Salary_Next_Year'].fillna(0) # Remplir les vides
            else:
                df['Salary_Next_Year'] = 0
                
        except FileNotFoundError:
            df['Salary_Next_Year'] = 0 # Si pas de fichier 2025, on met 0
        
        # 3. Normalisation pour Radar Chart
        stats_cols = ['PTS', 'TRB', 'AST', 'STL', 'BLK']
        max_vals = df[stats_cols].max()
        for c in stats_cols:
            df[f'{c}_norm'] = df[c] / max_vals[c] if max_vals[c] > 0 else 0
            
        avg_league_norm = df[[f'{c}_norm' for c in stats_cols]].mean()
        
        return df, avg_league_norm
        
    except FileNotFoundError:
        st.error("⚠️ Fichier 'nba_predictions.csv' manquant. Lance ml_logic.py !")
        st.stop()

data_load = load_data()
df = data_load[0]
avg_league = data_load[1]

# ==========================================
# 3. SIDEBAR
# ==========================================
st.sidebar.image("https://cdn.nba.com/logos/leagues/logo-nba.svg", width=80)
st.sidebar.title("NBA Analytics")
st.sidebar.info("Application d'analyse salariale basée sur le Machine Learning (Random Forest).")

# ==========================================
# 4. NAVIGATION (LES 3 ONGLETS)
# ==========================================
st.title("🏀 NBA Moneyball : Analyse & Prédictions")

tab_market, tab_scout, tab_oracle = st.tabs([
    "📊 Marché 2024 (Tops/Flops)", 
    "👤 Player Scout (Profil)", 
    "🔮 Oracle (Futur 2025)"
])

# ---------------------------------------------------------
# ONGLET 1 : MARCHÉ 2024 (Comme avant)
# ---------------------------------------------------------
with tab_market:
    st.header("Analyse de la Saison Actuelle (2024-25)")
    
    col_graph, col_kpi = st.columns([2, 1])
    
    with col_graph:
        st.subheader("Salaire Réel vs Juste Prix (IA)")
        fig = px.scatter(
            df, x="Salary", y="Predicted_Salary", hover_name="Player",
            color="Difference", color_continuous_scale="RdBu", size="PTS",
            labels={"Salary": "Salaire Actuel ($)", "Predicted_Salary": "Estimation IA ($)"},
            height=450
        )
        fig.add_shape(type="line", x0=0, y0=0, x1=60000000, y1=60000000, line=dict(color="White", dash="dash"))
        st.plotly_chart(fig, use_container_width=True)
        
    with col_kpi:
        st.subheader("💡 Le concept")
        st.info("""
        **Comment lire ce graphique ?**
        
        - **Points Bleus** (Au-dessus de la ligne) : Joueurs **SOUS-PAYÉS**. Ils produisent plus que leur salaire.
        - **Points Rouges** (En dessous) : Joueurs **SUR-PAYÉS**.
        - **Ligne Pointillée** : Le salaire parfait.
        """)

    st.markdown("---")
    
    # TES LISTES STEAL / BUST
    col_steal, col_over = st.columns(2)
    df_veterans = df[df['Age'] > 22].copy()
    
    with col_steal:
        st.subheader("💎 Top 5 Pépites (Steals)")
        steals = df_veterans.sort_values(by='Difference', ascending=False).head(5)
        for _, row in steals.iterrows():
            with st.container(border=True):
                st.markdown(f"**{row['Player']}** ({row['Pos']})")
                st.caption(f"Actuel: ${row['Salary']/1e6:.1f}M ➔ Estimé: ${row['Predicted_Salary']/1e6:.1f}M")
                st.success(f"Gain potentiel : +${row['Difference']/1e6:.1f}M")

    with col_over:
        st.subheader("💸 Top 5 Arnaques (Busts)")
        overpaid = df_veterans.sort_values(by='Difference', ascending=True).head(5)
        for _, row in overpaid.iterrows():
            with st.container(border=True):
                st.markdown(f"**{row['Player']}** ({row['Pos']})")
                st.caption(f"Actuel: ${row['Salary']/1e6:.1f}M ➔ Estimé: ${row['Predicted_Salary']/1e6:.1f}M")
                st.error(f"Perte de valeur : -${abs(row['Difference'])/1e6:.1f}M")

# ---------------------------------------------------------
# ONGLET 2 : PLAYER SCOUT (Radar & Identité)
# ---------------------------------------------------------
with tab_scout:
    st.header("🔎 Fiche Joueur")
    
    # Sélecteur spécifique
    player_list = df['Player'].sort_values().unique()
    selected_player = st.selectbox("Rechercher un joueur :", player_list)
    
    p_data = df[df['Player'] == selected_player].iloc[0]
    
    st.markdown("---")
    col_id, col_verdict = st.columns([1, 2])
    
    with col_id:
        st.subheader(p_data['Player'])
        st.markdown(f"**{p_data['Pos']}** | {int(p_data['Age'])} ans | {int(p_data['G'])} Matchs")
        
    with col_verdict:
        diff = p_data['Difference'] / 1e6
        if diff > 10: status, color = "💎 PÉPITE", "green"
        elif diff > 2: status, color = "✅ BONNE AFFAIRE", "#4CAF50"
        elif diff < -10: status, color = "🚨 ARNAQUE", "red"
        elif diff < -2: status, color = "⚠️ SUR-PAYÉ", "orange"
        else: status, color = "⚖️ JUSTE PRIX", "white"
        st.markdown(f"<h2 style='color: {color} !important;'>{status}</h2>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        c1.metric("Salaire Réel 24", f"${p_data['Salary']/1e6:.1f}M")
        c2.metric("Valeur Estimée", f"${p_data['Predicted_Salary']/1e6:.1f}M", delta=f"{diff:.1f}M")

    st.markdown("---")
    
    # RADAR CHART
    c_radar, c_stats = st.columns([1.5, 1])
    with c_radar:
        st.subheader("🕸️ Profil Athlétique")
        radar_map = {'Points': 'PTS', 'Rebonds': 'TRB', 'Passes': 'AST', 'Interceptions': 'STL', 'Contres': 'BLK'}
        categories = list(radar_map.keys())
        values_player = [p_data[f"{radar_map[c]}_norm"] for c in categories]
        values_league = [avg_league[f"{radar_map[c]}_norm"] for c in categories]
        categories += [categories[0]]
        values_player += [values_player[0]]
        values_league += [values_league[0]]
        
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(r=values_league, theta=categories, fill='toself', name='Moyenne NBA', line_color='gray', opacity=0.3))
        fig_radar.add_trace(go.Scatterpolar(r=values_player, theta=categories, fill='toself', name=p_data['Player'], line_color='#FA8320'))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=False, range=[0, 1]), bgcolor='#1E1E1E'), paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'), legend=dict(orientation="h", y=-0.1))
        st.plotly_chart(fig_radar, use_container_width=True)

    with c_stats:
        st.subheader("📊 Stats Clés")
        for c in ['PTS', 'TRB', 'AST', 'FG%', '3P%']:
            delta = p_data[c] - df[c].mean()
            fmt = "%.1f%%" if '%' in c else "%.1f"
            val = p_data[c] * 100 if '%' in c else p_data[c]
            st.metric(c, fmt % val, delta=f"{delta:.1f}")

# ---------------------------------------------------------
# ONGLET 3 : ORACLE (FUTUR vs IA)
# ---------------------------------------------------------
with tab_oracle:
    st.header("🔮 L'IA a-t-elle prédit le futur ?")
    st.write("Comparaison entre l'estimation de notre modèle (basé sur 2024) et les vrais contrats signés pour 2025-26.")
    
    # Filtre sur ceux qui ont un salaire futur
    df_futur = df[df['Salary_Next_Year'] > 0].copy()
    
    if df_futur.empty:
        st.warning("⚠️ Aucun salaire 2025-26 trouvé dans 'salaries2025.csv'. Vérifie ton fichier.")
    else:
        # GRAPHIQUE 1 : Scatter Global Futur
        st.subheader("1. Corrélation : Prédiction IA vs Réalité Future")
        fig_future = px.scatter(
            df_futur, x="Salary_Next_Year", y="Predicted_Salary", hover_name="Player",
            color="Difference", size="PTS",
            labels={"Salary_Next_Year": "VRAI Salaire 2025-26 ($)", "Predicted_Salary": "Prédiction IA ($)"},
            height=500, title="Est-ce que l'IA avait vu juste ?"
        )
        # Ligne verte de perfection
        fig_future.add_shape(type="line", x0=0, y0=0, x1=65000000, y1=65000000, line=dict(color="#00FF00", dash="solid"))
        st.plotly_chart(fig_future, use_container_width=True)
        st.caption("La ligne verte représente une prédiction parfaite. Plus les points sont proches de la ligne, plus l'IA a été précise sur le futur contrat.")

        st.markdown("---")

        # GRAPHIQUE 2 : Focus Joueur (Bar Chart Evolution)
        st.subheader("2. Évolution Salariale par Joueur")
        
        # On remet un sélecteur ici pour que l'utilisateur puisse tester
        p_oracle = st.selectbox("Voir l'évolution de :", df_futur['Player'].unique())
        
        row_oracle = df_futur[df_futur['Player'] == p_oracle].iloc[0]
        
        # Data pour le graph
        data_evo = {
            'Stade': ['1. Actuel (24-25)', '2. Juste Prix (IA)', '3. Futur (25-26)'],
            'Montant': [row_oracle['Salary'], row_oracle['Predicted_Salary'], row_oracle['Salary_Next_Year']],
            'Couleur': ['#1E88E5', '#FA8320', '#43A047'] # Bleu, Orange, Vert
        }
        df_evo = pd.DataFrame(data_evo)
        
        fig_evo = px.bar(df_evo, x='Stade', y='Montant', color='Stade', text_auto='.3s',
                         color_discrete_sequence=data_evo['Couleur'])
        fig_evo.update_layout(showlegend=False, height=400, yaxis_title="Salaire ($)")
        fig_evo.update_traces(textposition="outside")
        
        st.plotly_chart(fig_evo, use_container_width=True)
        
        # Analyse textuelle
        ecart = row_oracle['Salary_Next_Year'] - row_oracle['Predicted_Salary']
        if abs(ecart) < 3000000:
            st.success(f"🎯 **PRÉDICTION VALIDÉE !** Le salaire futur de {p_oracle} est presque identique à l'estimation de l'IA.")
        elif ecart > 0:
            st.info(f"📈 **Super Négociation :** {p_oracle} a obtenu {ecart/1e6:.1f}M$ de PLUS que ce que l'IA prédisait.")
        else:
            st.warning(f"📉 **Rabais :** {p_oracle} a signé pour {abs(ecart)/1e6:.1f}M$ de MOINS que l'estimation IA.")


# ==========================================
# FOOTER
# ==========================================
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #808080; padding-top: 10px; padding-bottom: 20px;'>
        <p>Conçu & Développé par <b>Alexandre Fiette</b></p>
        <p style='font-size: 0.8em;'>© 2025 - Tous droits réservés | Données issues de Basketball Reference & NBA Stats</p>
    </div>
    """,
    unsafe_allow_html=True
)
