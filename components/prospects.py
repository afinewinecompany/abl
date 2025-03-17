import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from typing import Dict
import unicodedata

def normalize_name(name: str) -> str:
    """Normalize player name for comparison"""
    try:
        # Convert diacritics to ASCII
        name = ''.join(c for c in unicodedata.normalize('NFKD', name)
                      if not unicodedata.combining(c))

        if ',' in name:
            last, first = name.split(',', 1)
            name = f"{first.strip()} {last.strip()}"

        # Handle middle initials by removing them
        parts = name.strip().split()
        if len(parts) > 2:
            # If middle part is an initial (one letter possibly with period)
            if len(parts[1]) <= 2 and ('.' in parts[1] or len(parts[1]) == 1):
                name = f"{parts[0]} {parts[-1]}"

        return name.strip()
    except:
        return name.strip()

# Team abbreviation mapping with additional variations
TEAM_ABBREVIATIONS = {
    "Baltimore Orioles": "BAL",
    "Boston Red Sox": "BOS",
    "New York Yankees": "NYY",
    "Tampa Bay Rays": "TB",
    "Toronto Blue Jays": "TOR",
    "Chicago White Sox": "CHW",
    "Cleveland Guardians": "CLE",
    "Detroit Tigers": "DET",
    "Kansas City Royals": "KC",
    "Minnesota Twins": "MIN",
    "Houston Astros": "HOU",
    "Los Angeles Angels": "LAA",
    "Athletics": "ATH",  # Added variation
    "Oakland Athletics": "ATH",
    "Seattle Mariners": "SEA",
    "Texas Rangers": "TEX",
    "Atlanta Braves": "ATL",
    "Miami Marlins": "MIA",
    "New York Mets": "NYM",
    "Philadelphia Phillies": "PHI",
    "Washington Nationals": "WSH",
    "Chicago Cubs": "CHC",
    "Cincinnati Reds": "CIN",
    "Milwaukee Brewers": "MIL",
    "Pittsburgh Pirates": "PIT",
    "Cardinals": "STL",  # Added variation
    "Saint Louis Cardinals": "STL",  # Added variation
    "St Louis Cardinals": "STL",  # Added variation without period
    "St. Louis Cardinals": "STL",
    "Arizona Diamondbacks": "ARI",
    "Colorado Rockies": "COL",
    "Los Angeles Dodgers": "LAD",
    "San Diego Padres": "SD",
    "San Francisco Giants": "SF"
}

def get_gradient_color(value: float, min_val: float, max_val: float) -> str:
    """Generate a color gradient between red and green based on value"""
    normalized = (value - min_val) / (max_val - min_val)
    red = int(255 * (1 - normalized))
    green = int(255 * normalized)
    blue = 0
    return f"rgb({red}, {green}, {blue})"

def render_prospect_preview(prospect, color):
    """Render a single prospect preview card"""
    # Handle MLB team display - ensure single value and handle NaN
    mlb_team = prospect.get('mlb_team', 'N/A')
    if isinstance(mlb_team, pd.Series):
        mlb_team = mlb_team.iloc[0] if not mlb_team.empty else 'N/A'
    mlb_team = str(mlb_team).strip() if pd.notna(mlb_team) else 'N/A'

    return f"""
    <div style="padding: 0.75rem; background-color: rgba(26, 28, 35, 0.5); border-radius: 8px; margin: 0.25rem 0; border-left: 3px solid {color}; transition: all 0.2s ease; cursor: pointer;" onmouseover="this.style.transform='translateX(4px)'; this.style.backgroundColor='rgba(26, 28, 35, 0.8)'; this.style.borderLeftWidth='5px';" onmouseout="this.style.transform='translateX(0)'; this.style.backgroundColor='rgba(26, 28, 35, 0.5)'; this.style.borderLeftWidth='3px';">
        <div style="display: flex; justify-content: space-between; align-items: center; gap: 1rem;">
            <div style="flex-grow: 1;">
                <div style="font-weight: 600; font-size: 0.95rem; margin-bottom: 0.2rem; color: #fafafa;">{prospect['player_name']}</div>
                <div style="font-size: 0.85rem; color: rgba(250, 250, 250, 0.7);">{prospect['position']} | Score: {prospect['prospect_score']:.1f}</div>
            </div>
            <div style="text-align: right; font-size: 0.85rem; color: rgba(250, 250, 250, 0.6);">{TEAM_ABBREVIATIONS.get(mlb_team, mlb_team)}</div>
        </div>
    </div>"""

