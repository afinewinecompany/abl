import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from typing import Dict

def normalize_name(name: str) -> str:
    """Normalize player name for comparison"""
    try:
        if ',' in name:
            last, first = name.split(',', 1)
            return f"{first.strip()} {last.strip()}"
        return name.strip()
    except:
        return name.strip()

def calculate_prospect_score(ranking: int) -> float:
    """
    Calculate prospect score based on ranking using exponential decay.
    - Ranked prospects (1-600) get scores from 100 to ~5
    - Unranked prospects get a baseline score of 2

    Formula: score = 100 * e^(-0.005 * (rank-1))
    This creates an exponential decay where:
    - #1 prospect = 100 points
    - #100 prospect ≈ 60 points
    - #300 prospect ≈ 22 points
    - #600 prospect ≈ 5 points
    """
    if pd.isna(ranking):
        return 2.0  # Baseline score for unranked prospects

    # Exponential decay formula
    decay_rate = 0.005  # Controls how quickly scores decline
    score = 100 * np.exp(-decay_rate * (ranking - 1))

    return round(score, 1)

def get_gradient_color(value: float, min_val: float, max_val: float) -> str:
    """Generate a color gradient between red and green based on value"""
    # Normalize value between 0 and 1
    normalized = (value - min_val) / (max_val - min_val)

    # Generate RGB values for gradient from red (low) to green (high)
    red = int(255 * (1 - normalized))
    green = int(255 * normalized)
    blue = 0

    return f"rgb({red}, {green}, {blue})"

def render_prospect_preview(prospect, color):
    """Render a single prospect preview card"""
    rank_color = "#00ff88" if pd.notna(prospect['Ranking']) else "#888"
    return f"""
    <div style="
        padding: 0.5rem;
        background-color: #1a1c23;
        border-radius: 8px;
        margin: 0.25rem 0;
        border-left: 3px solid {color};
        transition: all 0.3s ease;
        cursor: pointer;
        transform-origin: center;
    "
    onmouseover="this.style.transform='scale(1.02)';
                 this.style.boxShadow='0 8px 16px rgba(0,0,0,0.2)';
                 this.style.borderLeftWidth='6px';
                 this.style.backgroundColor='#22242c';"
    onmouseout="this.style.transform='scale(1)';
                this.style.boxShadow='none';
                this.style.borderLeftWidth='3px';
                this.style.backgroundColor='#1a1c23';">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-weight: bold;">{prospect['player_name']}</div>
                <div style="font-size: 0.8rem; color: #888;">
                    {prospect['position']} | Score: {prospect['prospect_score']:.1f}
                </div>
            </div>
            <div style="text-align: right;">
                <div style="color: {rank_color};">
                    {f"#{int(prospect['Ranking'])}" if pd.notna(prospect['Ranking']) else "Unranked"}
                </div>
            </div>
        </div>
    </div>"""

def render_team_card(team, team_rank, score, ranked_prospects, division, color, top_3_prospects):
    """Render a team card with prospect preview"""
    preview_html = "".join([render_prospect_preview(prospect, color) 
                           for _, prospect in top_3_prospects.iterrows()])

    return f"""
    <div style="
        padding: 1rem;
        background-color: #1a1c23;
        border-radius: 10px;
        border-left: 5px solid {color};
        margin: 0.5rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
        cursor: pointer;
        transform-origin: center;
    "
    onmouseover="this.style.transform='scale(1.01)';
                 this.style.boxShadow='0 8px 16px rgba(0,0,0,0.2)';
                 this.style.borderLeftWidth='8px';"
    onmouseout="this.style.transform='scale(1)';
                this.style.boxShadow='0 4px 6px rgba(0,0,0,0.1)';
                this.style.borderLeftWidth='5px';">
        <div style="display: flex; justify-content: space-between; margin-bottom: 1rem;">
            <div>
                <div style="font-weight: bold; font-size: 1.2rem;">#{team_rank} {team}</div>
                <div style="font-size: 0.8rem; color: #888;">{division}</div>
            </div>
            <div style="text-align: right;">
                <div style="font-weight: bold; font-size: 1.2rem;">{score:.1f}</div>
                <div style="font-size: 0.8rem; color: #888;">{int(ranked_prospects)} Ranked</div>
            </div>
        </div>
        <div style="margin-top: 0.5rem;">
            <div style="font-size: 0.9rem; color: #888; margin-bottom: 0.5rem;">Top Prospects:</div>
            {preview_html}
        </div>
    </div>"""

