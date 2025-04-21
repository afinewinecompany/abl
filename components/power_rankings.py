import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Optional, Tuple
from utils import load_rankings_history
from datetime import datetime, timedelta

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
    """Calculate points modifier based on total points ranking using a straight line distribution"""
    if all_teams_points.empty or all_teams_points.max() == all_teams_points.min():
        return 1.0  # Default value if no valid comparison can be made

    # Get min and max points
    min_points = all_teams_points.min()
    max_points = all_teams_points.max()

    # Linear scaling from 1.0 to 1.9 based on where this team's points fall in the range
    # Linear formula: y = m*x + b where:
    # m = (max_modifier - min_modifier) / (max_points - min_points)
    # b = min_modifier - m * min_points
    min_modifier = 1.0
    max_modifier = 1.9
    range_width = max_points - min_points

    if range_width == 0:  # Avoid division by zero
        return (min_modifier + max_modifier) / 2

    # Calculate scale factor (how far along the line this team's points fall)
    scale_factor = (total_points - min_points) / range_width

    # Linear interpolation between min_modifier and max_modifier
    modifier = min_modifier + (scale_factor * (max_modifier - min_modifier))

    return modifier  # Returns a value between 1.0 and 1.9 on a linear scale

def calculate_schedule_strength_modifier(team_name: str, current_period: int) -> float:
    """
    Calculate strength of schedule modifier based on how a team performed against good/bad teams.

    Args:
        team_name: The team name to calculate the modifier for
        current_period: The current scoring period (to only include completed games)

    Returns:
        float: A modifier between -1.0 and 1.0 where:
        - Positive values mean the team performed well against strong opponents
        - Negative values mean the team performed poorly against weak opponents
        - 0 means neutral performance or insufficient data
    """
    # Get debug flag from session state
    debug_modifiers = st.session_state.get('debug_modifiers', False)

    try:
        # Check if team_name is empty or None
        if not team_name:
            return 0.0

        # Load schedule data with debug output
        try:
            schedule_df = pd.read_csv("attached_assets/fantasy_baseball_schedule.csv")
            st.sidebar.info(f"Loaded schedule data with {len(schedule_df)} rows")

            # Show a sample of the data for debugging
            st.sidebar.write("Schedule sample:", schedule_df.head(3))

            # Debug the column names to ensure they match
            st.sidebar.write("Schedule columns:", schedule_df.columns.tolist())

            # Fix column name if needed - the actual CSV file has "Scoring Period" with a space
            if 'Scoring Period' in schedule_df.columns:
                scoring_period_col = 'Scoring Period'
            else:
                # Try other common variations of the column name
                potential_columns = ['ScoringPeriod', 'Period', 'Week', 'WeekNum']
                found_col = False
                for col in potential_columns:
                    if col in schedule_df.columns:
                        scoring_period_col = col
                        found_col = True
                        break

                if not found_col:
                    st.sidebar.error(f"Could not find scoring period column in schedule data.")
                    return 0.0

            st.sidebar.info(f"Using scoring period column: {scoring_period_col}")

            # Only consider completed periods - make sure column name matches exactly
            schedule_df = schedule_df[schedule_df[scoring_period_col] < current_period]

            st.sidebar.info(f"After filtering by period < {current_period}: {len(schedule_df)} rows remain")

            if len(schedule_df) == 0:
                st.sidebar.warning(f"No schedule data for periods < {current_period}")
                return 0.0  # No completed games yet

        except Exception as e:
            st.sidebar.error(f"Error loading schedule data: {str(e)}")
            return 0.0  # Error loading schedule data

        # Get team stats for FPtsF to determine team strength
        team_stats = None
        if 'standings_data' in st.session_state and isinstance(st.session_state.standings_data, pd.DataFrame):
            team_stats = st.session_state.standings_data

        if team_stats is None or 'fptsf' not in team_stats.columns:
            return 0.0  # Can't calculate strength without team stats

        # Map teams to their strength (FPtsF) - make sure team_name exists in dataframe
        if 'team_name' not in team_stats.columns:
            return 0.0

        # Create team strength dictionary with safety checks
        team_strength = {}
        for _, row in team_stats.iterrows():
            if 'team_name' in row and 'fptsf' in row:
                name = row['team_name']
                if name and isinstance(name, str):  # Make sure it's a valid string
                    team_strength[name] = float(row['fptsf'])

        if not team_strength:
            return 0.0  # No valid team strength data

        # Get average team strength
        if team_strength:
            avg_strength = sum(team_strength.values()) / len(team_strength)
        else:
            return 0.0

        # Filter games where this team played
        team_home_games = schedule_df[schedule_df['Home'] == team_name]
        team_away_games = schedule_df[schedule_df['Away'] == team_name]

        # Combine home and away games into a list of opponents
        opponents = []
        for _, row in team_home_games.iterrows():
            if 'Away' in row and isinstance(row['Away'], str):
                opponents.append({"opponent": row['Away'], "home": True})

        for _, row in team_away_games.iterrows():
            if 'Home' in row and isinstance(row['Home'], str):
                opponents.append({"opponent": row['Home'], "home": False})

        if not opponents:
            return 0.0  # No games played

        # Calculate the average strength of opponents
        opponent_strengths = []
        for game in opponents:
            opponent = game["opponent"]
            if opponent in team_strength:
                opponent_strengths.append(team_strength[opponent])

        if not opponent_strengths:
            return 0.0  # No valid opponent data

        # Safely calculate average opponent strength
        avg_opponent_strength = sum(opponent_strengths) / max(len(opponent_strengths), 1)

        # Safely get min and max values
        min_strength = min(team_strength.values())
        max_strength = max(team_strength.values())
        strength_range = max_strength - min_strength

        # Avoid division by zero
        if strength_range == 0:
            return 0.0

        # Get team's performance (FPtsF) and normalize it
        team_performance = team_strength.get(team_name, avg_strength)
        performance_percentile = (team_performance - min_strength) / strength_range

        # Calculate opponent strength percentile
        opponent_strength_percentile = (avg_opponent_strength - min_strength) / strength_range

        # Calculate relative performance (how team did vs expected against these opponents)
        expected_performance = 0.5  # Base expectation
        relative_performance = performance_percentile - expected_performance

        # Determine how much stronger the opponents are than average
        opponent_relative_strength = opponent_strength_percentile - 0.5
        
        # IMPROVED FORMULA: Include a scaling factor that doesn't unfairly penalize teams facing tough opponents
        # 1. If team is performing well (relative_performance > 0):
        #    - Against strong opponents (opponent_relative_strength > 0): big positive boost
        #    - Against weak opponents (opponent_relative_strength < 0): smaller positive boost
        # 2. If team is performing poorly (relative_performance < 0):
        #    - Against strong opponents (opponent_relative_strength > 0): small negative effect (reduced penalty)
        #    - Against weak opponents (opponent_relative_strength < 0): bigger negative effect
        
        if relative_performance >= 0:
            # Performing well - multiply by opponent strength for bigger boost against tough opponents
            modifier = relative_performance * (1.0 + opponent_relative_strength)
        else:
            # Performing poorly - reduce penalty against strong opponents
            penalty_factor = 1.0 - (opponent_relative_strength * 0.5)  # Reduce penalty up to 50% for strong opponents
            modifier = relative_performance * max(0.2, penalty_factor)  # Ensure some penalty remains

        # Log values for debugging
        st.sidebar.info(f"SoS Debug - {team_name}: perf={performance_percentile:.3f}, opp={opponent_strength_percentile:.3f}, rel={relative_performance:.3f}, mod={modifier:.3f}")
        
        # Scale modifier between -1 and 1
        return max(min(modifier, 1.0), -1.0)

    except Exception as e:
        print(f"Error calculating schedule strength modifier: {str(e)}")
        return 0.0  # Default to no modification on error

