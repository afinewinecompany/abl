import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Dict
import plotly.graph_objects as go

# Import team colors and IDs from prospects.py
from components.prospects import MLB_TEAM_COLORS, MLB_TEAM_IDS

# Add team abbreviation mapping
TEAM_ABBREVIATIONS = {
    "Baltimore Orioles": "BAL",
    "Boston Red Sox": "BOS",
    "New York Yankees": "NYY",
    "Tampa Bay Rays": "TB",
    "Toronto Blue Jays": "TOR",
    "Chicago White Sox": "CHW",
    "Cleveland Guardians": "CLE",
    "Detroit Tigers": "DET",
    "Kansas City Royals": "KC",
    "Minnesota Twins": "MIN",
    "Houston Astros": "HOU",
    "Los Angeles Angels": "LAA",
    "Athletics": "ATH",  # Added variation
    "Oakland Athletics": "ATH",
    "Seattle Mariners": "SEA",
    "Texas Rangers": "TEX",
    "Atlanta Braves": "ATL",
    "Miami Marlins": "MIA",
    "New York Mets": "NYM",
    "Philadelphia Phillies": "PHI",
    "Washington Nationals": "WSH",
    "Chicago Cubs": "CHC",
    "Cincinnati Reds": "CIN",
    "Milwaukee Brewers": "MIL",
    "Pittsburgh Pirates": "PIT",
    "St. Louis Cardinals": "STL",
    "Arizona Diamondbacks": "ARI",
    "Colorado Rockies": "COL",
    "Los Angeles Dodgers": "LAD",
    "San Diego Padres": "SD",
    "San Francisco Giants": "SF"
}

DIVISIONS = {
    "AL East": ["Baltimore Orioles", "Boston Red Sox", "New York Yankees", "Tampa Bay Rays", "Toronto Blue Jays"],
    "AL Central": ["Chicago White Sox", "Cleveland Guardians", "Detroit Tigers", "Kansas City Royals", "Minnesota Twins"],
    "AL West": ["Houston Astros", "Los Angeles Angels", "Oakland Athletics", "Seattle Mariners", "Texas Rangers"],
    "NL East": ["Atlanta Braves", "Miami Marlins", "New York Mets", "Philadelphia Phillies", "Washington Nationals"],
    "NL Central": ["Chicago Cubs", "Cincinnati Reds", "Milwaukee Brewers", "Pittsburgh Pirates", "St. Louis Cardinals"],
    "NL West": ["Arizona Diamondbacks", "Colorado Rockies", "Los Angeles Dodgers", "San Diego Padres", "San Francisco Giants"]
}

def calculate_points_modifier(total_points: float, all_teams_points: pd.Series) -> float:
    """Calculate points modifier based on total points ranking"""
    sorted_points = all_teams_points.sort_values(ascending=False)
    group_size = len(sorted_points) // 10
    rank = sorted_points[sorted_points >= total_points].index.min()
    group = rank // group_size
    return 1 + (0.1 * (9 - group))  # 1.9x for top group, 1.0x for bottom group

def calculate_hot_cold_modifier(recent_record: float) -> float:
    """Calculate hot/cold modifier based on recent performance"""
    if recent_record >= 0.800:  # Group 1
        return 1.5
    elif recent_record >= 0.650:  # Group 2
        return 1.4
    elif recent_record >= 0.500:  # Group 3
        return 1.3
    elif recent_record >= 0.350:  # Group 4
        return 1.2
    elif recent_record >= 0.200:  # Group 5
        return 1.1
    else:  # Group 6
        return 1.0

def calculate_power_score(row: pd.Series, all_teams_data: pd.DataFrame, include_division_factor: bool = True) -> float:
    """Calculate power score based on weekly average, points modifier, and hot/cold modifier"""
    weekly_avg = row['total_points'] / max(row['weeks_played'], 1)
    points_mod = calculate_points_modifier(row['total_points'], all_teams_data['total_points'])

    total_recent_games = row['recent_wins'] + row['recent_losses']
    recent_record = row['recent_wins'] / total_recent_games if total_recent_games > 0 else 0.5
    hot_cold_mod = calculate_hot_cold_modifier(recent_record)

    score = (weekly_avg * points_mod) * hot_cold_mod

    if include_division_factor:
        score *= row['division_factor']

    return score

def get_team_division(team_name: str) -> str:
    """Get the division for a given team"""
    for division, teams in DIVISIONS.items():
        if team_name in teams:
            return division
    return "Unknown"

