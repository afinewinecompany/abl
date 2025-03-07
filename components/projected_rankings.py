import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Dict
import os
import unicodedata

def normalize_name(name: str) -> str:
    """Normalize player name from [last], [first] to [first] [last]"""
    try:
        # Convert to lowercase for case-insensitive comparison
        name = name.lower()
        # Remove diacritical marks
        name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII')
        if ',' in name:
            last, first = name.split(',', 1)
            name = f"{first.strip()} {last.strip()}"
        # Remove any parentheses and their contents
        name = name.split('(')[0].strip()
        # Remove any team designations after the name
        name = name.split(' - ')[0].strip()
        # Remove any periods and extra spaces
        name = name.replace('.', '').strip()
        name = ' '.join(name.split())
        return name
    except:
        return name.strip().lower()

def calculate_hitter_points(row: pd.Series) -> float:
    """Calculate fantasy points for a hitter based on scoring settings"""
    try:
        points = 0
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

def get_best_lineup_points(players_df: pd.DataFrame, position_limits: Dict[str, int]) -> tuple:
    """Calculate points for the best possible active lineup and return used players"""
    total_points = 0
    used_players = set()

    # Process each position in order of importance
    for pos, limit in position_limits.items():
        # Filter available players for this position
        eligible_players = players_df[
            (players_df['position'].str.contains(pos, case=False, na=False)) &
            (~players_df.index.isin(used_players))
        ].sort_values('projected_points', ascending=False)

        # Take the best N players for this position
        best_players = eligible_players.head(limit)
        total_points += best_players['projected_points'].sum()
        used_players.update(best_players.index)

    return total_points, used_players

def calculate_depth_score(players_df: pd.DataFrame, used_players: set) -> float:
    """Calculate a depth score for bench players with increased weight"""
    bench_players = players_df[~players_df.index.isin(used_players)]
    return bench_players['projected_points'].sum() * 0.75  # Weight bench players at 75%

def get_division_strength(team: str) -> float:
    """Calculate division strength adjustment"""
    division_mapping = {
        # AL West
        "Texas Rangers": "AL West",
        "Seattle Mariners": "AL West",
        "Houston Astros": "AL West",
        "Athletics": "AL West",
        "Los Angeles Angels": "AL West",
        # AL Central
        "Cleveland Guardians": "AL Central",
        "Detroit Tigers": "AL Central",
        "Minnesota Twins": "AL Central",
        "Chicago White Sox": "AL Central",
        "Kansas City Royals": "AL Central",
        # AL East
        "Toronto Blue Jays": "AL East",
        "New York Yankees": "AL East",
        "Tampa Bay Rays": "AL East",
        "Baltimore Orioles": "AL East",
        "Boston Red Sox": "AL East",
        # NL Central
        "Saint Louis Cardinals": "NL Central",
        "Pittsburgh Pirates": "NL Central",
        "Chicago Cubs": "NL Central",
        "Cincinnati Reds": "NL Central",
        "Milwaukee Brewers": "NL Central",
        # NL East
        "Atlanta Braves": "NL East",
        "Washington Nationals": "NL East",
        "Miami Marlins": "NL East",
        "New York Mets": "NL East",
        "Philadelphia Phillies": "NL East",
        # NL West
        "Los Angeles Dodgers": "NL West",
        "Colorado Rockies": "NL West",
        "Arizona Diamondbacks": "NL West",
        "San Diego Padres": "NL West",
        "San Francisco Giants": "NL West"
    }

    # Division strength ratings (higher means tougher division)
    division_strength = {
        "AL East": 1.1,    # Traditionally strong division
        "AL West": 1.05,   # Competitive division
        "NL East": 1.05,   # Competitive division
        "NL West": 1.0,    # Average division
        "AL Central": 0.95, # Historically weaker division
        "NL Central": 0.95  # Historically weaker division
    }

    division = division_mapping.get(team, "Unknown")
    return division_strength.get(division, 1.0)

