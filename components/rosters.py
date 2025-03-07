import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Dict
from components.projected_rankings import calculate_hitter_points, calculate_pitcher_points, normalize_name

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
                if 'P' in player['position'].upper():
                    proj = pitchers_proj[pitchers_proj['Name'] == player['clean_name']]
                else:
                    proj = hitters_proj[hitters_proj['Name'] == player['clean_name']]

                if not proj.empty:
                    points = proj.iloc[0]['fantasy_points']
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
            if 'P' in player['position'].upper():
                proj = pitchers_proj[pitchers_proj['Name'] == player['clean_name']]
            else:
                proj = hitters_proj[hitters_proj['Name'] == player['clean_name']]

            if not proj.empty:
                team_roster.at[idx, 'projected_points'] = proj.iloc[0]['fantasy_points']

        # Split roster by status
        active_roster = team_roster[team_roster['status'].str.upper() == 'ACTIVE']
        minors_roster = team_roster[team_roster['status'].str.upper() == 'MINORS']
        reserve_roster = team_roster[
            ~team_roster['status'].str.upper().isin(['ACTIVE', 'MINORS'])
        ]

        # Display roster statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Players", len(team_roster))
        with col2:
            st.metric("Active Players", len(active_roster))
        with col3:
            st.metric("Total Salary", f"${team_roster['salary'].sum():,.2f}")
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