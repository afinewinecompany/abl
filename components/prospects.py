import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Dict

def normalize_name(name: str) -> str:
    """Normalize player name from [last], [first] to [first] [last]"""
    try:
        if ',' in name:
            last, first = name.split(',', 1)
            return f"{first.strip()} {last.strip()}"
        return name.strip()
    except:
        return name.strip()

def calculate_prospect_score(ranking: int) -> float:
    """Calculate prospect score based on ranking"""
    if pd.isna(ranking):
        return 0
    # Exponential decay scoring - higher ranked prospects worth more
    return 100 * (0.95 ** (ranking - 1))

def render(roster_data: pd.DataFrame):
    """Render prospects analysis section"""
    st.header("🌟 Prospect Analysis")
    
    # Read and process prospect rankings
    prospect_rankings = pd.read_csv("attached_assets/2025 Dynasty Dugout Offseason Rankings - Jan 25 Prospects.csv")
    prospect_rankings['Player'] = prospect_rankings['Player'].str.strip()
    prospect_rankings['prospect_score'] = prospect_rankings['Ranking'].apply(calculate_prospect_score)

    # Get all minor league players
    minors_players = roster_data[roster_data['status'].str.upper() == 'MINORS'].copy()
    minors_players['clean_name'] = minors_players['player_name'].apply(normalize_name)

    # Merge with rankings
    ranked_prospects = pd.merge(
        minors_players,
        prospect_rankings[['Player', 'Ranking', 'Tier', 'prospect_score', 'Position', 'ETA']],
        left_on='clean_name',
        right_on='Player',
        how='left'
    )

    # Team Prospect Rankings
    st.subheader("📊 Team Prospect Power Rankings")
    
    team_scores = ranked_prospects.groupby('team').agg({
        'prospect_score': ['sum', 'mean', 'count'],
        'Ranking': lambda x: x.notna().sum()
    }).reset_index()
    
    team_scores.columns = ['team', 'total_score', 'avg_score', 'total_prospects', 'ranked_prospects']
    team_scores = team_scores.sort_values('total_score', ascending=False)
    team_scores = team_scores.reset_index(drop=True)
    team_scores.index = team_scores.index + 1

    # Display team rankings
    st.dataframe(
        team_scores,
        column_config={
            "team": "Team",
            "total_score": st.column_config.NumberColumn(
                "Total Prospect Score",
                format="%.1f",
                help="Sum of all prospect scores"
            ),
            "avg_score": st.column_config.NumberColumn(
                "Average Prospect Score",
                format="%.1f",
                help="Average score per prospect"
            ),
            "total_prospects": "Total Prospects",
            "ranked_prospects": "Ranked Prospects"
        },
        hide_index=False
    )

    # Visualization
    fig = px.bar(
        team_scores,
        x='team',
        y='total_score',
        title='Team Prospect Power Rankings',
        labels={'team': 'Team', 'total_score': 'Total Prospect Score'},
        color='total_score',
        color_continuous_scale='viridis'
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

    # Individual Prospect Analysis
    st.subheader("👥 Top Prospects by Team")
    
    # Team selector
    selected_team = st.selectbox(
        "Select Team",
        options=team_scores['team'].tolist()
    )

    # Filter prospects for selected team
    team_prospects = ranked_prospects[ranked_prospects['team'] == selected_team].sort_values(
        'prospect_score', ascending=False
    )

    # Display team's prospects
    st.dataframe(
        team_prospects,
        column_config={
            "player_name": "Player",
            "Position": "Position",
            "Ranking": st.column_config.NumberColumn(
                "Overall Ranking",
                help="Industry prospect ranking"
            ),
            "Tier": "Prospect Tier",
            "ETA": "MLB ETA",
            "prospect_score": st.column_config.NumberColumn(
                "Prospect Score",
                format="%.1f",
                help="Calculated prospect value"
            )
        },
        hide_index=True
    )

    # Tier Distribution
    st.subheader("📈 Prospect Tier Distribution")
    tier_dist = ranked_prospects[ranked_prospects['Tier'].notna()].groupby(['team', 'Tier']).size().unstack(fill_value=0)
    
    fig2 = px.bar(
        tier_dist,
        title='Prospect Tier Distribution by Team',
        labels={'value': 'Number of Prospects', 'team': 'Team', 'variable': 'Tier'},
        barmode='group'
    )
    fig2.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig2, use_container_width=True)
