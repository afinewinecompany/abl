import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Dict

def calculate_power_score(row: pd.Series) -> float:
    """Calculate power score based on multiple factors"""
    win_weight = 0.4
    pct_weight = 0.4
    gb_weight = 0.2
    
    # Normalize games back (inverse because lower is better)
    max_gb = row['games_back'].max() if isinstance(row['games_back'], pd.Series) else row['games_back']
    gb_score = 1 - (row['games_back'] / (max_gb + 1))
    
    return (
        (row['wins'] * win_weight) + 
        (row['winning_pct'] * 100 * pct_weight) + 
        (gb_score * 100 * gb_weight)
    )

def render(standings_data: pd.DataFrame):
    """Render power rankings section"""
    st.header("⚾ Power Rankings")
    st.markdown("""
    <style>
    .power-ranking {
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
        background-color: #f0f2f6;
    }
    .top-team {
        background-color: #28a745;
        color: white;
    }
    .trending-up {
        color: #28a745;
    }
    .trending-down {
        color: #dc3545;
    }
    </style>
    """, unsafe_allow_html=True)

    # Calculate power rankings
    rankings_df = standings_data.copy()
    rankings_df['power_score'] = rankings_df.apply(calculate_power_score, axis=1)
    rankings_df = rankings_df.sort_values('power_score', ascending=False).reset_index(drop=True)
    rankings_df.index = rankings_df.index + 1  # Start ranking from 1

    # Display top teams
    st.subheader("🏆 Top Performers")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("1st Place", 
                 rankings_df.iloc[0]['team_name'],
                 f"Score: {rankings_df.iloc[0]['power_score']:.1f}")
    with col2:
        st.metric("2nd Place", 
                 rankings_df.iloc[1]['team_name'],
                 f"Score: {rankings_df.iloc[1]['power_score']:.1f}")
    with col3:
        st.metric("3rd Place", 
                 rankings_df.iloc[2]['team_name'],
                 f"Score: {rankings_df.iloc[2]['power_score']:.1f}")

    # Power Rankings Table
    st.subheader("📊 Complete Power Rankings")
    st.dataframe(
        rankings_df,
        column_config={
            "team_name": "Team",
            "wins": "Wins",
            "winning_pct": st.column_config.NumberColumn(
                "Win %",
                format="%.3f"
            ),
            "power_score": st.column_config.NumberColumn(
                "Power Score",
                format="%.1f"
            )
        },
        hide_index=False,
        column_order=["team_name", "wins", "winning_pct", "power_score"]
    )

    # Visualization
    st.subheader("📈 Power Rankings Distribution")
    fig = px.bar(
        rankings_df,
        x='team_name',
        y='power_score',
        title='Team Power Scores',
        color='power_score',
        color_continuous_scale='viridis',
        labels={'team_name': 'Team', 'power_score': 'Power Score'}
    )
    fig.update_layout(
        xaxis_tickangle=-45,
        showlegend=False,
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)