def render_gradient_visualization(team_scores: pd.DataFrame, division_mapping: Dict[str, str]) -> None:
    """Render interactive prospect strength visualization"""
    st.subheader("🎨 Prospect Strength Visualization")

    # Calculate min and max scores for color scaling
    min_score = team_scores['total_score'].min()
    max_score = team_scores['total_score'].max()

    # Create visualization grid - 3 columns for better mobile viewing
    cols = st.columns(3)  # 3 columns for 30 teams (10 rows)

    for idx, (_, row) in enumerate(team_scores.iterrows()):
        col = cols[idx % 3]
        with col:
            # Get team color based on prospect score
            gradient_color = get_gradient_color(row['total_score'], min_score, max_score)
            division = division_mapping.get(row['team'], "Unknown")

            st.markdown(f"""
            <div style="
                padding: 1rem;
                background-color: {gradient_color};
                border-radius: 12px;
                margin: 0.5rem 0;
                color: white;
                text-align: center;
                font-size: 1rem;
                text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
                transition: all 0.3s ease-in-out;
                cursor: pointer;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                min-height: 120px;
                display: flex;
                flex-direction: column;
                justify-content: center;
                position: relative;
                overflow: hidden;
            "
            onmouseover="
                this.style.transform='scale(1.05) translateY(-2px)';
                this.style.boxShadow='0 8px 16px rgba(0,0,0,0.2)';
                this.style.backgroundColor='{gradient_color}dd';
            "
            onmouseout="
                this.style.transform='scale(1) translateY(0)';
                this.style.boxShadow='0 2px 4px rgba(0,0,0,0.1)';
                this.style.backgroundColor='{gradient_color}';
            ">
                <div style="font-weight: bold; font-size: 1.1rem; margin-bottom: 0.3rem;">{row['team']}</div>
                <div style="font-size: 0.9rem; opacity: 0.9;">{division}</div>
                <div style="font-size: 1.2rem; margin: 0.5rem 0; font-weight: bold;">{row['total_score']:.1f}</div>
                <div style="font-size: 0.9rem; opacity: 0.9;">{int(row['ranked_prospects'])} Ranked</div>
            </div>
            """, unsafe_allow_html=True)

