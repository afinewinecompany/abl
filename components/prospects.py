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

def get_gradient_color(value: float, min_val: float, max_val: float) -> str:
    """Generate a color gradient between red and green based on value"""
    normalized = (value - min_val) / (max_val - min_val)
    red = int(255 * (1 - normalized))
    green = int(255 * normalized)
    blue = 0
    return f"rgb({red}, {green}, {blue})"

def render_prospect_preview(prospect, color):
    """Render a single prospect preview card"""
    # Get MLB team value and ensure it's a string before stripping
    mlb_team = str(prospect['mlb_team']).strip() if not pd.isna(prospect['mlb_team']) else "N/A"

    return f"""
    <div style="padding: 0.75rem; background-color: rgba(26, 28, 35, 0.5); border-radius: 8px; margin: 0.25rem 0; border-left: 3px solid {color}; transition: all 0.2s ease; cursor: pointer;" onmouseover="this.style.transform='translateX(4px)'; this.style.backgroundColor='rgba(26, 28, 35, 0.8)'; this.style.borderLeftWidth='5px';" onmouseout="this.style.transform='translateX(0)'; this.style.backgroundColor='rgba(26, 28, 35, 0.5)'; this.style.borderLeftWidth='3px';">
        <div style="display: flex; justify-content: space-between; align-items: center; gap: 1rem;">
            <div style="flex-grow: 1;">
                <div style="font-weight: 600; font-size: 0.95rem; margin-bottom: 0.2rem; color: #fafafa;">{prospect['player_name']}</div>
                <div style="font-size: 0.85rem; color: rgba(250, 250, 250, 0.7);">{prospect['position']} | Score: {prospect['prospect_score']:.1f}</div>
            </div>
            <div style="text-align: right; font-size: 0.85rem; color: rgba(250, 250, 250, 0.6);">{mlb_team}</div>
        </div>
    </div>"""

def render_team_card(team, team_rank, total_score, avg_score, ranked_prospects, division, color, top_3_prospects):
    """Render a team card with prospect preview"""
    preview_html = "".join([render_prospect_preview(prospect, color) 
                           for _, prospect in top_3_prospects.iterrows()])

    return f"""
    <div style="padding: 1.25rem; background-color: rgba(26, 28, 35, 0.8); border-radius: 12px; margin: 0.75rem 0; border-left: 5px solid {color}; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); transition: all 0.3s ease;" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 8px 16px rgba(0,0,0,0.2)'; this.style.borderLeftWidth='7px';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 6px rgba(0,0,0,0.1)'; this.style.borderLeftWidth='5px';">
        <div style="display: flex; justify-content: space-between; margin-bottom: 1rem; align-items: center;">
            <div>
                <div style="font-weight: 600; font-size: 1.1rem; color: #fafafa; margin-bottom: 0.2rem;">#{team_rank} {team}</div>
                <div style="font-size: 0.9rem; color: rgba(250, 250, 250, 0.7);">{division}</div>
            </div>
            <div style="text-align: right;">
                <div style="font-weight: 600; font-size: 1.1rem; color: #fafafa;">{total_score:.1f}</div>
                <div style="font-size: 0.85rem; color: rgba(250, 250, 250, 0.7);">Avg: {avg_score:.2f} | {int(ranked_prospects)} Players</div>
            </div>
        </div>
        <div style="margin-top: 0.75rem;">
            <div style="font-size: 0.9rem; color: rgba(250, 250, 250, 0.8); margin-bottom: 0.5rem; font-weight: 500;">Top Prospects:</div>
            {preview_html}
        </div>
    </div>"""

