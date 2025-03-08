from components.prospects import calculate_prospect_score
import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Dict
from components.projected_rankings import calculate_hitter_points, calculate_pitcher_points, normalize_name

def calculate_total_points(player_name: str, hitters_proj: pd.DataFrame, pitchers_proj: pd.DataFrame) -> float:
    """Calculate total fantasy points for a player, handling special case for Ohtani"""
    total_points = 0

    # Normalize the player name for comparison
    player_name = normalize_name(player_name)

    # Check for hitter projections (using normalized names for comparison)
    hitter_proj = hitters_proj[hitters_proj['Name'].apply(normalize_name) == player_name]
    if not hitter_proj.empty:
        total_points += hitter_proj.iloc[0]['fantasy_points']

    # Check for pitcher projections (using normalized names for comparison)
    pitcher_proj = pitchers_proj[pitchers_proj['Name'].apply(normalize_name) == player_name]
    if not pitcher_proj.empty:
        total_points += pitcher_proj.iloc[0]['fantasy_points']

    return total_points

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

def render(roster_data: pd.DataFrame):
    """Render roster information section"""
    st.header("Team Rosters")

    try:
        # Load projections data
        hitters_proj = pd.read_csv("attached_assets/batx-hitters.csv")
        pitchers_proj = pd.read_csv("attached_assets/oopsy-pitchers-2.csv")

        # Load prospect rankings for minors
        prospect_rankings = pd.read_csv("attached_assets/2025 Dynasty Dugout Offseason Rankings - Jan 25 Prospects.csv")
        prospect_rankings['Player'] = prospect_rankings['Player'].apply(normalize_name)
        prospect_rankings['prospect_score'] = prospect_rankings['Ranking'].apply(calculate_prospect_score)

        # Normalize names in projection data
        hitters_proj['Name'] = hitters_proj['Name'].apply(normalize_name)
        pitchers_proj['Name'] = pitchers_proj['Name'].apply(normalize_name)

        # Calculate fantasy points for projections
        hitters_proj['fantasy_points'] = hitters_proj.apply(calculate_hitter_points, axis=1)
        pitchers_proj['fantasy_points'] = pitchers_proj.apply(calculate_pitcher_points, axis=1)

        # Calculate team projected rankings
        all_teams_points = {}
        for team in roster_data['team'].unique():
            team_roster = roster_data[roster_data['team'] == team].copy()
            team_roster['clean_name'] = team_roster['player_name'].apply(normalize_name)

            total_points = 0
            for idx, player in team_roster.iterrows():
                points = calculate_total_points(player['clean_name'], hitters_proj, pitchers_proj)
                total_points += points

            all_teams_points[team] = total_points

        # Sort teams by projected points to get rankings
        rankings = pd.Series(all_teams_points).sort_values(ascending=False)
        team_rankings = {team: rank + 1 for rank, team in enumerate(rankings.index)}

        # Add team filter
        teams = roster_data['team'].unique()
        selected_team = st.selectbox("Select Team", teams)

        # Show team rank and projected points in header
        rank = team_rankings[selected_team]
        total_points = all_teams_points[selected_team]
        st.subheader(f"{selected_team} (Rank: #{rank} - Projected Points: {total_points:,.1f})")

        # Filter data by selected team and create a copy
        team_roster = roster_data[roster_data['team'] == selected_team].copy()
        team_roster['clean_name'] = team_roster['player_name'].apply(normalize_name)

        # Add projected points to team roster
        team_roster['projected_points'] = 0.0  # Initialize with zeros
        for idx, player in team_roster.iterrows():
            points = calculate_total_points(player['clean_name'], hitters_proj, pitchers_proj)
            team_roster.at[idx, 'projected_points'] = points

        # Split roster by status
        active_roster = team_roster[team_roster['status'].str.upper() == 'ACTIVE']
        minors_roster = team_roster[team_roster['status'].str.upper() == 'MINORS']
        reserve_roster = team_roster[
            ~team_roster['status'].str.upper().isin(['ACTIVE', 'MINORS'])
        ]

        # Calculate total salary excluding MINORS players
        non_minors_roster = team_roster[team_roster['status'].str.upper() != 'MINORS']
        salary_penalty = get_salary_penalty(selected_team)
        total_salary = non_minors_roster['salary'].sum() + salary_penalty

        # Display roster statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Players", len(team_roster))
        with col2:
            st.metric("Active Players", len(active_roster))
        with col3:
            st.metric(
                "Total Salary",
                f"${total_salary:,.2f}",
                help=f"Includes ${salary_penalty:.2f} cap penalty" if salary_penalty > 0 else None
            )
        with col4:
            st.metric("Positions", len(team_roster['position'].unique()))

        # Add prospect scores to minors players
        minors_roster['prospect_score'] = 0.0  # Initialize with zeros
        for idx, player in minors_roster.iterrows():
            prospect_match = prospect_rankings[prospect_rankings['Player'] == player['clean_name']]
            if not prospect_match.empty:
                minors_roster.at[idx, 'prospect_score'] = prospect_match.iloc[0]['prospect_score']
            else:
                minors_roster.at[idx, 'prospect_score'] = 2.0  # Baseline score for unranked prospects

        # Display columns for different roster sections
        active_display_columns = ['player_name', 'position', 'salary', 'projected_points', 'mlb_team']
        minors_display_columns = ['player_name', 'position', 'salary', 'prospect_score', 'projected_points', 'mlb_team']

        # Active Roster Section
        st.subheader("📋 Active Roster")
        st.dataframe(
            active_roster[active_display_columns],
            column_config={
                "player_name": "Player",
                "position": "Position",
                "salary": st.column_config.NumberColumn(
                    "Salary",
                    format="$%.2f"
                ),
                "projected_points": st.column_config.NumberColumn(
                    "Projected Points",
                    format="%.1f",
                    help="Projected fantasy points for the season"
                ),
                "mlb_team": "MLB Team"
            },
            hide_index=True
        )

        # Reserve Roster Section
        if not reserve_roster.empty:
            st.subheader("🔄 Reserve Roster")
            st.dataframe(
                reserve_roster[active_display_columns],
                column_config={
                    "player_name": "Player",
                    "position": "Position",
                    "salary": st.column_config.NumberColumn(
                        "Salary",
                        format="$%.2f"
                    ),
                    "projected_points": st.column_config.NumberColumn(
                        "Projected Points",
                        format="%.1f",
                        help="Projected fantasy points for the season"
                    ),
                    "mlb_team": "MLB Team"
                },
                hide_index=True
            )

        # Minors/Prospects Section
        if not minors_roster.empty:
            st.subheader("⭐ Minor League Players")
            st.dataframe(
                minors_roster[minors_display_columns],
                column_config={
                    "player_name": "Player",
                    "position": "Position",
                    "salary": st.column_config.NumberColumn(
                        "Salary",
                        format="$%.2f"
                    ),
                    "prospect_score": st.column_config.NumberColumn(
                        "Prospect Score",
                        format="%.1f",
                        help="Prospect ranking score (100 = #1 prospect)"
                    ),
                    "projected_points": st.column_config.NumberColumn(
                        "Projected Points",
                        format="%.1f",
                        help="Projected fantasy points for the season"
                    ),
                    "mlb_team": "MLB Team"
                },
                hide_index=True
            )

        # Position breakdown
        st.subheader("Position Distribution")
        position_counts = team_roster['position'].value_counts()
        st.bar_chart(position_counts)

    except Exception as e:
        st.error(f"An error occurred while displaying roster data: {str(e)}")