def render_division_rankings(rankings_df: pd.DataFrame, division_name: str):
    """Render rankings for a specific division"""
    division_rankings = rankings_df[rankings_df['division'] == division_name].copy()
    division_rankings = division_rankings.sort_values('division_power_score', ascending=False).reset_index(drop=True)

    st.markdown(f"### {division_name}")

    for idx, row in division_rankings.iterrows():
        team_colors = MLB_TEAM_COLORS.get(row['team_name'], 
                                       {'primary': '#1a1c23', 'secondary': '#2d2f36', 'accent': '#FFFFFF'})
        st.markdown(f"""
            <div style="
                padding: 0.75rem;
                background: linear-gradient(135deg, {team_colors['primary']}80 0%, {team_colors['secondary']}80 100%);
                border-radius: 8px;
                margin: 0.5rem 0;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <span style="color: white; font-size: 1.1rem; font-weight: bold;">#{idx + 1}</span>
                        <div>
                            <div style="font-weight: bold; color: white;">{row['team_name']}</div>
                            <div style="font-size: 0.8rem; color: rgba(255,255,255,0.7);">
                                W: {row['wins']} | Win%: {row['winning_pct']:.3f}
                            </div>
                        </div>
                    </div>
                    <span style="font-weight: bold; font-size: 1.2rem; color: white;">
                        {row['division_power_score']:.1f}
                    </span>
                </div>
            </div>
        """, unsafe_allow_html=True)

