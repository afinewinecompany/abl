import streamlit as st
import pandas as pd
import unicodedata
from typing import Dict
from components.rosters import (
    normalize_name, calculate_hitter_points, calculate_pitcher_points, 
    calculate_total_points, get_position_order, MLB_TEAM_COLORS, MLB_TEAM_IDS,
    get_player_headshot_html, render_player_card
)

def render(roster_data: pd.DataFrame):
    """Render team handbook showing complete rosters by team"""
    st.header("📚 Team Handbook")
    
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
            if pd.notna(row.get('Last')) and pd.notna(row.get('First')) and pd.notna(row.get('MLBAMID')):
                name = normalize_name(f"{row['First']} {row['Last']}")
                if name:
                    player_id_cache[name] = str(row['MLBAMID'])

        # Normalize names in projection data
        hitters_proj['Name'] = hitters_proj['Name'].fillna('').astype(str).apply(normalize_name)
        pitchers_proj['Name'] = pitchers_proj['Name'].fillna('').astype(str).apply(normalize_name)

        # Calculate fantasy points
        hitters_proj['fantasy_points'] = hitters_proj.apply(calculate_hitter_points, axis=1)
        pitchers_proj['fantasy_points'] = pitchers_proj.apply(calculate_pitcher_points, axis=1)

        # Create prospect score lookup dictionary
        prospect_scores = dict(zip(prospect_import['Name'], prospect_import['Score']))

        # Get all teams and sort them alphabetically
        teams = sorted(roster_data['team'].unique())
        
        st.markdown("""
        <style>
        .handbook-container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .team-section {
            margin-bottom: 3rem;
            background: rgba(26, 28, 35, 0.7);
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .team-title {
            font-size: 1.8rem;
            font-weight: 700;
            color: white;
            margin-bottom: 1rem;
            text-align: center;
            text-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
        }
        .roster-stats {
            display: flex;
            justify-content: space-around;
            margin-bottom: 1.5rem;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 8px;
            padding: 1rem;
        }
        .stat-item {
            text-align: center;
            color: white;
        }
        .stat-value {
            font-size: 1.5rem;
            font-weight: 700;
            color: #ff3030;
        }
        .stat-label {
            font-size: 0.9rem;
            opacity: 0.8;
        }
        .position-group {
            margin-bottom: 1.5rem;
        }
        .position-header {
            background: rgba(255, 48, 48, 0.1);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            font-weight: 600;
            margin-bottom: 0.5rem;
            border-left: 4px solid #ff3030;
        }
        .player-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 0.5rem;
        }
        </style>
        """, unsafe_allow_html=True)

        # Render each team
        st.markdown('<div class="handbook-container">', unsafe_allow_html=True)
        
        for team in teams:
            render_team_section(
                team, roster_data, hitters_proj, pitchers_proj, 
                prospect_scores, player_id_cache
            )
        
        st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error loading handbook data: {str(e)}")

