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

def get_color_for_score(score: float, min_score: float, max_score: float) -> str:
    """Generate color based on score position in range from yellow (best) to purple (worst)"""
    # Normalize score to 0-1 range
    normalized = (score - min_score) / (max_score - min_score)
    # Create color gradient from yellow (#FFD700) to purple (#800080)
    r = int(255 * normalized + 128 * (1 - normalized))
    g = int(215 * normalized)
    b = int(128 * (1 - normalized))
    return f"#{r:02x}{g:02x}{b:02x}"

def get_team_prospects_html(prospects_df: pd.DataFrame) -> str:
    """Generate HTML for team prospects list"""
    avg_score = prospects_df['prospect_score'].mean()
    prospects_html = [
        f'<div style="font-size: 0.9rem; color: #fafafa; margin-bottom: 0.5rem;">Team Average Score: {avg_score:.2f}</div>'
    ]

    for _, prospect in prospects_df.iterrows():
        prospects_html.append(
            f'<div style="padding: 0.5rem; margin: 0.25rem 0; background: rgba(26, 28, 35, 0.3); border-radius: 4px;">'
            f'<div style="font-size: 0.9rem; color: #fafafa;">{prospect["player_name"]}</div>'
            f'<div style="font-size: 0.8rem; color: rgba(250, 250, 250, 0.7);">'
            f'{prospect["position"]} | Score: {prospect["prospect_score"]:.1f}</div>'
            f'</div>'
        )

    return "".join(prospects_html)

def render_prospect_preview(prospect, color, team_prospects=None):
    """Render a single prospect preview card with expandable details"""
    team_id = f"team_{prospect['player_name'].replace(' ', '_').lower()}"
    prospects_list = get_team_prospects_html(team_prospects) if team_prospects is not None else ""

    return f"""
    <div class="prospect-card" style="padding: 0.75rem; background-color: rgba(26, 28, 35, 0.5); border-radius: 8px; margin: 0.25rem 0; border-left: 3px solid {color}; transition: all 0.2s ease;">
        <div class="team-header" onclick="toggleTeam('{team_id}')" style="cursor: pointer; display: flex; justify-content: space-between; align-items: center; gap: 1rem;">
            <div style="flex-grow: 1;">
                <div style="font-weight: 600; font-size: 0.95rem; margin-bottom: 0.2rem; color: #fafafa;">
                    {prospect['player_name']}
                </div>
                <div style="font-size: 0.85rem; color: rgba(250, 250, 250, 0.7);">
                    {prospect['position']} | Score: {prospect['prospect_score']:.1f}
                </div>
            </div>
            <div style="text-align: right; font-size: 0.85rem; color: rgba(250, 250, 250, 0.6);">
                {TEAM_ABBREVIATIONS.get(str(prospect.get('mlb_team', '')), '')}
                <span class="arrow" id="arrow_{team_id}">▼</span>
            </div>
        </div>
        <div class="prospect-details" id="details_{team_id}" style="display: none; margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid rgba(255, 255, 255, 0.1);">
            {prospects_list}
        </div>
    </div>
    """

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

        # Add global styles and JavaScript
        st.markdown("""
        <style>
        @media screen and (max-width: 768px) {
            .prospect-card {
                padding: 0.5rem !important;
                margin: 0.15rem 0 !important;
            }
            .prospect-details {
                margin-top: 0.5rem !important;
                padding-top: 0.5rem !important;
            }
        }
        </style>
        <script>
        function toggleTeam(teamId) {
            var details = document.getElementById('details_' + teamId);
            var arrow = document.getElementById('arrow_' + teamId);
            var header = document.getElementById(teamId);

            if (details.style.display === 'none') {
                details.style.display = 'block';
                arrow.innerHTML = '▲';
            } else {
                details.style.display = 'none';
                arrow.innerHTML = '▼';
            }
        }
        </script>
        """, unsafe_allow_html=True)

        # Load division data
        divisions_df = pd.read_csv("attached_assets/divisions.csv", header=None, names=['division', 'team'])
        division_mapping = dict(zip(divisions_df['team'], divisions_df['division']))

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

        # Create sunburst visualization with adjusted height for mobile
        fig = create_sunburst_visualization(team_scores, division_mapping)
        fig.update_layout(
            height=450,  # Reduced height for better mobile viewing
            margin=dict(t=30, l=10, r=10, b=10)
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        # Add legend for color scale below the visualization
        st.markdown("""
        <div style="display: flex; flex-direction: column; gap: 0.5rem; margin: 0.5rem 0;">
            <div style="display: flex; height: 1.5rem; border-radius: 4px; background: linear-gradient(90deg, #FFD700 0%, #4169E1 50%, #800080 100%);"></div>
            <div style="display: flex; justify-content: space-between; font-size: 0.9rem;">
                <span>Higher Average Score</span>
                <span>Medium</span>
                <span>Lower Average Score</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Add explanation
        st.markdown("""
        #### Understanding the Visualization
        - **Size**: Represents total prospect value
        - **Color**: Indicates average prospect quality
        - **Hierarchy**: League → Division → Team
        - Hover over segments for detailed information
        """)

        # Get score range for color gradient - use average scores instead of total
        min_score = team_scores['avg_score'].min()
        max_score = team_scores['avg_score'].max()

        # Display top 3 teams
        st.subheader("🏆 Top Prospect Systems")
        col1, col2, col3 = st.columns(3)

        columns = [col1, col2, col3]
        for idx, (_, row) in enumerate(team_scores.head(3).iterrows()):
            with columns[idx]:
                color = get_color_for_score(row['avg_score'], min_score, max_score)
                team_prospects = ranked_prospects[ranked_prospects['team'] == row['team']].sort_values(
                    'prospect_score', ascending=False
                )
                st.markdown(render_prospect_preview({
                    'player_name': f"#{idx + 1} {row['team']}",
                    'position': division_mapping.get(row['team'], "Unknown"),
                    'prospect_score': row['total_score'],
                    'mlb_team': row['team']
                }, color, team_prospects), unsafe_allow_html=True)

        # Show remaining teams
        st.markdown("### Remaining Teams")
        remaining_teams = team_scores.iloc[3:]

        for i, (_, row) in enumerate(remaining_teams.iterrows()):
            color = get_color_for_score(row['avg_score'], min_score, max_score)
            team_prospects = ranked_prospects[ranked_prospects['team'] == row['team']].sort_values(
                'prospect_score', ascending=False
            )
            st.markdown(render_prospect_preview({
                'player_name': f"#{i + 4} {row['team']}",
                'position': division_mapping.get(row['team'], "Unknown"),
                'prospect_score': row['total_score'],
                'mlb_team': row['team']
            }, color, team_prospects), unsafe_allow_html=True)

        # Add legend for color scale
        st.markdown("### Color Scale Legend")
        st.markdown("""
        <div style="display: flex; flex-direction: column; gap: 0.5rem; margin: 1rem 0;">
            <div style="display: flex; height: 2rem; border-radius: 4px; background: linear-gradient(90deg, #FFD700 0%, #4169E1 50%, #800080 100%);"></div>
            <div style="display: flex; justify-content: space-between;">
                <span>Higher Average Score</span>
                <span>Medium</span>
                <span>Lower Average Score</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"An error occurred while processing prospect data: {str(e)}")