def calculate_hot_cold_modifier(win_percentage: float) -> float:
    """
    Calculate hot/cold modifier based on win percentage.
    
    The formula uses linear scaling to give teams with better records a higher modifier.
    Teams with a 100% win rate get a 1.5x bonus, teams with a 0% win rate get 1.0x (no bonus).
    
    Args:
        win_percentage: Team's win percentage (0.0 to 1.0)
        
    Returns:
        float: Hot/cold modifier between 1.0 and 1.5
    """
    # Ensure win_percentage is between 0 and 1
    win_percentage = max(0.0, min(1.0, win_percentage))
    
    # Define range for the modifier
    min_modifier = 1.0   # Modifier for 0% win rate
    max_modifier = 1.5   # Modifier for 100% win rate

    # Linear interpolation: y = min_modifier + (x * (max_modifier - min_modifier))
    # where x is the win percentage from 0.0 to 1.0
    modifier = min_modifier + (win_percentage * (max_modifier - min_modifier))
    
    # Return the calculated modifier
    return modifier

def get_previous_rankings() -> Dict[str, dict]:
    """
    Get the previous week's power rankings data and calculate week-to-week score changes
    
    Returns:
        Dict mapping team names to a dict with 'prev_rank' and 'score_change'
    """
    previous_rankings = {}
    
    try:
        # Load historical team points data from our CSV file
        history_df = pd.read_csv("data/team_fptsf_history.csv")
        
        # If no history exists, return empty dict
        if history_df.empty:
            print("No historical team points data found.")
            return {}
        
        # Get week 2 data (previous week)
        week2_data = history_df[history_df['week'] == 2]
        
        # Get week 3 data (current week)
        week3_data = history_df[history_df['week'] == 3]
        
        # Create dataframes with team and fptsf for each week
        week2_df = week2_data[['team', 'fptsf']].copy()
        week3_df = week3_data[['team', 'fptsf']].copy()
        
        # Rename columns to distinguish weeks
        week2_df.columns = ['team', 'week2_fptsf']
        week3_df.columns = ['team', 'week3_fptsf']
        
        # Merge the dataframes to calculate week-to-week changes
        combined_df = pd.merge(week2_df, week3_df, on='team', how='inner')
        
        # Calculate the points per week (what was earned in week 3 only)
        combined_df['week3_only_points'] = combined_df['week3_fptsf'] - combined_df['week2_fptsf']
        
        # Sort by week 2 points for ranking
        week2_ranked = week2_df.sort_values('week2_fptsf', ascending=False).reset_index(drop=True)
        week2_ranked.index = week2_ranked.index + 1  # Start ranking from 1
        week2_ranked['prev_rank'] = week2_ranked.index
        
        # Create rankings dictionary with previous rank and score change
        for _, row in combined_df.iterrows():
            team_name = row['team']
            # Get the previous rank from week 2
            prev_rank_row = week2_ranked[week2_ranked['team'] == team_name]
            prev_rank = prev_rank_row['prev_rank'].iloc[0] if not prev_rank_row.empty else 0
            
            # Calculate score change
            score_change = row['week3_only_points']
            
            # Store both previous rank and score change
            previous_rankings[team_name] = {
                'prev_rank': prev_rank,
                'score_change': score_change
            }
        
        # Debug info - print all previous rankings and score changes
        print("Score changes from week 2 to week 3:")
        for team, data in previous_rankings.items():
            print(f"  {team}: Rank {data['prev_rank']}, Week 3 Score Change: {data['score_change']:.2f}")
    
    except Exception as e:
        # Log the error but return an empty dict to avoid crashing
        print(f"Error getting previous rankings: {str(e)}")
        import traceback
        traceback.print_exc()
        
    return previous_rankings