def render(roster_data: pd.DataFrame):
    """Render projected rankings section"""
    try:
        st.header("📊 Projected Rankings")

        # Define active roster limits
        position_limits = {
            'C': 1,
            '1B': 1,
            '2B': 1,
            '3B': 1,
            'SS': 1,
            'LF': 1,
            'CF': 1,
            'RF': 1,
            'UT': 1,
            'SP': 3,
            'RP': 3,
            'P': 1
        }

        # Load projections
        hitters_file = "attached_assets/batx-hitters.csv"
        pitchers_file = "attached_assets/oopsy-pitchers-2.csv"

        if not os.path.exists(hitters_file) or not os.path.exists(pitchers_file):
            st.error("Projection files not found. Please check the file paths.")
            return

        hitters_proj = pd.read_csv(hitters_file)
        pitchers_proj = pd.read_csv(pitchers_file)

        # Normalize names and calculate fantasy points
        hitters_proj['Name'] = hitters_proj['Name'].apply(normalize_name)
        pitchers_proj['Name'] = pitchers_proj['Name'].apply(normalize_name)
        hitters_proj['fantasy_points'] = hitters_proj.apply(calculate_hitter_points, axis=1)
        pitchers_proj['fantasy_points'] = pitchers_proj.apply(calculate_pitcher_points, axis=1)

        # Calculate team rankings with active roster, depth, and division strength
        team_rankings_data = []
        for team in roster_data['team'].unique():
            team_roster = roster_data[roster_data['team'] == team].copy()
            team_roster['clean_name'] = team_roster['player_name'].apply(normalize_name)

            # Add projected points to each player
            team_roster['projected_points'] = 0.0
            for idx, player in team_roster.iterrows():
                # Check both hitter and pitcher projections for each player
                hitter_proj = hitters_proj[hitters_proj['Name'] == player['clean_name']]
                pitcher_proj = pitchers_proj[pitchers_proj['Name'] == player['clean_name']]

                points = 0
                if not hitter_proj.empty:
                    points += hitter_proj.iloc[0]['fantasy_points']
                if not pitcher_proj.empty:
                    points += pitcher_proj.iloc[0]['fantasy_points']

                team_roster.at[idx, 'projected_points'] = points

            # Calculate lineup and depth points
            active_points, used_players = get_best_lineup_points(team_roster, position_limits)
            depth_points = calculate_depth_score(team_roster, used_players)

            # Calculate division strength adjustment
            division_factor = get_division_strength(team)
            adjusted_total = (active_points + depth_points) * division_factor

            team_rankings_data.append({
                'team': team,
                'active_lineup_points': active_points,
                'depth_points': depth_points,
                'division_factor': division_factor,
                'adjusted_total': adjusted_total,
                'raw_total': active_points + depth_points
            })

        # Create rankings DataFrame
        team_rankings = pd.DataFrame(team_rankings_data)
        team_rankings = team_rankings.sort_values('adjusted_total', ascending=False)
        team_rankings = team_rankings.reset_index(drop=True)
        team_rankings.index = team_rankings.index + 1

        # Display rankings
        st.subheader("💫 Projected Team Rankings")
        st.dataframe(
            team_rankings,
            column_config={
                "team": "Team",
                "adjusted_total": st.column_config.NumberColumn(
                    "Adjusted Total Points",
                    format="%.1f",
                    help="Total points adjusted for division strength"
                ),
                "raw_total": st.column_config.NumberColumn(
                    "Raw Total Points",
                    format="%.1f",
                    help="Combined points before division adjustment"
                ),
                "active_lineup_points": st.column_config.NumberColumn(
                    "Active Lineup Points",
                    format="%.1f",
                    help="Points from best possible active lineup configuration"
                ),
                "depth_points": st.column_config.NumberColumn(
                    "Depth Value",
                    format="%.1f",
                    help="Additional value from bench players (weighted at 75%)"
                ),
                "division_factor": st.column_config.NumberColumn(
                    "Division Factor",
                    format="%.2f",
                    help="Strength of division adjustment (>1 means tougher division)"
                )
            },
            hide_index=False,
            column_order=[
                "team",
                "adjusted_total",
                "raw_total",
                "active_lineup_points",
                "depth_points",
                "division_factor"
            ]
        )

        # Visualization
        fig = px.bar(
            team_rankings,
            x='team',
            y=['active_lineup_points', 'depth_points'],
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

    except Exception as e:
        st.error(f"An error occurred while calculating projected rankings: {str(e)}")