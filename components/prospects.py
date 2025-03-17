import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from typing import Dict
import unicodedata
import os

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

# Add team abbreviation mapping
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
    "Athletics": "ATH",
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
    "Cardinals": "STL",
    "Saint Louis Cardinals": "STL",
    "St Louis Cardinals": "STL",
    "St. Louis Cardinals": "STL",
    "Arizona Diamondbacks": "ARI",
    "Colorado Rockies": "COL",
    "Los Angeles Dodgers": "LAD",
    "San Diego Padres": "SD",
    "San Francisco Giants": "SF"
}

def get_team_prospects_html(prospects_df: pd.DataFrame) -> str:
    """Generate HTML for team prospects list"""
    prospects_html = []
    for _, prospect in prospects_df.iterrows():
        prospect_html = f"""
        <div style="padding: 0.5rem; margin: 0.25rem 0; background: rgba(26, 28, 35, 0.3); border-radius: 4px;">
            <div style="font-size: 0.9rem; color: #fafafa;">{prospect['player_name']}</div>
            <div style="font-size: 0.8rem; color: rgba(250, 250, 250, 0.7);">
                {prospect['position']} | Score: {prospect['prospect_score']:.1f}
            </div>
        </div>
        """
        prospects_html.append(prospect_html)
    return "\n".join(prospects_html)

def render_prospect_preview(prospect, color, team_prospects=None):
    """Render a single prospect preview card with expandable details"""
    team_id = f"team_{prospect['player_name'].replace(' ', '_').lower()}"
    prospects_list = get_team_prospects_html(team_prospects) if team_prospects is not None else ""

    return f"""
    <div style="padding: 0.75rem; background-color: rgba(26, 28, 35, 0.5); border-radius: 8px; margin: 0.25rem 0; border-left: 3px solid {color}; transition: all 0.2s ease;">
        <div onclick="toggleTeam('{team_id}')" style="cursor: pointer; display: flex; justify-content: space-between; align-items: center; gap: 1rem;">
            <div style="flex-grow: 1;">
                <div style="font-weight: 600; font-size: 0.95rem; margin-bottom: 0.2rem; color: #fafafa;">{prospect['player_name']}</div>
                <div style="font-size: 0.85rem; color: rgba(250, 250, 250, 0.7);">{prospect['position']} | Score: {prospect['prospect_score']:.1f}</div>
            </div>
            <div style="text-align: right; font-size: 0.85rem; color: rgba(250, 250, 250, 0.6);">
                {TEAM_ABBREVIATIONS.get(str(prospect.get('mlb_team', '')), '')}
                <span id="arrow_{team_id}">▼</span>
            </div>
        </div>
        <div id="{team_id}" style="display: none; margin-top: 0.75rem; border-top: 1px solid rgba(255, 255, 255, 0.1); padding-top: 0.75rem;">
            <div style="font-size: 0.9rem; color: #fafafa; margin-bottom: 0.5rem;">All Prospects:</div>
            {prospects_list}
        </div>
    </div>
    """

def create_sunburst_visualization(team_scores: pd.DataFrame, division_mapping: Dict[str, str]):
    """Create the sunburst visualization"""
    # Add team abbreviations and division info
    team_scores['team_abbrev'] = team_scores['team'].map(TEAM_ABBREVIATIONS)
    team_scores['division'] = team_scores['team'].map(division_mapping)

    # Create division-level aggregates
    division_scores = team_scores.groupby('division').agg({
        'avg_score': 'mean',
        'total_score': 'sum'
    }).reset_index()

    # Create league-level aggregates
    league_total = team_scores['total_score'].sum()
    league_avg = team_scores['avg_score'].mean()

    # Create hierarchical data
    data = []

    # Add league level
    data.append({
        'id': 'league',
        'parent': '',
        'label': 'League',
        'value': league_total,
        'color': league_avg
    })

    # Add division level
    for _, div in division_scores.iterrows():
        data.append({
            'id': f"div_{div['division']}",
            'parent': 'league',
            'label': div['division'],
            'value': div['total_score'],
            'color': div['avg_score']
        })

    # Add team level
    for _, team in team_scores.iterrows():
        data.append({
            'id': f"team_{team['team_abbrev']}",
            'parent': f"div_{team['division']}",
            'label': team['team_abbrev'],
            'value': team['total_score'],
            'color': team['avg_score']
        })

    # Convert to DataFrame for easier handling
    df = pd.DataFrame(data)

    # Create sunburst chart
    fig = go.Figure(go.Sunburst(
        ids=df['id'],
        labels=df['label'],
        parents=df['parent'],
        values=df['value'],
        branchvalues='total',
        textinfo='label',
        marker=dict(
            colors=df['color'],
            colorscale='viridis',
            showscale=True,
            colorbar=dict(
                title=dict(
                    text='Average Prospect Score (0-10)',
                    font=dict(color='white')
                ),
                tickformat='.2f',
                tickfont=dict(color='white')
            )
        ),
        customdata=df[['color']],
        hovertemplate="""
        <b>%{label}</b><br>
        Total Score: %{value:.1f}<br>
        Average Score: %{customdata[0]:.2f}
        <extra></extra>
        """
    ))

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

    return fig

def render(roster_data: pd.DataFrame):
    """Render prospects analysis section"""
    try:
        st.header("📚 Prospect Analysis")

        # Verify file paths exist before reading
        divisions_file = "attached_assets/divisions.csv"
        prospects_file = "attached_assets/ABL-Import.csv"

        if not os.path.exists(divisions_file):
            st.error(f"Missing required file: {divisions_file}")
            return
        if not os.path.exists(prospects_file):
            st.error(f"Missing required file: {prospects_file}")
            return

        # Load division data
        divisions_df = pd.read_csv(divisions_file, header=None, names=['division', 'team'])
        division_mapping = dict(zip(divisions_df['team'], divisions_df['division']))

        # Read and process prospect scores
        prospect_import = pd.read_csv(prospects_file)
        prospect_import['Name'] = prospect_import['Name'].apply(normalize_name)

        # Get all minor league players
        minors_players = roster_data[roster_data['status'].str.upper() == 'MINORS'].copy()

        if minors_players.empty:
            st.warning("No minor league players found in the roster data.")
            return

        minors_players['clean_name'] = minors_players['player_name'].apply(normalize_name)

        # Merge with import data
        ranked_prospects = pd.merge(
            minors_players,
            prospect_import[['Name', 'Position', 'MLB Team', 'Unique score']],
            left_on='clean_name',
            right_on='Name',
            how='left'
        )

        if ranked_prospects.empty:
            st.warning("No prospect data found after merging with rankings.")
            return

        # Set prospect score from Unique score
        ranked_prospects['prospect_score'] = ranked_prospects['Unique score'].fillna(0)
        ranked_prospects.rename(columns={'MLB Team': 'mlb_team'}, inplace=True)


        st.write("### Prospect Rankings")
        st.dataframe(
            ranked_prospects[['player_name', 'position', 'team', 'prospect_score']].sort_values(
                'prospect_score', ascending=False
            ),
            hide_index=True
        )

    except Exception as e:
        st.error(f"Error in prospects analysis: {str(e)}")
        st.write("Please verify that all required data files are present and properly formatted.")