def render(roster_data: pd.DataFrame):
    """Render prospects analysis section"""
    try:
        st.header("🌟 Prospect Analysis")

        # Load division data for color coding
        divisions_df = pd.read_csv("attached_assets/divisions.csv", header=None, names=['division', 'team'])
        division_mapping = dict(zip(divisions_df['team'], divisions_df['division']))

        # Division color mapping
        division_colors = {
            "AL East": "#FF6B6B",  # Red shade
            "AL Central": "#4ECDC4",  # Teal shade
            "AL West": "#95A5A6",  # Gray shade
            "NL East": "#F39C12",  # Orange shade
            "NL Central": "#3498DB",  # Blue shade
            "NL West": "#2ECC71"   # Green shade
        }

        # Read and process prospect rankings
        prospect_rankings = pd.read_csv("attached_assets/2025 Dynasty Dugout Offseason Rankings - Jan 25 Prospects.csv")
        prospect_rankings['Player'] = prospect_rankings['Player'].str.strip()
        prospect_rankings['prospect_score'] = prospect_rankings['Ranking'].apply(calculate_prospect_score)

        # Get all minor league players
        minors_players = roster_data[roster_data['status'].str.upper() == 'MINORS'].copy()
        minors_players['clean_name'] = minors_players['player_name'].apply(normalize_name)

        # Merge with rankings
        ranked_prospects = pd.merge(
            minors_players,
            prospect_rankings[['Player', 'Ranking', 'Tier', 'prospect_score', 'Position', 'ETA']],
            left_on='clean_name',
            right_on='Player',
            how='left'
        )

        # Calculate team rankings (using ALL prospects)
        team_scores = ranked_prospects.groupby('team').agg({
            'prospect_score': 'sum',  # Total score of ALL prospects
            'Ranking': lambda x: x.notna().sum()  # Count of ALL ranked prospects
        }).reset_index()
        team_scores.columns = ['team', 'total_score', 'ranked_prospects']
        team_scores = team_scores.sort_values('total_score', ascending=False)
        team_scores = team_scores.reset_index(drop=True)
        team_scores.index = team_scores.index + 1

        # Render gradient visualization first
        render_gradient_visualization(team_scores, division_mapping)

        # Display top 3 teams
        st.subheader("🏆 Top Prospect Systems")
        col1, col2, col3 = st.columns(3)

        # Display top 3 teams in cards
        for idx, (col, (rank, row)) in enumerate(zip([col1, col2, col3], team_scores.head(3).iterrows())):
            with col:
                division = division_mapping.get(row['team'], "Unknown")
                color = division_colors.get(division, "#00ff88")

                # Get team's prospects (only display top 3)
                team_prospects = ranked_prospects[ranked_prospects['team'] == row['team']].sort_values(
                    'prospect_score', ascending=False
                )
                top_3_prospects = team_prospects.head(3)

                # Display team card
                st.markdown(render_team_card(
                    row['team'],
                    rank,
                    row['total_score'],
                    row['ranked_prospects'],
                    division,
                    color,
                    top_3_prospects
                ), unsafe_allow_html=True)

        # Show remaining teams
        st.markdown("### Remaining Teams")

        # Display teams 4-30 in single column
        remaining_teams = team_scores.iloc[3:]
        for rank, row in remaining_teams.iterrows():
            division = division_mapping.get(row['team'], "Unknown")
            color = division_colors.get(division, "#00ff88")

            # Get team's prospects (only display top 3)
            team_prospects = ranked_prospects[ranked_prospects['team'] == row['team']].sort_values(
                'prospect_score', ascending=False
            )
            top_3_prospects = team_prospects.head(3)

            # Display team card
            st.markdown(render_team_card(
                row['team'],
                rank + 3,  # Adjust rank for remaining teams
                row['total_score'],
                row['ranked_prospects'],
                division,
                color,
                top_3_prospects
            ), unsafe_allow_html=True)

        # Division legend
        st.markdown("### Division Color Guide")
        col1, col2 = st.columns(2)

        divisions = list(division_colors.items())
        mid = len(divisions) // 2

        for i, (division, color) in enumerate(divisions):
            col = col1 if i < mid else col2
            with col:
                st.markdown(f"""
                <div style="
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                    margin: 0.25rem 0;
                ">
                    <div style="
                        width: 1rem;
                        height: 1rem;
                        background-color: {color};
                        border-radius: 3px;
                    "></div>
                    <span>{division}</span>
                </div>
                """, unsafe_allow_html=True)

        # Tier Distribution
        with st.expander("📊 League-wide Tier Distribution"):
            tier_dist = ranked_prospects[ranked_prospects['Tier'].notna()].groupby(['team', 'Tier']).size().unstack(fill_value=0)

            fig = px.bar(
                tier_dist,
                title='Prospect Tier Distribution by Team',
                labels={'value': 'Number of Prospects', 'team': 'Team', 'variable': 'Tier'},
                barmode='group'
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"An error occurred while processing prospect data: {str(e)}")