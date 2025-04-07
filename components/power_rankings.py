import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
    # Define constants for calculations
    POINTS_PER_WIN = 20.0  # Points assigned per win
    
    # Calculate weekly average score - use various point sources in order of preference
    # Ensure we're working with numeric data
    fptsf = float(row.get('fptsf', 0))
    total_points = float(row.get('total_points', 0))
    points_for = float(row.get('points_for', 0))
    wins = float(row.get('wins', 0))
    winning_pct = float(row.get('winning_pct', 0))
    weeks_played = max(float(row.get('weeks_played', 1)), 1)  # Prevent division by zero
    
    # Determine which points source to use, in order of preference
    if fptsf > 0:
        points = fptsf
    elif total_points > 0:
        points = total_points
    elif points_for > 0:
        points = points_for
    else:
        points = 0
    
    # Get weekly average (points divided by weeks played)
    weekly_avg = points / weeks_played
    
    # If no points data is available, calculate based on wins consistently (not temporary)
    if points == 0:
        # Base points on wins and win percentage
        win_quality_bonus = winning_pct * 10.0  # Bonus based on win percentage
        
        # Create a meaningful score based on wins
        points = (wins * POINTS_PER_WIN) + win_quality_bonus
        weekly_avg = points / max(weeks_played, 1)
        
        st.sidebar.info(f"Using win-based calculation for {row.get('team_name', 'Unknown team')}: wins={wins}, win%={winning_pct}, calculated points={points:.1f}")
    
    # Calculate points modifier based on all teams
    # Prefer actual points, but fall back to our calculated points when needed
    if 'fptsf' in all_teams_data.columns and all_teams_data['fptsf'].sum() > 0:
        points_mod = calculate_points_modifier(points, all_teams_data['fptsf'])
    elif all_teams_data['total_points'].sum() > 0:
        points_mod = calculate_points_modifier(points, all_teams_data['total_points'])
    elif 'points_for' in all_teams_data.columns and all_teams_data['points_for'].sum() > 0:
        points_mod = calculate_points_modifier(points, all_teams_data['points_for'])
    else:
        # If no team has any points, use wins as the basis for ranking
        wins_series = all_teams_data['wins'].apply(lambda w: w * POINTS_PER_WIN)
        points_mod = calculate_points_modifier(points, wins_series)
    
    # Calculate hot/cold modifier based on recent wins
    # Set defaults for missing values
    recent_wins = float(row.get('recent_wins', 0))
    recent_losses = float(row.get('recent_losses', 0))
    
    total_recent_games = recent_wins + recent_losses
    
    # If no recent games data, use overall win percentage
    if total_recent_games == 0:
        recent_win_pct = winning_pct if winning_pct > 0 else 0.5
    else:
        recent_win_pct = recent_wins / total_recent_games
    
    hot_cold_mod = calculate_hot_cold_modifier(recent_win_pct)
    
    # Only show detailed debugging for teams with no points
    if total_points == 0:
        st.sidebar.info(f"Team: {row.get('team_name', 'Unknown')}, Weekly Avg: {weekly_avg:.2f}, Points Mod: {points_mod:.2f}, Hot/Cold: {hot_cold_mod:.2f}")
    
    # Calculate final power score
    power_score = (weekly_avg * points_mod) * hot_cold_mod
    return power_score