def calculate_power_score(row: pd.Series, all_teams_data: pd.DataFrame) -> float:
    """Calculate power score based on weekly average, points modifier, hot/cold modifier, and strength of schedule"""
    # Get debug flag from session state
    debug_modifiers = st.session_state.get('debug_modifiers', False)
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
    team_name = row.get('team_name', '')

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

        st.sidebar.info(f"Using win-based calculation for {team_name}: wins={wins}, win%={winning_pct}, calculated points={points:.1f}")

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

    # Calculate hot/cold modifier based on overall win percentage only
    # Use the season win percentage for all teams for consistency
    
    # Only show debugging info in sidebar if debug is enabled
    if st.session_state.get('debug_modifiers', False):
        st.sidebar.info(f"Hot/Cold Calc for {team_name}: Using overall win%: {winning_pct:.3f}")
    
    # Use overall win percentage directly for the hot/cold modifier
    hot_cold_mod = calculate_hot_cold_modifier(winning_pct)

    # REMOVED: Strength of schedule calculation per user request
    # We'll set schedule_mod to 0 for debugging purposes but won't use it in calculation
    schedule_mod = 0.0
    schedule_factor = 1.0  # No impact

    # Calculate the raw power score without strength of schedule
    raw_power_score = weekly_avg * points_mod * hot_cold_mod  # Removed schedule_factor

    # Show detailed info for each team if enabled
    if debug_modifiers:
        st.sidebar.info(
            f"Team: {team_name}\n"
            f"Weekly Avg: {weekly_avg:.2f}\n"
            f"Points Mod: {points_mod:.2f}\n"
            f"Hot/Cold Mod: {hot_cold_mod:.2f}\n"
            f"SoS Mod: {schedule_mod:.2f} ({schedule_factor:.2f}×)\n"
            f"Raw Score: {raw_power_score:.2f}"
        )
    elif total_points == 0:
        # Only show basic debugging for teams with no points
        st.sidebar.info(f"Team: {team_name}, Weekly Avg: {weekly_avg:.2f}, Points Mod: {points_mod:.2f}, Hot/Cold: {hot_cold_mod:.2f}")

    return raw_power_score

