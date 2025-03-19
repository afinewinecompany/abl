import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Dict
from components.projected_rankings import calculate_hitter_points, calculate_pitcher_points
import unicodedata
from components.prospects import normalize_name, MLB_TEAM_COLORS, MLB_TEAM_IDS, get_player_headshot_html

def get_salary_penalty(team: str) -> float:
    """Get salary cap penalty for a team"""
    penalties = {
        "Seattle Mariners": 24,
        "Colorado Rockies": 4,
        "Chicago Cubs": 12,
        "Los Angeles Angels": 11,
        "Philadelphia Phillies": 4,
        "Cleveland Guardians": 6,
        "Miami Marlins": 6,
        "Cincinnati Reds": 25,
        "Milwaukee Brewers": 34,
        "New York Yankees": 10,
        "Pittsburgh Pirates": 4
    }
    return penalties.get(team, 0)

def calculate_dynascore(power_rank: float, total_prospect_score: float) -> float:
    """Calculate Dynascore - combines power ranking and prospect strength"""
    # Normalize power rank (higher rank = lower number, so we invert it)
    normalized_power = (30 - power_rank) / 29  # Will be between 0 and 1

    # Normalize prospect score (assuming max possible is around 1000)
    normalized_prospects = min(total_prospect_score / 1000, 1)

    # Combine with weights (60% power rank, 40% prospects)
    dynascore = (normalized_power * 0.6 + normalized_prospects * 0.4) * 100

    return round(dynascore, 1)

