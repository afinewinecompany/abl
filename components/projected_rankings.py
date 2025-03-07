import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Dict
import os

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

def calculate_hitter_points(row: pd.Series) -> float:
    """Calculate fantasy points for a hitter based on scoring settings"""
    try:
        points = 0
        # Singles = H - (2B + 3B + HR)
        singles = row['H'] - (row['2B'] + row['3B'] + row['HR'])

        points += singles * 1  # Singles
        points += row['2B'] * 2  # Doubles
        points += row['3B'] * 3  # Triples
        points += row['HR'] * 4  # Home Runs
        points += row['RBI'] * 1  # RBI
        points += row['R'] * 1  # Runs
        points += row['BB'] * 1  # Walks
        points += row['HBP'] * 1  # Hit By Pitch
        points += row['SB'] * 2  # Stolen Bases

        return points
    except Exception as e:
        st.error(f"Error calculating hitter points: {str(e)}")
        return 0

def calculate_pitcher_points(row: pd.Series) -> float:
    """Calculate fantasy points for a pitcher based on scoring settings"""
    try:
        points = 0

        points += row['IP'] * 2  # Innings Pitched
        points += row['SO'] * 1  # Strikeouts
        points += row['SV'] * 6  # Saves
        points += row['HLD'] * 3  # Holds
        points -= row['ER'] * 1  # Earned Runs
        points -= row['H'] * 0.5  # Hits Allowed
        points -= row['BB'] * 0.5  # Walks Allowed
        # HBP is not included in projections, so we skip it

        # Calculate QA7 points
        if pd.notna(row['IP']) and pd.notna(row['ER']):
            ip = row['IP']
            er = row['ER']
            if (ip >= 4 and ip <= 4.67 and er <= 1) or \
               (ip >= 5 and ip <= 6.67 and er <= 2) or \
               (ip >= 7 and er <= 3):
                points += 8  # QA7 points

        return points
    except Exception as e:
        st.error(f"Error calculating pitcher points: {str(e)}")
        return 0

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

