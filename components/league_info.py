import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Dict

def calculate_prospect_score(ranking: int) -> float:
    """Calculate prospect score based on ranking"""
    if pd.isna(ranking):
        return 0
    return 100 * (0.95 ** (ranking - 1))

def render(league_data: Dict, roster_data: pd.DataFrame = None):
    """Render league information section"""
    st.header("League Information")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("League Name", league_data['name'])
        st.metric("Season", league_data['season'])

    with col2:
        st.metric("Number of Teams", league_data['teams'])
        st.metric("Sport", league_data['sport'])

    with col3:
        st.metric("Draft Type", league_data['scoring_type'])
        st.metric("Scoring Period", league_data['scoring_period'])

    st.divider()

    # Add Prospect Power Rankings if roster data is provided
    if roster_data is not None:
        st.header("🌟 League Prospect Power Rankings")

        # Read prospect rankings
        prospect_rankings = pd.read_csv("attached_assets/2025 Dynasty Dugout Offseason Rankings - Jan 25 Prospects.csv")
        prospect_rankings['prospect_score'] = prospect_rankings['Ranking'].apply(calculate_prospect_score)

        # Calculate team prospect scores
        teams = roster_data['team'].unique()
        team_prospect_scores = []

        for team in teams:
            team_minors = roster_data[
                (roster_data['team'] == team) & 
                (roster_data['status'].str.upper() == 'MINORS')
            ]

            # Clean names for matching
            team_minors['clean_name'] = team_minors['player_name'].apply(lambda x: x.strip())
            prospect_rankings['clean_name'] = prospect_rankings['Player'].apply(lambda x: x.strip())

            team_prospects = pd.merge(
                team_minors,
                prospect_rankings[['clean_name', 'prospect_score']],
                left_on='clean_name',
                right_on='clean_name',
                how='left'
            )

            total_score = team_prospects['prospect_score'].sum()
            avg_score = team_prospects['prospect_score'].mean()
            ranked_prospects = len(team_prospects[team_prospects['prospect_score'] > 0])

            team_prospect_scores.append({
                'team': team,
                'total_score': total_score,
                'average_score': avg_score,
                'ranked_prospects': ranked_prospects
            })

        # Create prospect rankings DataFrame
        prospect_rankings_df = pd.DataFrame(team_prospect_scores)
        prospect_rankings_df = prospect_rankings_df.sort_values('total_score', ascending=False)
        prospect_rankings_df = prospect_rankings_df.reset_index(drop=True)
        prospect_rankings_df.index = prospect_rankings_df.index + 1

        # Display rankings table
        st.subheader("📊 Team Rankings")
        st.dataframe(
            prospect_rankings_df,
            column_config={
                "team": "Team",
                "total_score": st.column_config.NumberColumn(
                    "Total Prospect Score",
                    format="%.1f"
                ),
                "average_score": st.column_config.NumberColumn(
                    "Average Prospect Score",
                    format="%.1f"
                ),
                "ranked_prospects": "Number of Ranked Prospects"
            },
            hide_index=False
        )

        # Visualize prospect rankings
        st.subheader("📈 Power Rankings Distribution")
        fig = px.bar(
            prospect_rankings_df,
            x='team',
            y='total_score',
            title='Team Prospect Power Rankings',
            labels={'team': 'Team', 'total_score': 'Total Prospect Score'},
            color='total_score',
            color_continuous_scale='viridis'
        )
        fig.update_layout(
            xaxis_tickangle=-45,
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)