def render(standings_data: pd.DataFrame, power_rankings_data: dict = None, weekly_results: list = None):
    """
    Render power rankings section
    
    Args:
        standings_data: DataFrame containing standings data
        power_rankings_data: Optional dict of custom power rankings data from user input
        weekly_results: Optional list of weekly results data from user input
    """
    st.header("⚾ Power Rankings")
    st.markdown("""
        <style>
        @keyframes slideInUp {
            from {
                transform: translateY(50px);
                opacity: 0;
            }
            to {
                transform: translateY(0);
                opacity: 1;
            }
        }
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.02); }
            100% { transform: scale(1); }
        }
        @keyframes shimmer {
            0% { background-position: -200% center; }
            100% { background-position: 200% center; }
        }
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

    # Start with the enhanced standings data from the API
    rankings_df = standings_data.copy()
    
    st.sidebar.success("⚡ Using live standings data from Fantrax API")
    
    # Check if we already have these fields from API data processing
    api_data_available = all(col in rankings_df.columns for col in ['total_points', 'weeks_played'])
    
    # Use provided custom data or fetch from session state if API data is insufficient
    if not api_data_available:
        if power_rankings_data:
            # Use the provided power rankings data
            custom_data = power_rankings_data
        elif 'power_rankings_data' in st.session_state and st.session_state.power_rankings_data:
            # Use data from session state
            custom_data = st.session_state.power_rankings_data
        else:
            # No custom data available
            custom_data = {}
        
        # Apply custom data if available
        if custom_data:
            for team_name, team_data in custom_data.items():
                # Only update teams that exist in the standings_data
                if team_name in rankings_df['team_name'].values:
                    # Find the index for this team
                    idx = rankings_df[rankings_df['team_name'] == team_name].index[0]
                    # Update the data
                    # Support both fptsf and total_points in the custom data
                    if 'fptsf' in team_data:
                        rankings_df.at[idx, 'fptsf'] = team_data['fptsf']
                        rankings_df.at[idx, 'total_points'] = team_data['fptsf']  # for compatibility
                    elif 'total_points' in team_data:
                        rankings_df.at[idx, 'total_points'] = team_data['total_points']
                        rankings_df.at[idx, 'fptsf'] = team_data['total_points']  # use both fields
                    
                    rankings_df.at[idx, 'weeks_played'] = team_data['weeks_played']
        else:
            # Calculate default values if no custom data
            rankings_df['fptsf'] = rankings_df['wins'] * 20  # 20 points per win as default
            rankings_df['total_points'] = rankings_df['fptsf']  # Keep both for compatibility
            rankings_df['weeks_played'] = rankings_df['wins'] + rankings_df['losses']
    
    # Display a info message about data source
    st.info("Power rankings are calculated using live standings data from Fantrax API combined with your manual data entries for recent performance.")
    
    # Fill any missing values with defaults
    if 'fptsf' not in rankings_df.columns:
        rankings_df['fptsf'] = rankings_df['wins'] * 20  # 20 points per win
    if 'total_points' not in rankings_df.columns:
        rankings_df['total_points'] = rankings_df['fptsf']  # Use fptsf if available
    if 'weeks_played' not in rankings_df.columns:
        rankings_df['weeks_played'] = rankings_df['wins'] + rankings_df['losses']
        
    # Ensure we have numeric values for calculations
    rankings_df['fptsf'] = pd.to_numeric(rankings_df['fptsf'], errors='coerce').fillna(0)
    rankings_df['total_points'] = pd.to_numeric(rankings_df['total_points'], errors='coerce').fillna(0)
    rankings_df['weeks_played'] = pd.to_numeric(rankings_df['weeks_played'], errors='coerce').fillna(1)  # Avoid div by zero
    
    # Use provided weekly results or fetch from session state
    if weekly_results:
        # Use the provided weekly results
        weekly_data = weekly_results
    elif 'weekly_results' in st.session_state and st.session_state.weekly_results:
        # Use data from session state
        weekly_data = st.session_state.weekly_results
    else:
        # No weekly results available
        weekly_data = []
    
    # Process recent wins/losses
    if weekly_data:
        # Process weekly results to get recent wins/losses for each team
        team_names = rankings_df['team_name'].unique()
        recent_weeks = 3  # How many weeks to consider for "recent" performance
        
        # Initialize recent wins/losses columns
        rankings_df['recent_wins'] = 0
        rankings_df['recent_losses'] = 0
        
        for team_name in team_names:
            # Get this team's results
            team_results = [r for r in weekly_data if r['team'] == team_name]
            
            # Sort by week number and get the most recent X weeks
            team_results.sort(key=lambda x: x['week'], reverse=True)
            recent_results = team_results[:recent_weeks]
            
            # Count wins and losses
            recent_wins = sum(1 for r in recent_results if r['result'] == 'Win')
            recent_losses = sum(1 for r in recent_results if r['result'] == 'Loss')
            
            # Update the dataframe
            if team_name in rankings_df['team_name'].values:
                idx = rankings_df[rankings_df['team_name'] == team_name].index[0]
                rankings_df.at[idx, 'recent_wins'] = recent_wins
                rankings_df.at[idx, 'recent_losses'] = recent_losses
    else:
        # Calculate recent wins/losses using rolling mean as default
        rankings_df['recent_wins'] = rankings_df['wins'].rolling(window=3, min_periods=1).mean()
        rankings_df['recent_losses'] = rankings_df['losses'].rolling(window=3, min_periods=1).mean()

    # Calculate power scores
    rankings_df['power_score'] = rankings_df.apply(lambda x: calculate_power_score(x, rankings_df), axis=1)
    rankings_df = rankings_df.sort_values('power_score', ascending=False).reset_index(drop=True)
    rankings_df.index = rankings_df.index + 1  # Start ranking from 1
    
    # Store the calculated rankings in session state for other components to use
    st.session_state.power_rankings_calculated = rankings_df.copy()

    # Display top teams
    st.subheader("🏆 League Leaders")
    col1, col2, col3 = st.columns(3)

    # Top 3 teams with enhanced styling
    for idx, (col, (_, row)) in enumerate(zip([col1, col2, col3], rankings_df.head(3).iterrows())):
        with col:
            team_colors = MLB_TEAM_COLORS.get(row['team_name'], 
                                            {'primary': '#1a1c23', 'secondary': '#2d2f36', 'accent': '#FFFFFF'})
            team_id = MLB_TEAM_IDS.get(row['team_name'], '')
            logo_url = f"https://www.mlbstatic.com/team-logos/team-cap-on-dark/{team_id}.svg" if team_id else ""

            st.markdown(f"""
                <div style="
                    padding: 1.5rem;
                    background: linear-gradient(135deg, {team_colors['primary']} 0%, {team_colors['secondary']} 100%);
                    border-radius: 12px;
                    margin: 0.5rem 0;
                    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
                    position: relative;
                    overflow: hidden;
                    animation: slideInUp 0.6s ease-out {idx * 0.1}s both;
                ">
                    <div style="position: absolute; right: -20px; top: 50%; transform: translateY(-50%); opacity: 0.15;">
                        <img src="{logo_url}" style="width: 180px; height: 180px;" alt="Team Logo">
                    </div>
                    <div style="position: absolute; left: -10px; top: -10px; background: {team_colors['accent']}; 
                         color: {team_colors['primary']}; width: 40px; height: 40px; border-radius: 50%; 
                         display: flex; align-items: center; justify-content: center; font-weight: bold; 
                         font-size: 1.2rem; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);">
                        #{idx + 1}
                    </div>
                    <div style="position: relative; z-index: 1;">
                        <div style="font-weight: 700; font-size: 1.5rem; margin-bottom: 0.5rem; color: white;">
                            {row['team_name']}
                        </div>
                        <div style="display: flex; gap: 1rem; margin-top: 1rem;">
                            <div style="background: rgba(255,255,255,0.1); padding: 0.5rem; border-radius: 8px; flex: 1; text-align: center;">
                                <div style="font-size: 0.8rem; color: rgba(255,255,255,0.7);">Wins</div>
                                <div style="font-size: 1.2rem; color: white;">{row['wins']}</div>
                            </div>
                            <div style="background: rgba(255,255,255,0.1); padding: 0.5rem; border-radius: 8px; flex: 1; text-align: center;">
                                <div style="font-size: 0.8rem; color: rgba(255,255,255,0.7);">Win %</div>
                                <div style="font-size: 1.2rem; color: white;">{row['winning_pct']:.3f}</div>
                            </div>
                            <div style="background: rgba(255,255,255,0.1); padding: 0.5rem; border-radius: 8px; flex: 1; text-align: center;">
                                <div style="font-size: 0.8rem; color: rgba(255,255,255,0.7);">Power</div>
                                <div style="font-size: 1.2rem; color: white;">{row['power_score']:.1f}</div>
                            </div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    # Show remaining teams with similar styling
    st.markdown("### Complete Power Rankings")

    remaining_teams = rankings_df.iloc[3:]
    for i, (_, row) in enumerate(remaining_teams.iterrows()):
        team_colors = MLB_TEAM_COLORS.get(row['team_name'], 
                                        {'primary': '#1a1c23', 'secondary': '#2d2f36', 'accent': '#FFFFFF'})
        team_id = MLB_TEAM_IDS.get(row['team_name'], '')
        logo_url = f"https://www.mlbstatic.com/team-logos/team-cap-on-dark/{team_id}.svg" if team_id else ""

        st.markdown(f"""
            <div style="
                padding: 1rem;
                background: linear-gradient(135deg, {team_colors['primary']} 0%, {team_colors['secondary']} 100%);
                border-radius: 10px;
                margin: 0.5rem 0;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                position: relative;
                overflow: hidden;
                animation: slideInUp 0.6s ease-out {(i + 3) * 0.1}s both;
            ">
                <div style="position: absolute; right: -20px; top: 50%; transform: translateY(-50%); opacity: 0.15;">
                    <img src="{logo_url}" style="width: 120px; height: 120px;" alt="Team Logo">
                </div>
                <div style="position: relative; z-index: 1; display: flex; align-items: center; gap: 1rem;">
                    <div style="background: {team_colors['accent']}; color: {team_colors['primary']}; 
                         width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; 
                         justify-content: center; font-weight: bold;">
                        #{i + 4}
                    </div>
                    <div style="flex-grow: 1;">
                        <div style="font-weight: 600; color: white;">{row['team_name']}</div>
                        <div style="display: flex; gap: 1rem; margin-top: 0.5rem;">
                            <div style="background: rgba(255,255,255,0.1); padding: 0.3rem 0.6rem; border-radius: 6px; font-size: 0.9rem;">
                                <span style="color: rgba(255,255,255,0.7);">W:</span>
                                <span style="color: white;">{row['wins']}</span>
                            </div>
                            <div style="background: rgba(255,255,255,0.1); padding: 0.3rem 0.6rem; border-radius: 6px; font-size: 0.9rem;">
                                <span style="color: rgba(255,255,255,0.7);">%:</span>
                                <span style="color: white;">{row['winning_pct']:.3f}</span>
                            </div>
                            <div style="background: rgba(255,255,255,0.1); padding: 0.3rem 0.6rem; border-radius: 6px; font-size: 0.9rem;">
                                <span style="color: rgba(255,255,255,0.7);">Power:</span>
                                <span style="color: white;">{row['power_score']:.1f}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # Visualization with enhanced styling
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

    # Add prospect strength comparison
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