import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Dict
import os
import unicodedata

def normalize_name(name: str) -> str:
    """Normalize player name for comparison"""
    try:
        name = name.lower()
        name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII')
        if ',' in name:
            last, first = name.split(',', 1)
            name = f"{first.strip()} {last.strip()}"
        name = name.split('(')[0].strip()
        name = name.split(' - ')[0].strip()
        name = name.replace('.', '').strip()
        name = ' '.join(name.split())
        return name
    except:
        return name.strip().lower()

def calculate_hitter_points(row: pd.Series) -> float:
    """Calculate fantasy points for a hitter"""
    try:
        points = 0
        singles = row['H'] - (row['2B'] + row['3B'] + row['HR'])
        points += singles * 1
        points += row['2B'] * 2
        points += row['3B'] * 3
        points += row['HR'] * 4
        points += row['RBI'] * 1
        points += row['R'] * 1
        points += row['BB'] * 1
        points += row['HBP'] * 1
        points += row['SB'] * 2
        return points
    except Exception as e:
        st.error(f"Error calculating hitter points: {str(e)}")
        return 0

def calculate_pitcher_points(row: pd.Series) -> float:
    """Calculate fantasy points for a pitcher"""
    try:
        points = 0
        points += row['IP'] * 2
        points += row['SO'] * 1
        points += row['SV'] * 6
        points += row['HLD'] * 3
        points -= row['ER'] * 1
        points -= row['H'] * 0.5
        points -= row['BB'] * 0.5

        if pd.notna(row['IP']) and pd.notna(row['ER']):
            ip = row['IP']
            er = row['ER']
            if (ip >= 4 and ip <= 4.67 and er <= 1) or \
               (ip >= 5 and ip <= 6.67 and er <= 2) or \
               (ip >= 7 and er <= 3):
                points += 8
        return points
    except Exception as e:
        st.error(f"Error calculating pitcher points: {str(e)}")
        return 0

def get_best_lineup_points(players_df: pd.DataFrame, position_limits: Dict[str, int]) -> tuple:
    """Calculate points for the best possible active lineup"""
    total_points = 0
    used_players = set()

    for pos, limit in position_limits.items():
        eligible_players = players_df[
            (players_df['position'].str.contains(pos, case=False, na=False)) &
            (~players_df.index.isin(used_players))
        ].sort_values('projected_points', ascending=False)

        best_players = eligible_players.head(limit)
        total_points += best_players['projected_points'].sum()
        used_players.update(best_players.index)

    return total_points, used_players

def calculate_depth_score(players_df: pd.DataFrame, used_players: set) -> float:
    """Calculate depth score for bench players"""
    bench_players = players_df[~players_df.index.isin(used_players)]
    return bench_players['projected_points'].sum() * 0.85  # Weight bench players at 85%

def calculate_abl_score(active_points: float, depth_points: float, division_factor: float) -> float:
    """Calculate overall ABL score combining all factors"""
    # Base score from active lineup (weighted at 100%)
    base_score = active_points

    # Add depth points (weighted at 85%)
    depth_score = depth_points

    # Apply division factor
    total_score = (base_score + depth_score) * division_factor

    # Scale to 1000-point basis for readability
    scaled_score = (total_score / 10)

    return round(scaled_score, 1)