def render(roster_data: pd.DataFrame):
    """Render prospects analysis section"""
    try:
        st.header("📚 Prospect Analysis")

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
            'prospect_score': ['sum', 'mean']
        }).reset_index()

        team_scores.columns = ['team', 'total_score', 'avg_score']
        team_scores = team_scores.sort_values('total_score', ascending=False)
        team_scores = team_scores.reset_index(drop=True)
        team_scores.index = team_scores.index + 1

        # Create visualization data
        team_scores['team_abbrev'] = team_scores['team'].map(TEAM_ABBREVIATIONS)
        team_scores['division'] = team_scores['team'].map(division_mapping)

        # Create division-level aggregates
        division_scores = team_scores.groupby('division').agg({
            'avg_score': 'mean',
            'total_score': 'sum'
        }).reset_index()

        # Create league-level aggregates
        league_scores = pd.DataFrame([{
            'level': 'League',
            'avg_score': team_scores['avg_score'].mean(),
            'total_score': team_scores['total_score'].sum()
        }])

        # Prepare data for sunburst chart
        sunburst_data = pd.DataFrame({
            'ids': ['League'] + 
                  [f"div_{div}" for div in division_scores['division']] +
                  [f"team_{team}" for team in team_scores['team_abbrev']],
            'labels': ['League'] + 
                     list(division_scores['division']) +
                     list(team_scores['team_abbrev']),
            'parents': [''] + 
                      ['League'] * len(division_scores) +
                      list(team_scores['division']),
            'values': [league_scores['total_score'].iloc[0]] +
                     list(division_scores['total_score']) +
                     list(team_scores['total_score']),
            'colors': [league_scores['avg_score'].iloc[0]] +
                     list(division_scores['avg_score']) +
                     list(team_scores['avg_score'])
        })

        # Create sunburst chart
        fig = go.Figure(go.Sunburst(
            ids=sunburst_data['ids'],
            labels=sunburst_data['labels'],
            parents=sunburst_data['parents'],
            values=sunburst_data['values'],
            branchvalues='total',
            textinfo='label+value',
            marker=dict(
                colors=sunburst_data['colors'],
                colorscale='viridis',
                showscale=True,
                colorbar=dict(
                    title=dict(
                        text='Average Score',
                        font=dict(color='white')
                    ),
                    tickfont=dict(color='white')
                )
            ),
            hovertemplate="""
            <b>%{label}</b><br>
            Total Score: %{value:.1f}<br>
            Average Score: %{marker.color:.2f}
            <extra></extra>
            """
        ))

        # Update layout
        fig.update_layout(
            title=dict(
                text='Prospect System Hierarchy',
                font=dict(color='white'),
                x=0.5,
                xanchor='center'
            ),
            height=700,
            font=dict(color='white'),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=30, l=10, r=10, b=10)
        )

        # Display the chart
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        # Add explanation
        st.markdown("""
        #### Understanding the Visualization
        - **Size**: Represents total prospect value
        - **Color**: Indicates average prospect quality
        - **Hierarchy**: League → Division → Team
        - Hover over segments for detailed information
        """)

        # Display top 3 teams
        st.subheader("🏆 Top Prospect Systems")
        col1, col2, col3 = st.columns(3)

        # Display top 3 teams in cards
        for idx, (col, (_, row)) in enumerate(zip([col1, col2, col3], team_scores.head(3).iterrows())):
            with col:
                division = division_mapping.get(row['team'], "Unknown")
                color = division_colors.get(division, "#00ff88")

                # Get team's prospects (only display top 3)
                team_prospects = ranked_prospects[ranked_prospects['team'] == row['team']].sort_values(
                    'prospect_score', ascending=False
                )
                top_3_prospects = team_prospects.head(3)

                # Display team card
                st.markdown(render_prospect_preview({
                    'player_name': f"#{idx + 1} {row['team']}",
                    'position': division,
                    'prospect_score': row['total_score'],
                    'mlb_team': row['team']
                }, color), unsafe_allow_html=True)

    except Exception as e:
        st.error(f"An error occurred while processing prospect data: {str(e)}")