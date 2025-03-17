import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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

    # Add prospect strength comparison
    st.subheader("🌟 System Strength vs Team Power")

    # Load prospect data
    try:
        prospect_import = pd.read_csv("attached_assets/ABL-Import.csv")
        ranked_prospects = pd.DataFrame()  # This will be populated with processed prospect data

        # Calculate prospect scores (simplified version)
        team_scores = pd.DataFrame({'team': rankings_df['team_name'].unique()})
        team_scores['power_rank'] = team_scores.index + 1

        # Create comparison visualization
        fig2 = go.Figure()

        # Add scatter plot
        fig2.add_trace(go.Scatter(
            x=team_scores['power_rank'],
            y=team_scores['prospect_score'] if 'prospect_score' in team_scores.columns else [0] * len(team_scores),
            mode='markers+text',
            marker=dict(
                size=15,
                color=team_scores['prospect_score'] if 'prospect_score' in team_scores.columns else [0] * len(team_scores),
                colorscale='viridis',
                showscale=True,
                colorbar=dict(
                    title=dict(
                        text='Prospect Score',
                        font=dict(color='white')
                    ),
                    tickfont=dict(color='white')
                )
            ),
            text=team_scores['team'].apply(lambda x: TEAM_ABBREVIATIONS.get(x, x)),
            textposition="top center",
            hovertemplate="<b>%{text}</b><br>" +
                        "Power Rank: %{x}<br>" +
                        "Prospect Score: %{y:.2f}<extra></extra>"
        ))

        # Update layout
        fig2.update_layout(
            title=dict(
                text='Prospect System Quality vs Power Rankings',
                font=dict(color='white'),
                x=0.5,
                xanchor='center'
            ),
            xaxis=dict(
                title='Power Rank',
                tickmode='linear',
                gridcolor='rgba(128,128,128,0.1)',
                title_font=dict(color='white'),
                tickfont=dict(color='white'),
                zeroline=False
            ),
            yaxis=dict(
                title='Average Prospect Score',
                gridcolor='rgba(128,128,128,0.1)',
                title_font=dict(color='white'),
                tickfont=dict(color='white'),
                zeroline=False
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=500,
            showlegend=False,
            margin=dict(l=10, r=50, t=40, b=10)
        )

        st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})

        # Add context explanation
        st.markdown("""
        #### Understanding the Metrics
        - **Power Rank**: Current team power ranking (1 being best)
        - **Prospect Score**: Average quality of prospects in the system
        - Teams in the upper left quadrant have both strong present and future outlook
        """)
    except Exception as e:
        st.error(f"Error loading prospect comparison: {str(e)}")