def render_team_section(
    team: str,
    roster_data: pd.DataFrame,
    hitters_proj: pd.DataFrame,
    pitchers_proj: pd.DataFrame,
    prospect_scores: Dict,
    player_id_cache: Dict
):
    """Render a complete team section for the handbook"""
    
    # Get team colors
    team_colors = MLB_TEAM_COLORS.get(team, {'primary': '#1a1c23', 'secondary': '#2d2f36', 'accent': '#FFFFFF'})
    team_id = MLB_TEAM_IDS.get(team, '')
    
    # Filter data by team
    team_roster = roster_data[roster_data['team'] == team].copy()
    team_roster['clean_name'] = team_roster['player_name'].fillna('').astype(str).apply(normalize_name)

    # Calculate projected points for each player
    team_roster['projected_points'] = team_roster['player_name'].apply(
        lambda x: calculate_total_points(x, hitters_proj, pitchers_proj)
    )

    # Get team logo
    logo_html = f'<img src="https://www.mlbstatic.com/team-logos/{team_id}.svg" style="width: 50px; height: 50px; vertical-align: middle; margin-right: 1rem;">' if team_id else ""
    
    # Calculate team stats
    total_players = len(team_roster)
    active_players = len(team_roster[team_roster['status'].str.upper() == 'ACTIVE'])
    minor_players = len(team_roster[team_roster['status'].str.upper() == 'MINORS'])
    total_projected_points = team_roster['projected_points'].sum()

    # Start team section
    st.markdown(f"""
    <div class="team-section" style="border: 2px solid {team_colors['primary']};">
        <div class="team-title" style="color: {team_colors['primary']};">
            {logo_html}{team}
        </div>
        <div class="roster-stats">
            <div class="stat-item">
                <div class="stat-value">{total_players}</div>
                <div class="stat-label">Total Players</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{active_players}</div>
                <div class="stat-label">Active Roster</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{minor_players}</div>
                <div class="stat-label">Minor League</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{total_projected_points:.0f}</div>
                <div class="stat-label">Projected Points</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Split roster by status and sort by position
    active_roster = team_roster[team_roster['status'].str.upper() == 'ACTIVE'].copy()
    active_roster['position_order'] = active_roster['position'].apply(get_position_order)
    active_roster = active_roster.sort_values('position_order')

    minors_roster = team_roster[team_roster['status'].str.upper() == 'MINORS']
    reserve_roster = team_roster[~team_roster['status'].str.upper().isin(['ACTIVE', 'MINORS'])]

    # Render Active Roster
    if not active_roster.empty:
        st.markdown('<div class="position-group">', unsafe_allow_html=True)
        st.markdown('<div class="position-header">🏟️ Active Roster</div>', unsafe_allow_html=True)
        
        # Group by position
        position_groups = {
            'Catchers': active_roster[active_roster['position'] == 'C'],
            'Infielders': active_roster[active_roster['position'].isin(['1B', '2B', '3B', 'SS', 'UT'])],
            'Outfielders': active_roster[active_roster['position'].isin(['LF', 'CF', 'RF'])],
            'Pitchers': active_roster[active_roster['position'].isin(['SP', 'RP', 'P'])]
        }
        
        for pos_group_name, pos_players in position_groups.items():
            if not pos_players.empty:
                st.markdown(f'<div style="margin: 1rem 0; font-weight: 600; color: white;">{pos_group_name}</div>', unsafe_allow_html=True)
                st.markdown('<div class="player-grid">', unsafe_allow_html=True)
                
                for _, player in pos_players.iterrows():
                    headshot_html = get_player_headshot_html(player['player_name'], player_id_cache)
                    st.markdown(render_player_card(player, headshot_html, team_colors), unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    # Render Reserve Roster
    if not reserve_roster.empty:
        st.markdown('<div class="position-group">', unsafe_allow_html=True)
        st.markdown('<div class="position-header">🔄 Reserve Roster</div>', unsafe_allow_html=True)
        st.markdown('<div class="player-grid">', unsafe_allow_html=True)
        
        for _, player in reserve_roster.iterrows():
            headshot_html = get_player_headshot_html(player['player_name'], player_id_cache)
            st.markdown(render_player_card(player, headshot_html, team_colors), unsafe_allow_html=True)
        
        st.markdown('</div></div>', unsafe_allow_html=True)

    # Render Minor League Players
    if not minors_roster.empty:
        st.markdown('<div class="position-group">', unsafe_allow_html=True)
        st.markdown('<div class="position-header">⭐ Minor League Players</div>', unsafe_allow_html=True)
        st.markdown('<div class="player-grid">', unsafe_allow_html=True)
        
        for _, player in minors_roster.iterrows():
            headshot_html = get_player_headshot_html(player['player_name'], player_id_cache)
            prospect_score = prospect_scores.get(normalize_name(player['player_name']), None)
            st.markdown(render_player_card(player, headshot_html, team_colors, prospect_score), unsafe_allow_html=True)
        
        st.markdown('</div></div>', unsafe_allow_html=True)

    # Close team section
    st.markdown('</div>', unsafe_allow_html=True)