def render(standings_data: pd.DataFrame):
    """Render power rankings section"""
    st.header("⚾ Power Rankings")

    # Calculate rankings
    rankings_df = standings_data.copy()

    # Add required fields for power score calculation
    rankings_df['total_points'] = rankings_df['wins'] * 2
    rankings_df['weeks_played'] = rankings_df['wins'] + rankings_df['losses']
    rankings_df['recent_wins'] = rankings_df['wins'].rolling(window=3, min_periods=1).mean()
    rankings_df['recent_losses'] = rankings_df['losses'].rolling(window=3, min_periods=1).mean()

    # Add division information
    rankings_df['division'] = rankings_df['team_name'].apply(get_team_division)
    rankings_df['division_factor'] = rankings_df['division'].map({
        "AL East": 1.1,
        "AL West": 1.05,
        "NL East": 1.05,
        "NL West": 1.0,
        "AL Central": 0.95,
        "NL Central": 0.95
    })

    # Calculate both regular and division-adjusted power scores
    rankings_df['power_score'] = rankings_df.apply(
        lambda x: calculate_power_score(x, rankings_df, include_division_factor=False), axis=1
    )
    rankings_df['division_power_score'] = rankings_df.apply(
        lambda x: calculate_power_score(x, rankings_df, include_division_factor=True), axis=1
    )

    # Sort by regular power score for overall rankings
    rankings_df = rankings_df.sort_values('power_score', ascending=False).reset_index(drop=True)

    # Display top 3 teams
    st.subheader("🏆 League Leaders")
    col1, col2, col3 = st.columns(3)

    for idx, (col, (_, row)) in enumerate(zip([col1, col2, col3], rankings_df.head(3).iterrows())):
        with col:
            team_colors = MLB_TEAM_COLORS.get(row['team_name'], 
                                           {'primary': '#1a1c23', 'secondary': '#2d2f36', 'accent': '#FFFFFF'})
            st.markdown(f"""
                <div style="
                    padding: 1rem;
                    background: linear-gradient(135deg, {team_colors['primary']} 0%, {team_colors['secondary']} 100%);
                    border-radius: 12px;
                    margin: 0.5rem 0;
                    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
                    animation: slideInUp 0.6s ease-out {idx * 0.1}s both;">
                    <h3 style="margin:0; color: white;">#{idx + 1}</h3>
                    <h4 style="margin:0.5rem 0; color: white;">{row['team_name']}</h4>
                    <p style="margin:0; font-size: 1.2rem; color: #fafafa;">
                        {row['power_score']:.1f}
                    </p>
                    <p style="margin:0; font-size: 0.8rem; color: rgba(255,255,255,0.7);">
                        {row['division']}
                    </p>
                </div>
            """, unsafe_allow_html=True)

    # Show remaining teams in overall rankings
    st.markdown("### Complete Power Rankings")
    remaining_teams = rankings_df.iloc[3:]
    for i, (_, row) in enumerate(remaining_teams.iterrows()):
        team_colors = MLB_TEAM_COLORS.get(row['team_name'], 
                                       {'primary': '#1a1c23', 'secondary': '#2d2f36', 'accent': '#FFFFFF'})
        st.markdown(f"""
            <div style="
                padding: 0.75rem;
                background: linear-gradient(135deg, {team_colors['primary']}80 0%, {team_colors['secondary']}80 100%);
                border-radius: 8px;
                margin: 0.5rem 0;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <span style="color: white; font-size: 1.1rem; font-weight: bold;">#{i + 4}</span>
                        <div>
                            <div style="font-weight: bold; color: white;">{row['team_name']}</div>
                            <div style="font-size: 0.8rem; color: rgba(255,255,255,0.7);">
                                {row['division']} | Win%: {row['winning_pct']:.3f}
                            </div>
                        </div>
                    </div>
                    <span style="font-weight: bold; font-size: 1.2rem; color: white;">
                        {row['power_score']:.1f}
                    </span>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # Add divisional rankings
    st.markdown("## Rankings by Division")
    st.markdown("""
        <div style="
            padding: 1rem;
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
            margin: 1rem 0;">
            <p style="margin:0; color: rgba(255,255,255,0.8);">
                Division rankings include the division strength factor:
                <br>• AL East: 1.1x
                <br>• AL West & NL East: 1.05x
                <br>• NL West: 1.0x
                <br>• AL/NL Central: 0.95x
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Create tabs for leagues
    al_tab, nl_tab = st.tabs(["American League", "National League"])

    with al_tab:
        col1, col2, col3 = st.columns(3)
        with col1:
            render_division_rankings(rankings_df, "AL East")
        with col2:
            render_division_rankings(rankings_df, "AL Central")
        with col3:
            render_division_rankings(rankings_df, "AL West")

    with nl_tab:
        col1, col2, col3 = st.columns(3)
        with col1:
            render_division_rankings(rankings_df, "NL East")
        with col2:
            render_division_rankings(rankings_df, "NL Central")
        with col3:
            render_division_rankings(rankings_df, "NL West")

    # Add visualization
    st.subheader("📈 Power Score Distribution")

    # Create figure with both regular and division-adjusted scores
    fig = go.Figure()

    # Regular power scores
    fig.add_trace(go.Bar(
        name="Base Power Score",
        x=rankings_df['team_name'],
        y=rankings_df['power_score'],
        marker_color=rankings_df['division'].map({
            "AL East": "#FF6B6B",
            "AL Central": "#4ECDC4",
            "AL West": "#95A5A6",
            "NL East": "#F39C12",
            "NL Central": "#3498DB",
            "NL West": "#2ECC71"
        })
    ))

    # Division-adjusted scores (transparent overlay)
    fig.add_trace(go.Bar(
        name="Division-Adjusted Score",
        x=rankings_df['team_name'],
        y=rankings_df['division_power_score'],
        marker=dict(
            color='rgba(255, 255, 255, 0.3)',
            line=dict(color='rgba(255, 255, 255, 0.5)', width=1)
        )
    ))

    fig.update_layout(
        barmode='overlay',
        title="Team Power Scores (with Division Adjustment Overlay)",
        xaxis_tickangle=-45,
        showlegend=True,
        height=500,
        template="plotly_dark",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )

    st.plotly_chart(fig, use_container_width=True)

    # Add prospect strength comparison (unchanged)
    st.subheader("🌟 System Strength vs Team Power")

    # Load prospect data
    try:
        prospect_import = pd.read_csv("attached_assets/ABL-Import.csv")

        # Calculate prospect scores
        team_scores = pd.DataFrame({'team': rankings_df['team_name'].unique()})
        team_scores['power_rank'] = team_scores.index + 1

        # Add prospect data processing here.  This is a placeholder, needs real logic.
        team_scores['prospect_score'] = 0  # Placeholder for actual prospect scores

        # Create comparison visualization
        fig2 = go.Figure()

        # Add scatter plot
        fig2.add_trace(go.Scatter(
            x=team_scores['power_rank'],
            y=team_scores['prospect_score'],
            mode='markers+text',
            marker=dict(
                size=15,
                color=team_scores['prospect_score'],
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
            text=[TEAM_ABBREVIATIONS.get(team, team) for team in team_scores['team']],
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