def render(roster_data: pd.DataFrame):
    """Render projected rankings section"""
    try:
        # Add custom CSS with animations
        st.markdown("""
        <style>
        @keyframes slideIn {
            from {
                transform: translateX(-20px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
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

        .title-container {
            background: linear-gradient(135deg, #1a1c23 0%, #2a2c33 100%);
            padding: 1.5rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            animation: fadeIn 0.8s ease-out;
            border-bottom: 3px solid #E63946;  /* Patriotic red */
        }

        .rank-card {
            animation: slideIn 0.5s ease-out;
            transition: transform 0.2s ease;
        }

        .rank-card:hover {
            transform: translateY(-2px);
            animation: pulse 1s infinite;
        }

        .division-indicator {
            width: 3px;
            height: 100%;
            position: absolute;
            left: 0;
            top: 0;
            transition: background-color 0.3s ease;
        }
        </style>
        """, unsafe_allow_html=True)

        # Header with updated styling
        st.markdown("""
        <div class="title-container">
            <h1 style="color: #fff; margin: 0;">📊 Armchair Baseball League Power Rankings</h1>
            <p style="color: #aaa; margin: 0.5rem 0 0 0;">Advanced analytics and projections</p>
        </div>
        """, unsafe_allow_html=True)

        # Load division data
        divisions_df = pd.read_csv("attached_assets/divisions.csv", header=None, names=['division', 'team'])
        division_mapping = dict(zip(divisions_df['team'], divisions_df['division']))

        # Updated patriotic color scheme for divisions
        division_colors = {
            "AL East": "#E63946",    # Patriotic red
            "AL Central": "#457B9D", # Patriotic blue
            "AL West": "#1D3557",    # Dark blue
            "NL East": "#F1FAEE",    # Off white
            "NL Central": "#A8DADC", # Light blue
            "NL West": "#E63946"     # Patriotic red
        }

        position_limits = {
            'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1,
            'LF': 1, 'CF': 1, 'RF': 1, 'UT': 1,
            'SP': 3, 'RP': 3, 'P': 1
        }

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

        # Calculate team rankings
        team_rankings_data = []
        for team in roster_data['team'].unique():
            team_roster = roster_data[roster_data['team'] == team].copy()
            team_roster['clean_name'] = team_roster['player_name'].apply(normalize_name)

            # Calculate player points
            team_roster['projected_points'] = 0.0
            for idx, player in team_roster.iterrows():
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
            division = division_mapping.get(team, "Unknown")
            division_factor = 1.0 #division_strength.get(division, 1.0) #removed division strength

            # Calculate ABL Score
            abl_score = calculate_abl_score(active_points, depth_points, division_factor)

            team_rankings_data.append({
                'team': team,
                'abl_score': abl_score,
                'active_lineup_points': active_points,
                'depth_points': depth_points,
                'division_factor': division_factor,
                'raw_total': active_points + depth_points,
                'adjusted_total': (active_points + depth_points) * division_factor
            })

        # Create rankings DataFrame and sort by ABL score
        team_rankings = pd.DataFrame(team_rankings_data)
        team_rankings = team_rankings.sort_values('abl_score', ascending=False)
        team_rankings = team_rankings.reset_index(drop=True)
        team_rankings.index = team_rankings.index + 1

        # Display prominent rankings table
        st.subheader("🏆 ABL Power Rankings")

        # Top 3 teams in cards
        col1, col2, col3 = st.columns(3)


        # Display top 3 teams in cards with enhanced styling
        for idx, (col, (_, row)) in enumerate(zip([col1, col2, col3], team_rankings.head(3).iterrows())):
            with col:
                division = division_mapping.get(row['team'], "Unknown")
                color = division_colors.get(division, "#E63946")
                st.markdown(f"""
                <div class="rank-card" style="
                    padding: 1.5rem;
                    background: linear-gradient(145deg, #1a1c23 0%, #2a2c33 100%);
                    border-radius: 15px;
                    margin: 0.5rem 0;
                    border: 1px solid rgba(255,255,255,0.1);
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    position: relative;
                    overflow: hidden;
                ">
                    <div class="division-indicator" style="background-color: {color};"></div>
                    <h3 style="margin:0; color: {color}; font-size: 1.8rem;">#{idx + 1}</h3>
                    <h4 style="margin:0.5rem 0; color: #fff; font-size: 1.3rem;">{row['team']}</h4>
                    <p style="margin:0; font-size: 1.4rem; color: #F1FAEE;">
                        {row['abl_score']:.1f}
                    </p>
                    <p style="margin:0.5rem 0 0 0; font-size: 0.9rem; color: {color};">
                        {division}
                    </p>
                </div>
                """, unsafe_allow_html=True)

        # Display remaining teams with enhanced styling
        st.markdown("### Remaining Teams")

        for i, (_, row) in enumerate(team_rankings.iloc[3:].iterrows()):
            division = division_mapping.get(row['team'], "Unknown")
            color = division_colors.get(division, "#E63946")
            st.markdown(f"""
            <div class="rank-card" style="
                padding: 1rem;
                background: linear-gradient(145deg, #1a1c23 0%, #2a2c33 100%);
                border-radius: 10px;
                margin: 0.5rem 0;
                border: 1px solid rgba(255,255,255,0.1);
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                position: relative;
                overflow: hidden;
                display: flex;
                justify-content: space-between;
                align-items: center;
            ">
                <div class="division-indicator" style="background-color: {color};"></div>
                <div style="display: flex; align-items: center; gap: 1rem; padding-left: 1rem;">
                    <span style="color: {color}; font-size: 1.2rem; font-weight: bold;">#{i + 4}</span>
                    <div>
                        <div style="color: #fff; font-weight: bold;">{row['team']}</div>
                        <div style="font-size: 0.8rem; color: {color};">{division}</div>
                    </div>
                </div>
                <span style="font-weight: bold; font-size: 1.3rem; color: #F1FAEE; padding-right: 1rem;">
                    {row['abl_score']:.1f}
                </span>
            </div>
            """, unsafe_allow_html=True)

        # Division legend with updated styling
        st.markdown("### Division Legend")
        col1, col2 = st.columns(2)

        divisions = list(division_colors.items())
        mid = len(divisions) // 2

        for i, (division, color) in enumerate(divisions):
            col = col1 if i < mid else col2
            with col:
                st.markdown(f"""
                <div class="rank-card" style="
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                    margin: 0.25rem 0;
                    padding: 0.5rem;
                    border-radius: 5px;
                    background: rgba(26,28,35,0.5);
                ">
                    <div style="
                        width: 1rem;
                        height: 1rem;
                        background-color: {color};
                        border-radius: 3px;
                    "></div>
                    <span style="color: #fff;">{division}</span>
                </div>
                """, unsafe_allow_html=True)

        # Detailed Statistics section
        with st.expander("📊 Detailed Statistics"):
            st.dataframe(
                team_rankings,
                column_config={
                    "team": "Team",
                    "abl_score": st.column_config.NumberColumn(
                        "ABL Score",
                        format="%.1f",
                        help="Combined score based on active lineup, depth, and division strength"
                    ),
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
                        help="Additional value from bench players (weighted at 85%)"
                    ),
                    "division_factor": st.column_config.NumberColumn(
                        "Division Factor",
                        format="%.2f",
                        help="Strength of division adjustment (>1 means tougher division)"
                    )
                },
                hide_index=True
            )

            fig = px.bar(
                team_rankings,
                x='team',
                y=['active_lineup_points', 'depth_points'],
                title='Team Points Distribution',
                labels={
                    'team': 'Team',
                    'value': 'Projected Points',
                    'variable': 'Category'
                },
                barmode='stack',
                color_discrete_sequence=['#457B9D', '#E63946']  # Patriotic blue and red
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#ffffff',
                xaxis_tickangle=-45
            )
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"An error occurred while calculating projected rankings: {str(e)}")