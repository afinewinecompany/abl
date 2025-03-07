import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Dict
from components.projected_rankings import calculate_hitter_points, calculate_pitcher_points, normalize_name

def calculate_total_points(player_name: str, hitters_proj: pd.DataFrame, pitchers_proj: pd.DataFrame) -> float:
    """Calculate total fantasy points for a player, handling special case for Ohtani"""
    total_points = 0

    # Check for hitter projections
    hitter_proj = hitters_proj[hitters_proj['Name'] == player_name]
    if not hitter_proj.empty:
        total_points += hitter_proj.iloc[0]['fantasy_points']

    # Check for pitcher projections
    pitcher_proj = pitchers_proj[pitchers_proj['Name'] == player_name]
    if not pitcher_proj.empty:
        total_points += pitcher_proj.iloc[0]['fantasy_points']

    return total_points

def get_salary_penalty(team: str) -> float:
    """Get salary cap penalty for a team"""
    penalties = {
        "Mariners": 16,
        "Rockies": 4,
        "Cubs": 12,
        "Angels": 11,
        "Phillies": 4,
        "Guardians": 6,
        "Marlins": 6,
        "Reds": 25,
        "Brewers": 34,
        "Yankees": 10,
        "Pirates": 4
    }
    return penalties.get(team, 0)

def render(roster_data: pd.DataFrame):
    """Render roster information section"""
    st.header("Team Rosters")

    try:
        # Load projections data
        hitters_proj = pd.read_csv("attached_assets/batx-hitters.csv")
        pitchers_proj = pd.read_csv("attached_assets/oopsy-pitchers-2.csv")

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

        # Add projected points to display columns
        display_columns = ['player_name', 'position', 'mlb_team', 'status', 'salary', 'projected_points']

        # Active Roster Section
        st.subheader("📋 Active Roster")
        st.dataframe(
            active_roster[display_columns],
            column_config={
                "player_name": "Player",
                "position": "Position",
                "mlb_team": "MLB Team",
                "status": "Status",
                "salary": st.column_config.NumberColumn(
                    "Salary",
                    format="$%.2f"
                ),
                "projected_points": st.column_config.NumberColumn(
                    "Projected Points",
                    format="%.1f",
                    help="Projected fantasy points for the season"
                )
            },
            hide_index=True
        )

        # Reserve Roster Section
        if not reserve_roster.empty:
            st.subheader("🔄 Reserve Roster")
            st.dataframe(
                reserve_roster[display_columns],
                column_config={
                    "player_name": "Player",
                    "position": "Position",
                    "mlb_team": "MLB Team",
                    "status": "Status",
                    "salary": st.column_config.NumberColumn(
                        "Salary",
                        format="$%.2f"
                    ),
                    "projected_points": st.column_config.NumberColumn(
                        "Projected Points",
                        format="%.1f",
                        help="Projected fantasy points for the season"
                    )
                },
                hide_index=True
            )

        # Minors/Prospects Section
        if not minors_roster.empty:
            st.subheader("⭐ Minor League Players")
            st.dataframe(
                minors_roster[display_columns],
                column_config={
                    "player_name": "Player",
                    "position": "Position",
                    "mlb_team": "MLB Team",
                    "status": "Status",
                    "salary": st.column_config.NumberColumn(
                        "Salary",
                        format="$%.2f"
                    ),
                    "projected_points": st.column_config.NumberColumn(
                        "Projected Points",
                        format="%.1f",
                        help="Projected fantasy points for the season"
                    )
                },
                hide_index=True
            )

        # Position breakdown
        st.subheader("Position Distribution")
        position_counts = team_roster['position'].value_counts()
        st.bar_chart(position_counts)

    except Exception as e:
        st.error(f"An error occurred while displaying roster data: {str(e)}")

def normalize_name(name: str) -> str:
    """Normalize player name from [last], [first] to [first] [last]"""
    try:
        if ',' in name:
            last, first = name.split(',', 1)
            return f"{first.strip()} {last.strip()}"
        # Remove any parentheses and their contents
        name = name.split('(')[0].strip()
        # Remove any team designations after the name
        name = name.split(' - ')[0].strip()
        return name.strip()
    except:
        return name.strip()