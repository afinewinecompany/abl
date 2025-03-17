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
                <span id="arrow_{team_id}">▼</span>
            </div>
        </div>
        <div id="{team_id}" style="display: none; margin-top: 0.75rem; border-top: 1px solid rgba(255, 255, 255, 0.1); padding-top: 0.75rem;">
            <div style="font-size: 0.9rem; color: #fafafa; margin-bottom: 0.5rem;">All Prospects:</div>
            {prospects_list}
        </div>
    </div>
    """

def create_sunburst_visualization(team_scores: pd.DataFrame, division_mapping: Dict[str, str] = None):
    """Create the visualization based on whether divisions exist"""
    if division_mapping:
        # Add division info when available
        team_scores['division'] = team_scores['team'].map(division_mapping)

        # Create division-level aggregates
        division_scores = team_scores.groupby('division').agg({
            'avg_score': 'mean',
            'total_score': 'sum'
        }).reset_index()

        # Create league-level aggregates
        league_total = team_scores['total_score'].sum()
        league_avg = team_scores['avg_score'].mean()

        # Create hierarchical data for sunburst
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
                'id': f"team_{team['team']}",
                'parent': f"div_{team['division']}",
                'label': team['team'],
                'value': team['total_score'],
                'color': team['avg_score']
            })

        # Create sunburst chart
        fig = go.Figure(go.Sunburst(
            ids=[d['id'] for d in data],
            labels=[d['label'] for d in data],
            parents=[d['parent'] for d in data],
            values=[d['value'] for d in data],
            branchvalues='total',
            textinfo='label',
            marker=dict(
                colors=[d['color'] for d in data],
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
            hovertemplate="""
            <b>%{label}</b><br>
            Total Score: %{value:.1f}<br>
            Average Score: %{customdata[0]:.2f}
            <extra></extra>
            """
        ))

    else:
        # Create treemap for leagues without divisions
        fig = px.treemap(
            team_scores,
            names='team',
            values='total_score',
            color='avg_score',
            color_continuous_scale='viridis',
            title='Prospect System Rankings',
            custom_data=['total_score', 'avg_score']
        )

        fig.update_traces(
            hovertemplate="""
            <b>%{label}</b><br>
            Total Score: %{customdata[0]:.1f}<br>
            Average Score: %{customdata[1]:.2f}<br>
            <extra></extra>
            """
        )

    fig.update_layout(
        title=dict(
            text='Prospect System Overview',
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

        # Add JavaScript for team expansion
        st.markdown("""
        <script>
        function toggleTeam(teamId) {
            var content = document.getElementById(teamId);
            var arrow = document.getElementById('arrow_' + teamId);
            if (content.style.display === 'none') {
                content.style.display = 'block';
                arrow.innerHTML = '▲';
            } else {
                content.style.display = 'none';
                arrow.innerHTML = '▼';
            }
        }
        </script>
        """, unsafe_allow_html=True)

        # Try to load division data (optional)
        try:
            divisions_df = pd.read_csv("attached_assets/divisions.csv", header=None, names=['division', 'team'])
            division_mapping = dict(zip(divisions_df['team'], divisions_df['division']))
        except:
            division_mapping = None

        # Generate team colors without relying on divisions
        unique_teams = roster_data['team'].unique()
        num_teams = len(unique_teams)
        team_colors = {
            team: f"hsl({(i * 360/num_teams)}, 70%, 50%)"
            for i, team in enumerate(unique_teams)
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

        # Create and display visualization
        fig = create_sunburst_visualization(team_scores, division_mapping)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        # Add explanation
        st.markdown("""
        #### Understanding the Visualization
        - **Size**: Represents total prospect value
        - **Color**: Indicates average prospect quality
        - **Organization**: Teams ranked by total prospect value
        - Hover over segments for detailed information
        """)

        # Display top 3 teams
        st.subheader("🏆 Top Prospect Systems")
        col1, col2, col3 = st.columns(3)

        columns = [col1, col2, col3]
        for idx, (_, row) in enumerate(team_scores.head(3).iterrows()):
            with columns[idx]:
                color = team_colors[row['team']]
                team_prospects = ranked_prospects[ranked_prospects['team'] == row['team']].sort_values(
                    'prospect_score', ascending=False
                )
                st.markdown(render_prospect_preview({
                    'player_name': f"#{idx + 1} {row['team']}",
                    'position': "Prospects",
                    'prospect_score': row['total_score']
                }, color, team_prospects), unsafe_allow_html=True)

        # Show remaining teams
        st.markdown("### Remaining Teams")
        remaining_teams = team_scores.iloc[3:]

        for i, (_, row) in enumerate(remaining_teams.iterrows()):
            color = team_colors[row['team']]
            team_prospects = ranked_prospects[ranked_prospects['team'] == row['team']].sort_values(
                'prospect_score', ascending=False
            )
            st.markdown(render_prospect_preview({
                'player_name': f"#{i + 4} {row['team']}",
                'position': "Prospects",
                'prospect_score': row['total_score']
            }, color, team_prospects), unsafe_allow_html=True)

    except Exception as e:
        st.error(f"An error occurred while processing prospect data: {str(e)}")