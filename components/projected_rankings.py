import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Dict, List

def calculate_hitter_points(row: pd.Series) -> float:
    """Calculate fantasy points for a hitter based on scoring settings"""
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

def calculate_pitcher_points(row: pd.Series) -> float:
    """Calculate fantasy points for a pitcher based on scoring settings"""
    points = 0
    
    points += row['IP'] * 2  # Innings Pitched
    points += row['SO'] * 1  # Strikeouts
    points += row['SV'] * 6  # Saves
    points += row['HLD'] * 3  # Holds
    points -= row['ER'] * 1  # Earned Runs
    points -= row['H'] * 0.5  # Hits Allowed
    points -= row['BB'] * 0.5  # Walks Allowed
    points -= row['HBP'] * 0.5  # Hit Batsmen
    
    # Calculate QA7 points
    if pd.notna(row['IP']):
        ip = row['IP']
        er = row['ER']
        if (ip >= 4 and ip <= 4.67 and er <= 1) or \
           (ip >= 5 and ip <= 6.67 and er <= 2) or \
           (ip >= 7 and er <= 3):
            points += 8  # QA7 points
    
    return points

def render(roster_data: pd.DataFrame):
    """Render projected rankings section"""
    st.header("📊 Projected Rankings")
    
    try:
        # Load projections data
        hitters_proj = pd.read_csv("attached_assets/oopsy-hitters.csv")
        pitchers_proj = pd.read_csv("attached_assets/oopsy-pitchers.csv")
        
        # Calculate points for each player
        hitters_proj['fantasy_points'] = hitters_proj.apply(calculate_hitter_points, axis=1)
        pitchers_proj['fantasy_points'] = pitchers_proj.apply(calculate_pitcher_points, axis=1)
        
        # Clean up team names and merge with roster data
        roster_hitters = roster_data[roster_data['position'].str.match(r'^(C|1B|2B|3B|SS|OF|DH|UTIL)$', na=False)]
        roster_pitchers = roster_data[roster_data['position'].str.match(r'^P', na=False)]
        
        # Merge rosters with projections
        team_hitter_points = []
        team_pitcher_points = []
        
        for team in roster_data['team'].unique():
            # Calculate hitter points
            team_hitters = roster_hitters[roster_hitters['team'] == team]
            hitter_points = 0
            for _, hitter in team_hitters.iterrows():
                player_proj = hitters_proj[hitters_proj['Name'] == hitter['player_name']]
                if not player_proj.empty:
                    hitter_points += player_proj.iloc[0]['fantasy_points']
            
            # Calculate pitcher points
            team_pitchers = roster_pitchers[roster_pitchers['team'] == team]
            pitcher_points = 0
            for _, pitcher in team_pitchers.iterrows():
                player_proj = pitchers_proj[pitchers_proj['Name'] == pitcher['player_name']]
                if not player_proj.empty:
                    pitcher_points += player_proj.iloc[0]['fantasy_points']
            
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
        st.error(f"An error occurred while calculating projected rankings. Please try refreshing.")
