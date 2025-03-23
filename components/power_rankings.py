import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Dict

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
    "Cardinals": "STL",  # Added variation
    "Saint Louis Cardinals": "STL",  # Added variation
    "St Louis Cardinals": "STL",  # Added variation without period
    "St. Louis Cardinals": "STL",
    "Arizona Diamondbacks": "ARI",
    "Colorado Rockies": "COL",
    "Los Angeles Dodgers": "LAD",
    "San Diego Padres": "SD",
    "San Francisco Giants": "SF"
}

def calculate_points_modifier(total_points: float, all_teams_points: pd.Series) -> float:
    """Calculate points modifier based on total points ranking"""
    # Sort all teams by points and split into 10 groups of 3
    sorted_points = all_teams_points.sort_values(ascending=False)
    group_size = len(sorted_points) // 10
    rank = sorted_points[sorted_points >= total_points].index.min()
    group = rank // group_size
    return 1 + (0.1 * (9 - group))  # 1.9x for top group, 1.0x for bottom group

def calculate_hot_cold_modifier(recent_record: float) -> float:
    """Calculate hot/cold modifier based on recent performance"""
    # Split into 6 groups, with modifiers from 1.5x to 1.0x
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

def calculate_power_score(row: pd.Series, all_teams_data: pd.DataFrame) -> float:
    """Calculate power score based on weekly average, points modifier, and hot/cold modifier"""
    # Calculate weekly average score
    weekly_avg = row['total_points'] / max(row['weeks_played'], 1)  # Prevent division by zero

    # Calculate points modifier
    points_mod = calculate_points_modifier(row['total_points'], all_teams_data['total_points'])

    # Calculate hot/cold modifier based on recent record
    total_recent_games = row['recent_wins'] + row['recent_losses']
    recent_record = row['recent_wins'] / total_recent_games if total_recent_games > 0 else 0.5  # Default to 0.5 if no games
    hot_cold_mod = calculate_hot_cold_modifier(recent_record)

    return (weekly_avg * points_mod) * hot_cold_mod

def render(standings_data: pd.DataFrame):
    """Render power rankings section with simplified styling"""
    # Calculate power rankings
    rankings_df = standings_data.copy()
    
    # Add required fields for power score calculation
    rankings_df['total_points'] = rankings_df['wins'] * 2  # Assuming 2 points per win
    rankings_df['weeks_played'] = rankings_df['wins'] + rankings_df['losses']
    rankings_df['recent_wins'] = rankings_df['wins'].rolling(window=3, min_periods=1).mean()
    rankings_df['recent_losses'] = rankings_df['losses'].rolling(window=3, min_periods=1).mean()
    
    # Calculate power scores
    rankings_df['power_score'] = rankings_df.apply(lambda x: calculate_power_score(x, rankings_df), axis=1)
    rankings_df = rankings_df.sort_values('power_score', ascending=False).reset_index(drop=True)
    rankings_df.index = rankings_df.index + 1  # Start ranking from 1

    # Display top teams in a simple table
    st.subheader("🏆 League Leaders")
    
    # Top 3 teams highlighted
    top_teams = rankings_df.head(3).copy()
    top_teams['rank'] = [1, 2, 3]
    top_teams = top_teams[['rank', 'team_name', 'wins', 'losses', 'winning_pct', 'power_score']]
    
    # Format the table
    top_teams['winning_pct'] = top_teams['winning_pct'].apply(lambda x: f"{x:.3f}")
    top_teams['power_score'] = top_teams['power_score'].apply(lambda x: f"{x:.1f}")
    
    # Rename columns
    top_teams.columns = ['Rank', 'Team', 'Wins', 'Losses', 'Win %', 'Power Score']
    
    # Display the table
    st.dataframe(top_teams, use_container_width=True, hide_index=True)

    # Show remaining teams in a simple table
    st.subheader("Complete Power Rankings")
    
    # Format remaining teams
    remaining_teams = rankings_df.iloc[3:].copy()
    remaining_teams['rank'] = range(4, len(remaining_teams) + 4)
    remaining_teams = remaining_teams[['rank', 'team_name', 'wins', 'losses', 'winning_pct', 'power_score']]
    
    # Format the table
    remaining_teams['winning_pct'] = remaining_teams['winning_pct'].apply(lambda x: f"{x:.3f}")
    remaining_teams['power_score'] = remaining_teams['power_score'].apply(lambda x: f"{x:.1f}")
    
    # Rename columns
    remaining_teams.columns = ['Rank', 'Team', 'Wins', 'Losses', 'Win %', 'Power Score']
    
    # Display the table
    st.dataframe(remaining_teams, use_container_width=True, hide_index=True)

    # Visualization - simplified bar chart
    st.subheader("📈 Power Score Distribution")
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
        height=500,
        template="plotly_dark",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True)

    # Add prospect strength comparison - simplified
    st.subheader("🌟 System Strength vs Team Power")

    # Load prospect data
    try:
        prospect_import = pd.read_csv("attached_assets/ABL-Import.csv")

        # Calculate prospect scores
        team_scores = pd.DataFrame({'team': rankings_df['team_name'].unique()})
        team_scores['power_rank'] = team_scores.index + 1

        # Add prospect data processing here. This is a placeholder, needs real logic.
        team_scores['prospect_score'] = 0  # Placeholder for actual prospect scores

        # Create simplified comparison visualization
        fig2 = px.scatter(
            team_scores,
            x='power_rank',
            y='prospect_score',
            text=[TEAM_ABBREVIATIONS.get(team, team) for team in team_scores['team']],
            title='Prospect System Quality vs Power Rankings',
            labels={'power_rank': 'Power Rank', 'prospect_score': 'Prospect Score'},
            color='prospect_score',
            color_continuous_scale='viridis'
        )
        
        # Update text position and styling
        fig2.update_traces(
            textposition='top center',
            marker=dict(size=15)
        )
        
        # Update layout
        fig2.update_layout(
            height=500,
            template="plotly_dark",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig2, use_container_width=True)

        # Add context explanation
        st.markdown("""
        #### Understanding the Metrics
        - **Power Rank**: Current team power ranking (1 being best)
        - **Prospect Score**: Average quality of prospects in the system
        - Teams in the upper left quadrant have both strong present and future outlook
        """)
    except Exception as e:
        st.error(f"Error loading prospect comparison: {str(e)}")