def render_gradient_visualization(team_scores: pd.DataFrame, division_mapping: Dict[str, str]) -> None:
    """Render interactive prospect strength visualization"""
    st.subheader("🎨 Prospect Strength Visualization")

    # Create a color scale for the bars
    team_scores['normalized_score'] = (team_scores['total_score'] - team_scores['total_score'].min()) / \
                                    (team_scores['total_score'].max() - team_scores['total_score'].min())

    # Add division information
    team_scores['division'] = team_scores['team'].map(division_mapping)

    # Create horizontal bar chart
    fig = px.bar(
        team_scores,
        y='team',
        x='total_score',
        orientation='h',
        color='normalized_score',
        color_continuous_scale='RdYlGn',  # Red to Yellow to Green scale
        hover_data={
            'normalized_score': False,
            'ranked_prospects': True,
            'division': True,
            'total_score': ':.1f',
            'avg_score': ':.2f'
        },
        labels={
            'team': 'Team',
            'total_score': 'Total Prospect Score',
            'ranked_prospects': 'Total Prospects',
            'division': 'Division',
            'avg_score': 'Average Score'
        },
        height=800  # Taller to accommodate all teams
    )

    # Update layout for better mobile viewing
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        coloraxis_showscale=False,  # Hide the color scale
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        xaxis=dict(
            gridcolor='rgba(128,128,128,0.1)',
            title_font=dict(size=14),
            tickfont=dict(size=12),
        ),
        yaxis=dict(
            gridcolor='rgba(128,128,128,0.1)',
            title_font=dict(size=14),
            tickfont=dict(size=12),
        ),
        hoverlabel=dict(
            bgcolor='#1a1c23',
            font_size=14,
            font_family="sans serif"
        )
    )

    # Add hover template
    fig.update_traces(
        hovertemplate="<b>%{y}</b><br>" +
                      "Total Score: %{x:.1f}<br>" +
                      "Avg Score: %{customdata[4]:.2f}<br>" +
                      "Division: %{customdata[2]}<br>" +
                      "Total Prospects: %{customdata[1]}<extra></extra>"
    )

    # Display the chart
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

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

        # Read and process prospect scores
        prospect_import = pd.read_csv("attached_assets/ABL-Import.csv")
        prospect_import['Name'] = prospect_import['Name'].apply(normalize_name)

        # Get all minor league players
        minors_players = roster_data[roster_data['status'].str.upper() == 'MINORS'].copy()
        minors_players['clean_name'] = minors_players['player_name'].apply(normalize_name)

        # Merge with import data
        ranked_prospects = pd.merge(
            minors_players,
            prospect_import[['Name', 'Position', 'MLB Team', 'Unique score']],
            left_on='clean_name',
            right_on='Name',
            how='left'
        )

        # Set prospect score from Unique score
        ranked_prospects['prospect_score'] = ranked_prospects['Unique score'].fillna(0)
        ranked_prospects.rename(columns={'MLB Team': 'mlb_team'}, inplace=True)


        # Calculate team rankings
        team_scores = ranked_prospects.groupby('team').agg({
            'prospect_score': ['sum', 'mean', 'count']
        }).reset_index()

        team_scores.columns = ['team', 'total_score', 'avg_score', 'ranked_prospects']
        team_scores = team_scores.sort_values('total_score', ascending=False)
        team_scores = team_scores.reset_index(drop=True)
        team_scores.index = team_scores.index + 1

        # Render gradient visualization first
        render_gradient_visualization(team_scores, division_mapping)

        # Display top 3 teams
        st.subheader("🏆 Top Prospect Systems")
        col1, col2, col3 = st.columns(3)

        # Display top 3 teams in cards
        for idx, (col, row) in enumerate(zip([col1, col2, col3], team_scores.head(3).iterrows())):
            with col:
                division = division_mapping.get(row[1]['team'], "Unknown")
                color = division_colors.get(division, "#00ff88")

                # Get team's prospects (only display top 3)
                team_prospects = ranked_prospects[ranked_prospects['team'] == row[1]['team']].sort_values(
                    'prospect_score', ascending=False
                )
                top_3_prospects = team_prospects.head(3)

                # Display team card
                st.markdown(render_team_card(
                    row[1]['team'],
                    idx + 1,  # Rank 1-3
                    row[1]['total_score'],
                    row[1]['avg_score'],
                    row[1]['ranked_prospects'],
                    division,
                    color,
                    top_3_prospects
                ), unsafe_allow_html=True)

        # Show remaining teams
        st.markdown("### Remaining Teams")

        # Display teams 4-30 in single column
        remaining_teams = team_scores.iloc[3:]

        # Reset index for remaining teams to ensure correct rank numbering
        remaining_teams = remaining_teams.reset_index(drop=True)

        for idx, row in remaining_teams.iterrows():
            division = division_mapping.get(row['team'], "Unknown")
            color = division_colors.get(division, "#00ff88")

            # Get team's prospects (only display top 3)
            team_prospects = ranked_prospects[ranked_prospects['team'] == row['team']].sort_values(
                'prospect_score', ascending=False
            )
            top_3_prospects = team_prospects.head(3)

            # Display team card with correct rank (starting from 4)
            st.markdown(render_team_card(
                row['team'],
                idx + 4,  # Start numbering from 4
                row['total_score'],
                row['avg_score'],
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

    except Exception as e:
        st.error(f"An error occurred while processing prospect data: {str(e)}")