def render(roster_data: pd.DataFrame):
    """Render projected rankings section"""
    try:
        st.header("📊 Projected Rankings")

        # Debug information
        st.sidebar.markdown("### Debug Information")
        show_debug = st.sidebar.checkbox("Show Debug Info")

        if show_debug:
            st.sidebar.markdown("### Initial Roster Data")
            st.sidebar.write(f"Total players in roster: {len(roster_data)}")
            st.sidebar.write("\nUnique positions in roster:")
            st.sidebar.write(roster_data['position'].unique().tolist())

        # Check if projection files exist
        hitters_file = "attached_assets/batx-hitters.csv"
        pitchers_file = "attached_assets/oopsy-pitchers-2.csv"

        if not os.path.exists(hitters_file) or not os.path.exists(pitchers_file):
            st.error("Projection files not found. Please check the file paths.")
            return

        # Load projections data
        hitters_proj = pd.read_csv(hitters_file)
        pitchers_proj = pd.read_csv(pitchers_file)

        if show_debug:
            st.sidebar.markdown("### Data Loading Info")
            st.sidebar.write(f"Total pitchers in projections: {len(pitchers_proj)}")
            st.sidebar.write(f"Total hitters in projections: {len(hitters_proj)}")
            st.sidebar.write("\nRaw CSV rows for each file:")
            st.sidebar.write(f"Hitters CSV total rows: {sum(1 for line in open(hitters_file))}")
            st.sidebar.write(f"Pitchers CSV total rows: {sum(1 for line in open(pitchers_file))}")

        # Normalize names in projection data
        hitters_proj['Name'] = hitters_proj['Name'].apply(normalize_name)
        pitchers_proj['Name'] = pitchers_proj['Name'].apply(normalize_name)

        # Calculate points for each player
        hitters_proj['fantasy_points'] = hitters_proj.apply(calculate_hitter_points, axis=1)
        pitchers_proj['fantasy_points'] = pitchers_proj.apply(calculate_pitcher_points, axis=1)

        # Split roster by position type
        pitcher_positions = ['SP', 'RP', 'P']  # List of pitcher positions
        roster_pitchers = roster_data[
            roster_data['position'].str.upper().str.contains('SP|RP|P', na=False)
        ]
        roster_hitters = roster_data[
            ~roster_data['position'].str.upper().str.contains('SP|RP|P', na=False)
        ]

        if show_debug:
            st.sidebar.markdown("### Position Filtering Results")
            st.sidebar.write(f"Total hitters after position filter: {len(roster_hitters)}")
            st.sidebar.write(f"Total pitchers after position filter: {len(roster_pitchers)}")
            st.sidebar.write("\nPitcher positions found:")
            st.sidebar.write(roster_pitchers['position'].unique().tolist())

        # Normalize names in roster data
        roster_hitters['clean_name'] = roster_hitters['player_name'].apply(normalize_name)
        roster_pitchers['clean_name'] = roster_pitchers['player_name'].apply(normalize_name)

        # Initialize lists to store team scores
        team_hitter_points = []
        team_pitcher_points = []

        for team in roster_data['team'].unique():
            # Calculate hitter points
            team_hitters = roster_hitters[roster_hitters['team'] == team]
            hitter_points = 0
            matched_hitters = 0
            total_hitters = len(team_hitters)

            if show_debug:
                st.sidebar.markdown(f"\n### {team} Roster Analysis")

            for _, hitter in team_hitters.iterrows():
                points = calculate_total_points(hitter['clean_name'], hitters_proj, pitchers_proj)
                if points > 0:
                    hitter_points += points
                    matched_hitters += 1
                    if show_debug:
                        st.sidebar.write(f"✅ Matched hitter: {hitter['clean_name']} ({points:.1f} pts)")
                elif show_debug:
                    st.sidebar.write(f"❌ No match: {hitter['clean_name']}")

            # Calculate pitcher points
            team_pitchers = roster_pitchers[roster_pitchers['team'] == team]
            pitcher_points = 0
            matched_pitchers = 0
            total_pitchers = len(team_pitchers)

            for _, pitcher in team_pitchers.iterrows():
                points = calculate_total_points(pitcher['clean_name'], hitters_proj, pitchers_proj)
                if points > 0:
                    pitcher_points += points
                    matched_pitchers += 1
                    if show_debug:
                        st.sidebar.write(f"✅ Matched pitcher: {pitcher['clean_name']} ({points:.1f} pts)")
                elif show_debug:
                    st.sidebar.write(f"❌ No match: {pitcher['clean_name']}")

            if show_debug:
                st.sidebar.markdown(f"### {team} Stats")
                st.sidebar.write(f"Hitters matched: {matched_hitters}/{total_hitters}")
                st.sidebar.write(f"Pitchers matched: {matched_pitchers}/{total_pitchers}")

            team_hitter_points.append({
                'team': team,
                'hitter_points': hitter_points
            })

            team_pitcher_points.append({
                'team': team,
                'pitcher_points': pitcher_points
            })

        # Create team rankings dataframe
        hitter_df = pd.DataFrame(team_hitter_points)
        pitcher_df = pd.DataFrame(team_pitcher_points)

        team_rankings = pd.merge(hitter_df, pitcher_df, on='team')
        team_rankings['total_points'] = team_rankings['hitter_points'] + team_rankings['pitcher_points']
        team_rankings = team_rankings.sort_values('total_points', ascending=False)
        team_rankings = team_rankings.reset_index(drop=True)
        team_rankings.index = team_rankings.index + 1

        # Display rankings
        st.subheader("💫 Projected Team Rankings")
        st.dataframe(
            team_rankings,
            column_config={
                "team": "Team",
                "hitter_points": st.column_config.NumberColumn(
                    "Projected Hitter Points",
                    format="%.1f"
                ),
                "pitcher_points": st.column_config.NumberColumn(
                    "Projected Pitcher Points",
                    format="%.1f"
                ),
                "total_points": st.column_config.NumberColumn(
                    "Total Projected Points",
                    format="%.1f"
                )
            },
            hide_index=False
        )

        # Visualization
        fig = px.bar(
            team_rankings,
            x='team',
            y=['hitter_points', 'pitcher_points'],
            title='Projected Team Points Distribution',
            labels={
                'team': 'Team',
                'value': 'Projected Points',
                'variable': 'Category'
            },
            barmode='stack'
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

        # Display top projected players
        st.subheader("🌟 Top Projected Players")

        col1, col2 = st.columns(2)

        with col1:
            st.write("Top 10 Hitters")
            top_hitters = hitters_proj.nlargest(10, 'fantasy_points')[['Name', 'Team', 'fantasy_points']]
            st.dataframe(
                top_hitters,
                column_config={
                    "Name": "Player",
                    "Team": "MLB Team",
                    "fantasy_points": st.column_config.NumberColumn(
                        "Projected Points",
                        format="%.1f"
                    )
                },
                hide_index=True
            )

        with col2:
            st.write("Top 10 Pitchers")
            top_pitchers = pitchers_proj.nlargest(10, 'fantasy_points')[['Name', 'Team', 'fantasy_points']]
            st.dataframe(
                top_pitchers,
                column_config={
                    "Name": "Player",
                    "Team": "MLB Team",
                    "fantasy_points": st.column_config.NumberColumn(
                        "Projected Points",
                        format="%.1f"
                    )
                },
                hide_index=True
            )

    except Exception as e:
        st.error(f"An error occurred while calculating projected rankings: {str(e)}")