def render(standings_data: pd.DataFrame, power_rankings_data: dict = None, weekly_results: list = None):
    """
    Render power rankings section

    Args:
        standings_data: DataFrame containing standings data
        power_rankings_data: Optional dict of custom power rankings data from user input
        weekly_results: Optional list of weekly results data from user input
    """
    st.header("⚾ Power Rankings")

    # Add explanation of the power score
    st.markdown("""
    Power Rankings combine weekly scoring average, points comparison against other teams, and overall win percentage.
    This is a measure of *current season performance only* and does not include historical data or playoff history.

    - **Power Score Scale**: 100 = League Average
    - **Above 100**: Team is performing better than league average
    - **Below 100**: Team is performing below league average
    - **Rank Movement**: ▲ (up), ▼ (down), – (unchanged) from April 14th

    Movement indicators show how teams have moved since the April 14th rankings snapshot, 
    providing a weekly comparison point for tracking performance trends.
    """)
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

    st.sidebar.success("⚡ Using live standings data from Fantrax API with manual data overrides")

    # Add version info
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Version Info")
    st.sidebar.info("Power Rankings v2.3.0\n- Linear modifier distribution\n- SoS modifier removed\n- Using overall win% for hot/cold\n- No playoff data included")

    # Add a debug option in sidebar to show detailed modifiers
    st.session_state.debug_modifiers = st.sidebar.checkbox("Show detailed modifier calculations", value=False)

    # Get custom data from parameters or session state
    if power_rankings_data:
        # Use the provided power rankings data
        custom_data = power_rankings_data
    elif 'power_rankings_data' in st.session_state and st.session_state.power_rankings_data:
        # Use data from session state
        custom_data = st.session_state.power_rankings_data
    else:
        # No custom data available
        custom_data = {}

    # Always apply manual data overrides if available
    has_manual_overrides = False
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
                    has_manual_overrides = True
                elif 'total_points' in team_data:
                    rankings_df.at[idx, 'total_points'] = team_data['total_points']
                    rankings_df.at[idx, 'fptsf'] = team_data['total_points']  # use both fields
                    has_manual_overrides = True

                if 'weeks_played' in team_data:
                    rankings_df.at[idx, 'weeks_played'] = team_data['weeks_played']
                    has_manual_overrides = True

    # Ensure we have these fields from either API or defaults
    if 'fptsf' not in rankings_df.columns or 'total_points' not in rankings_df.columns:
        # Calculate default values if needed
        rankings_df['fptsf'] = rankings_df['wins'] * 20  # 20 points per win as default
        rankings_df['total_points'] = rankings_df['fptsf']  # Keep both for compatibility

    if 'weeks_played' not in rankings_df.columns:
        rankings_df['weeks_played'] = rankings_df['wins'] + rankings_df['losses']

    # Display appropriate info message about data source
    if has_manual_overrides:
        st.info("Power rankings are calculated using a combination of Fantrax API data and your manual FPtsF entries from the sidebar. Power scores are normalized to 100 = league average.")
    else:
        st.info("Power rankings are calculated using live standings data from Fantrax API. Add manual FPtsF entries in the sidebar for more accurate power scores. Power scores are normalized to 100 = league average.")

    # Add an expander with detailed explanation of the new calculation method
    with st.expander("📊 How Power Scores Are Calculated"):
        st.markdown("""
        ### Power Score Calculation Details

        Power scores are calculated using three main components:

        1. **Weekly Average** - Average fantasy points per week
        2. **Points Modifier** - Based on total points compared to other teams (1.0× to 1.9×)
        3. **Hot/Cold Modifier** - Based on overall season win percentage (1.0× to 1.5×)

        #### Linear Distribution Method

        All modifiers use a straight line (linear) distribution rather than bucketed groups:

        - **Points Modifier**: Teams with the highest total points receive a 1.9× bonus, while teams with
          the lowest total points receive a 1.0× modifier. All other teams receive a proportional value
          between these extremes based on where their points total falls in the league range.

        - **Hot/Cold Modifier**: Teams with a 100% season win rate receive a 1.5× bonus, teams with a 0%
          win rate receive a 1.0× modifier. All teams receive a proportional value based on their exact
          overall win percentage for the season.

        This creates a more accurate and fair distribution of power scores that better reflects actual
        regular season performance differences between teams, without any consideration of playoff history.
        """)

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
        st.sidebar.success("Using provided weekly results parameter")
    elif 'weekly_results' in st.session_state and st.session_state.weekly_results:
        # Use data from session state
        weekly_data = st.session_state.weekly_results
        st.sidebar.success("Using weekly results from session state")
    else:
        # No weekly results available
        weekly_data = []
        st.sidebar.warning("No weekly results data available - using overall win/loss records")
        
    # Debug weekly data
    if weekly_data:
        st.sidebar.info(f"Weekly data available: {len(weekly_data)} entries")
        # Show the first entry as an example
        if len(weekly_data) > 0:
            st.sidebar.write("Example weekly result:", weekly_data[0])

    # Process recent wins/losses
    if weekly_data:
        # Process weekly results to get recent wins/losses for each team
        team_names = rankings_df['team_name'].unique()
        recent_weeks = 3  # How many weeks to consider for "recent" performance

        # Initialize recent wins/losses/draws columns
        rankings_df['recent_wins'] = 0
        rankings_df['recent_losses'] = 0
        rankings_df['recent_draws'] = 0

        for team_name in team_names:
            # Get this team's results
            team_results = [r for r in weekly_data if r['team'] == team_name]

            # Sort by week number and get the most recent X weeks
            team_results.sort(key=lambda x: x['week'], reverse=True)
            recent_results = team_results[:recent_weeks]

            # Sum weekly wins and losses across all matchups
            recent_weekly_wins = sum(r.get('weekly_wins', 0) for r in recent_results)
            recent_weekly_losses = sum(r.get('weekly_losses', 0) for r in recent_results)
            recent_weekly_draws = sum(r.get('weekly_draws', 0) for r in recent_results)

            # For backward compatibility, also calculate traditional wins/losses
            recent_wins = sum(1 for r in recent_results if r['result'] == 'Win')
            recent_losses = sum(1 for r in recent_results if r['result'] == 'Loss')

            # Update the dataframe
            if team_name in rankings_df['team_name'].values:
                idx = rankings_df[rankings_df['team_name'] == team_name].index[0]
                rankings_df.at[idx, 'recent_wins'] = recent_weekly_wins
                rankings_df.at[idx, 'recent_losses'] = recent_weekly_losses
                rankings_df.at[idx, 'recent_draws'] = recent_weekly_draws
                # Store traditional W-L too for backward compatibility
                rankings_df.at[idx, 'recent_match_wins'] = recent_wins
                rankings_df.at[idx, 'recent_match_losses'] = recent_losses
    else:
        # Don't use rolling mean as it creates fractional win/loss values
        # Instead, just use the overall win/loss record for each team
        st.sidebar.info("No weekly results data found - using overall win/loss record for hot/cold calculation")
        
        # Initialize columns with zeros
        rankings_df['recent_wins'] = 0
        rankings_df['recent_losses'] = 0 
        rankings_df['recent_draws'] = 0
        
        # We won't set these values since we'll use the winning_pct directly in the hot/cold calculation

    # Get previous rankings for movement indicators
    previous_rankings = get_previous_rankings()
    
    # Calculate raw power scores
    rankings_df['raw_power_score'] = rankings_df.apply(lambda x: calculate_power_score(x, rankings_df), axis=1)

    # Normalize power scores where 100 is the league average
    average_power = rankings_df['raw_power_score'].mean()
    rankings_df['power_score'] = (rankings_df['raw_power_score'] / average_power) * 100

    # Sort by normalized power score
    rankings_df = rankings_df.sort_values('power_score', ascending=False).reset_index(drop=True)
    rankings_df.index = rankings_df.index + 1  # Start ranking from 1
    
    # Add movement compared to previous rankings
    rankings_df['prev_rank'] = rankings_df['team_name'].map(lambda x: previous_rankings.get(x, 0))
    rankings_df['rank_change'] = rankings_df.apply(
        lambda x: 0 if x['prev_rank'] == 0 else int(x['prev_rank'] - x.name), axis=1
    )
    
    # Add movement indicators
    rankings_df['movement'] = rankings_df['rank_change'].apply(
        lambda x: "▲" if x > 0 else ("▼" if x < 0 else "–")
    )
    
    # Add style classes for color coding
    rankings_df['movement_class'] = rankings_df['rank_change'].apply(
        lambda x: "trending-up" if x > 0 else ("trending-down" if x < 0 else "")
    )

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
                        <div style="font-weight: 700; font-size: 1.5rem; margin-bottom: 0.5rem; color: white; display: flex; align-items: center; gap: 0.5rem;">
                            {row['team_name']}
                            <span class="{row['movement_class']}" style="font-size: 1.2rem; font-weight: bold; margin-left: 0.5rem;">
                                {row['movement']} {abs(row['rank_change']) if row['rank_change'] != 0 else ''}
                            </span>
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
                        <div style="font-weight: 600; color: white; display: flex; align-items: center;">
                            {row['team_name']}
                            <span class="{row['movement_class']}" style="font-size: 0.9rem; font-weight: bold; margin-left: 0.5rem;">
                                {row['movement']} {abs(row['rank_change']) if row['rank_change'] != 0 else ''}
                            </span>
                        </div>
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

    # Add a reference line for league average (100)
    fig.add_shape(
        type="line",
        x0=-0.5,
        x1=len(rankings_df) - 0.5,
        y0=100,
        y1=100,
        line=dict(
            color="red",
            width=2,
            dash="dash",
        )
    )

    # Add annotation for the reference line
    fig.add_annotation(
        x=len(rankings_df) - 0.5,
        y=100,
        text="League Average (100)",
        showarrow=False,
        font=dict(color="red"),
        xanchor="right",
        yanchor="bottom"
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