def render_team_header(
    team: str,
    total_players: int,
    total_salary: float,
    salary_penalty: float,
    prospect_stats: Dict,
    power_rank: float,
    team_colors: Dict
):
    """Render the team dashboard header"""
    dynascore = calculate_dynascore(power_rank, prospect_stats.get('total_score', 0))

    st.markdown(f"""
        <style>
        .team-header {{
            background: linear-gradient(135deg, 
                {team_colors['primary']} 0%,
                {team_colors['secondary']} 60%,
                {team_colors['primary']} 100%);
            padding: 2rem;
            border-radius: 16px;
            margin-bottom: 2rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
        }}
        .team-name {{
            font-size: 2.5rem;
            font-weight: 800;
            color: white;
            margin-bottom: 1rem;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-top: 1.5rem;
        }}
        .stat-card {{
            background: rgba(255, 255, 255, 0.1);
            padding: 1rem;
            border-radius: 8px;
            backdrop-filter: blur(10px);
        }}
        .stat-label {{
            font-size: 0.9rem;
            color: rgba(255, 255, 255, 0.8);
        }}
        .stat-value {{
            font-size: 1.5rem;
            font-weight: 700;
            color: white;
            margin-top: 0.25rem;
        }}
        </style>

        <div class="team-header">
            <div class="team-name">{team}</div>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Dynascore™</div>
                    <div class="stat-value">{dynascore}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Power Rank</div>
                    <div class="stat-value">#{power_rank:.0f}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Total Players</div>
                    <div class="stat-value">{total_players}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Total Salary</div>
                    <div class="stat-value">${total_salary:,.2f}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Salary Penalty</div>
                    <div class="stat-value">${salary_penalty:,.2f}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Prospect Score</div>
                    <div class="stat-value">{prospect_stats.get('total_score', 0):.1f}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Avg Prospect Score</div>
                    <div class="stat-value">{prospect_stats.get('avg_score', 0):.1f}</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def get_position_order(position: str) -> int:
    """Get sorting order for positions"""
    position_order = {
        'C': 1,
        '1B': 2,
        '2B': 3,
        '3B': 4,
        'SS': 5,
        'LF': 6,
        'CF': 7,
        'RF': 8,
        'UT': 9,
        'SP': 10,
        'RP': 11,
        'P': 12
    }
    return position_order.get(position, 99)

def render_player_card(player: Dict, headshot_html: str, team_colors: Dict, prospect_score: float = None):
    """Render an individual player card"""
    projected_points = player.get('projected_points', 0)
    points_display = f"| {projected_points:.1f} pts" if projected_points > 0 else ""

    return f"""
        <div class="player-card" style="
            background: linear-gradient(135deg, 
                {team_colors['primary']} 0%,
                {team_colors['secondary']} 100%);
            border-radius: 10px;
            padding: 0.75rem;
            margin: 0.5rem 0;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            cursor: pointer;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);"
            onmouseover="this.style.transform='translateY(-3px)';this.style.boxShadow='0 4px 8px rgba(0,0,0,0.2)';"
            onmouseout="this.style.transform='translateY(0)';this.style.boxShadow='0 2px 4px rgba(0,0,0,0.1)';">
            {headshot_html}
            <div style="flex-grow: 1; color: white;">
                <div style="font-size: 1rem; font-weight: 600;">{player['player_name']}</div>
                <div style="font-size: 0.8rem; color: rgba(255,255,255,0.8); margin-top: 0.15rem;">
                    {player['position']} | {player['mlb_team']} | ${player['salary']:,.0f}{points_display}{f' | Score: {prospect_score:.1f}' if prospect_score is not None else ''}
                </div>
            </div>
            <span style="
                background: rgba(255,255,255,0.1);
                padding: 0.25rem 0.75rem;
                border-radius: 15px;
                font-weight: 600;
                font-size: 0.8rem;">
                {player['status'].upper()}
            </span>
        </div>
    """

def calculate_total_points(player_name: str, hitters_proj: pd.DataFrame, pitchers_proj: pd.DataFrame) -> float:
    """Calculate total fantasy points for a player"""
    total_points = 0
    player_name = normalize_name(player_name)

    # Handle special case for Luis Ortiz/Luis L. Ortiz
    if player_name.lower() == "luis ortiz":
        alternate_names = ["luis ortiz", "luis l ortiz", "luis l. ortiz"]
        # Check for hitter projections with any name variant
        hitter_proj = hitters_proj[hitters_proj['Name'].apply(lambda x: normalize_name(str(x)).lower() in alternate_names)]
        if not hitter_proj.empty:
            total_points += hitter_proj.iloc[0]['fantasy_points']

        # Check for pitcher projections with any name variant
        pitcher_proj = pitchers_proj[pitchers_proj['Name'].apply(lambda x: normalize_name(str(x)).lower() in alternate_names)]
        if not pitcher_proj.empty:
            total_points += pitcher_proj.iloc[0]['fantasy_points']
    else:
        # Regular name matching for other players
        hitter_proj = hitters_proj[hitters_proj['Name'].apply(normalize_name) == player_name]
        if not hitter_proj.empty:
            total_points += hitter_proj.iloc[0]['fantasy_points']

        pitcher_proj = pitchers_proj[pitchers_proj['Name'].apply(normalize_name) == player_name]
        if not pitcher_proj.empty:
            total_points += pitcher_proj.iloc[0]['fantasy_points']

    return total_points

def render(roster_data: pd.DataFrame):
    """Render roster information section"""
    st.header("Team Rosters")

    try:
        # Load projections data with proper NA handling
        hitters_proj = pd.read_csv("attached_assets/batx-hitters.csv", na_values=['NA', ''], keep_default_na=True)
        pitchers_proj = pd.read_csv("attached_assets/oopsy-pitchers-2.csv", na_values=['NA', ''], keep_default_na=True)

        # Load prospect scores
        prospect_import = pd.read_csv("attached_assets/ABL-Import.csv", na_values=['NA', ''], keep_default_na=True)
        prospect_import['Name'] = prospect_import['Name'].fillna('').astype(str).apply(normalize_name)

        # Load MLB player IDs for headshots
        mlb_ids_df = pd.read_csv("attached_assets/mlb_player_ids-2.csv")
        player_id_cache = {}
        for _, row in mlb_ids_df.iterrows():
            if pd.notna(row['Last']) and pd.notna(row['First']) and pd.notna(row['MLBAMID']):
                name = normalize_name(f"{row['First']} {row['Last']}")
                if name:
                    player_id_cache[name] = str(row['MLBAMID'])

        # Normalize names in projection data
        hitters_proj['Name'] = hitters_proj['Name'].fillna('').astype(str).apply(normalize_name)
        pitchers_proj['Name'] = pitchers_proj['Name'].fillna('').astype(str).apply(normalize_name)

        # Calculate fantasy points
        hitters_proj['fantasy_points'] = hitters_proj.apply(calculate_hitter_points, axis=1)
        pitchers_proj['fantasy_points'] = pitchers_proj.apply(calculate_pitcher_points, axis=1)

        # Add team filter
        teams = roster_data['team'].unique()
        selected_team = st.selectbox("Select Team", teams)

        # Get team colors
        team_colors = MLB_TEAM_COLORS.get(selected_team, {'primary': '#1a1c23', 'secondary': '#2d2f36', 'accent': '#FFFFFF'})

        # Filter data by selected team and create a copy
        team_roster = roster_data[roster_data['team'] == selected_team].copy()
        team_roster['clean_name'] = team_roster['player_name'].fillna('').astype(str).apply(normalize_name)

        # Calculate projected points for each player
        team_roster['projected_points'] = team_roster['player_name'].apply(
            lambda x: calculate_total_points(x, hitters_proj, pitchers_proj)
        )


        # Calculate prospect stats
        minors_players = team_roster[team_roster['status'].str.upper() == 'MINORS'].copy()
        minors_players = pd.merge(
            minors_players,
            prospect_import[['Name', 'Score']],  # Changed from 'Unique score' to 'Score'
            left_on='clean_name',
            right_on='Name',
            how='left'
        )

        # Create prospect score lookup dictionary
        prospect_scores = dict(zip(minors_players['clean_name'], minors_players['Score']))  # Changed from 'Unique score' to 'Score'

        prospect_stats = {
            'total_score': minors_players['Score'].fillna(0).sum(),  # Changed from 'Unique score' to 'Score'
            'avg_score': minors_players['Score'].fillna(0).mean(),   # Changed from 'Unique score' to 'Score'
            'count': len(minors_players)
        }

        # Calculate salary info
        salary_penalty = get_salary_penalty(selected_team)
        non_minors_roster = team_roster[team_roster['status'].str.upper() != 'MINORS']
        total_salary = non_minors_roster['salary'].sum() + salary_penalty

        # Get power rank (assuming 15 is middle if not found)
        power_rank = 15.0  # Default value
        # You would normally get this from your power rankings calculation

        # Render team header
        render_team_header(
            selected_team,
            len(team_roster),
            total_salary,
            salary_penalty,
            prospect_stats,
            power_rank,
            team_colors
        )

        # Split roster by status and sort by position
        active_roster = team_roster[team_roster['status'].str.upper() == 'ACTIVE'].copy()
        active_roster['position_order'] = active_roster['position'].apply(get_position_order)
        active_roster = active_roster.sort_values('position_order')

        minors_roster = team_roster[team_roster['status'].str.upper() == 'MINORS']
        reserve_roster = team_roster[
            ~team_roster['status'].str.upper().isin(['ACTIVE', 'MINORS'])
        ]

        # Active Roster Section with position-based layout
        st.subheader("📋 Active Roster")

        # Group active roster by position
        for pos in ['C', '1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF', 'UT']:
            pos_players = active_roster[active_roster['position'] == pos]
            if not pos_players.empty:
                st.markdown(f"**{pos}**")
                for _, player in pos_players.iterrows():
                    headshot_html = get_player_headshot_html(player['player_name'], player_id_cache)
                    st.markdown(render_player_card(player, headshot_html, team_colors), unsafe_allow_html=True)

        # Display pitchers after position players
        pitchers = active_roster[active_roster['position'].isin(['SP', 'RP', 'P'])]
        if not pitchers.empty:
            st.markdown("**Pitchers**")
            for _, player in pitchers.iterrows():
                headshot_html = get_player_headshot_html(player['player_name'], player_id_cache)
                st.markdown(render_player_card(player, headshot_html, team_colors), unsafe_allow_html=True)

        # Reserve Roster Section
        if not reserve_roster.empty:
            st.subheader("🔄 Reserve Roster")
            for _, player in reserve_roster.iterrows():
                headshot_html = get_player_headshot_html(player['player_name'], player_id_cache)
                st.markdown(render_player_card(player, headshot_html, team_colors), unsafe_allow_html=True)

        # Minors/Prospects Section
        if not minors_roster.empty:
            st.subheader("⭐ Minor League Players")
            for _, player in minors_roster.iterrows():
                headshot_html = get_player_headshot_html(player['player_name'], player_id_cache)
                prospect_score = prospect_scores.get(normalize_name(player['player_name']), None)
                st.markdown(render_player_card(player, headshot_html, team_colors, prospect_score), unsafe_allow_html=True)

        # Position breakdown
        st.subheader("Position Distribution")
        position_counts = team_roster['position'].value_counts()
        st.bar_chart(position_counts)

    except Exception as e:
        st.error(f"An error occurred while displaying roster data: {str(e)}")