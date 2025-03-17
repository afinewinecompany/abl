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

def get_color_for_rank(rank: int, total_teams: int = 30) -> str:
    """Generate color based on rank position (1 = most red, 30 = most blue)"""
    # Normalize rank to 0-1 range (reverse it so 1 = 1.0 and 30 = 0.0)
    normalized = 1 - ((rank - 1) / (total_teams - 1))

    # Direct red to blue transition
    # Red: #DC143C (Crimson)
    # Blue: #4169E1 (Royal Blue)

    # Start color (Crimson)
    r1, g1, b1 = 220, 20, 60
    # End color (Royal Blue)
    r2, g2, b2 = 65, 105, 225

    # Linear interpolation between the two colors
    r = int(r1 * normalized + r2 * (1 - normalized))
    g = int(g1 * normalized + g2 * (1 - normalized))
    b = int(b1 * normalized + b2 * (1 - normalized))

    return f"#{r:02x}{g:02x}{b:02x}"

def render_prospect_preview(prospect, rank: int, team_prospects=None):
    """Render a single prospect preview card with native Streamlit expander"""
    color = get_color_for_rank(rank)

    st.markdown(
        f'<div style="padding: 0.75rem; background-color: rgba(26, 28, 35, 0.5); border-radius: 8px; margin: 0.25rem 0; border-left: 3px solid {color};">',
        unsafe_allow_html=True
    )

    # Display team header
    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: center; gap: 1rem;">
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
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Show prospects in expander
    if team_prospects is not None:
        with st.expander("Show Prospects"):
            prospects_html = get_team_prospects_html(team_prospects)
            st.markdown(prospects_html, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


def get_team_prospects_html(prospects_df: pd.DataFrame) -> str:
    """Generate HTML for team prospects list"""
    avg_score = prospects_df['prospect_score'].mean()
    prospects_html = [
        f'<div style="font-size: 0.9rem; color: #fafafa; margin-bottom: 0.5rem;">Team Average Score: {avg_score:.2f}</div>'
    ]

    for _, prospect in prospects_df.iterrows():
        # Add headshot for Kristian Campbell as a test
        headshot_html = ""
        if "kristian campbell" in prospect['player_name'].lower():
            headshot_html = """
                <div style="width: 60px; height: 60px; min-width: 60px; border-radius: 50%; overflow: hidden; margin-right: 1rem;">
                    <img src="https://img.mlbstatic.com/mlb-photos/image/upload/w_213,d_people:generic:headshot:silo:current.png,q_auto:best,f_auto/v1/people/692225/headshot/67/current"
                         style="width: 100%; height: 100%; object-fit: cover;"
                         onerror="this.src='data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgdmlld0JveD0iMCAwIDYwIDYwIj48cmVjdCB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIGZpbGw9IiMzMzMiLz48dGV4dCB4PSIzMCIgeT0iMzAiIGZpbGw9IiNmZmYiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGFsaWdubWVudC1iYXNlbGluZT0ibWlkZGxlIiBmb250LXNpemU9IjIwIj4/PC90ZXh0Pjwvc3ZnPg==';"
                         alt="Player headshot">
                </div>
            """

        prospects_html.append(
            f'<div style="padding: 0.5rem; margin: 0.25rem 0; background: rgba(26, 28, 35, 0.3); border-radius: 4px;">'
            f'<div style="display: flex; align-items: center;">'
            f'{headshot_html}'
            f'<div style="flex-grow: 1;">'
            f'<div style="font-size: 0.9rem; color: #fafafa;">{prospect["player_name"]}</div>'
            f'<div style="font-size: 0.8rem; color: rgba(250, 250, 250, 0.7);">'
            f'{prospect["position"]} | Score: {prospect["prospect_score"]:.1f}</div>'
            f'</div>'
            f'</div>'
            f'</div>'
        )

    return "".join(prospects_html)

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

def normalize_within_groups(df: pd.DataFrame, group_col: str, value_col: str) -> pd.Series:
    """Normalize values within groups to 0-1 range"""
    return df.groupby(group_col)[value_col].transform(lambda x: (x - x.min()) / (x.max() - x.min()))

def create_sunburst_visualization(team_scores: pd.DataFrame, division_mapping: Dict[str, str]):
    """Create the sunburst visualization with league-wide team comparisons"""
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

    # Normalize team scores against all teams in the league
    team_scores['normalized_score'] = (team_scores['avg_score'] - team_scores['avg_score'].min()) / \
                                    (team_scores['avg_score'].max() - team_scores['avg_score'].min())

    # Normalize division scores against other divisions
    division_scores['normalized_score'] = (division_scores['avg_score'] - division_scores['avg_score'].min()) / \
                                        (division_scores['avg_score'].max() - division_scores['avg_score'].min())

    # Create hierarchical data for sunburst
    data = []

    # Add league level
    data.append({
        'id': 'league',
        'parent': '',
        'label': 'League',
        'value': league_total,
        'color': 0.5,  # Middle of color scale for root
        'avg_score': league_avg
    })

    # Add division level
    for _, div in division_scores.iterrows():
        data.append({
            'id': f"div_{div['division']}",
            'parent': 'league',
            'label': div['division'],
            'value': div['total_score'],
            'color': div['normalized_score'],
            'avg_score': div['avg_score']
        })

    # Add team level
    for _, team in team_scores.iterrows():
        data.append({
            'id': f"team_{team['team_abbrev']}",
            'parent': f"div_{team['division']}",
            'label': team['team_abbrev'],
            'value': team['total_score'],
            'color': team['normalized_score'],
            'avg_score': team['avg_score']
        })

    # Convert to DataFrame for easier handling
    df = pd.DataFrame(data)

    # Create sunburst chart with increased size and mobile optimization
    fig = go.Figure(go.Sunburst(
        ids=df['id'],
        labels=df['label'],
        parents=df['parent'],
        values=df['value'],
        branchvalues='total',
        textinfo='label',
        marker=dict(
            colors=df['color'],
            colorscale='RdYlBu_r',  # Red to Blue color scale
            showscale=True,
            colorbar=dict(
                title=dict(
                    text='Relative Prospect Score',
                    font=dict(color='white', size=12)
                ),
                tickfont=dict(color='white', size=10),
                len=0.6,  # Slightly longer colorbar
                yanchor='top',  # Position from top
                y=-0.12,  # Move down below the plot
                xanchor='center',
                x=0.5,  # Center horizontally
                orientation='h',  # Horizontal colorbar
                thickness=20,  # Slightly thicker bar
                bgcolor='rgba(0,0,0,0)'  # Transparent background
            )
        ),
        customdata=df[['avg_score']],
        hovertemplate="""
        <b>%{label}</b><br>
        Total Score: %{value:.1f}<br>
        Average Score: %{customdata[0]:.2f}<br>
        Relative Position: %{color:.2f}
        <extra></extra>
        """
    ))

    # Update layout with mobile-responsive settings
    fig.update_layout(
        title=dict(
            text='Prospect System Hierarchy',
            font=dict(color='white', size=24),
            x=0.5,
            xanchor='center',
            y=0.98
        ),
        width=None,  # Allow width to be responsive
        height=700,  # Fixed height that works well on both desktop and mobile
        font=dict(color='white'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(
            t=50,   # Top margin
            l=10,   # Left margin
            r=10,   # Right margin
            b=150,  # Increased bottom margin for colorbar
            pad=0   # No padding
        ),
        autosize=True,
        # Ensure the plot maintains aspect ratio
        xaxis=dict(
            scaleanchor='y',
            scaleratio=1
        ),
        yaxis=dict(
            scaleanchor='x',
            scaleratio=1
        )
    )

    return fig

def render(roster_data: pd.DataFrame):
    """Render prospects analysis section"""
    try:
        st.header("📚 Prospect Analysis")

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

        # Create and display sunburst visualization with increased size
        fig = create_sunburst_visualization(team_scores, division_mapping)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        # Add explanation
        st.markdown("""
        #### Understanding the Visualization
        - **Size**: Represents total prospect value
        - **Color**: Indicates average prospect quality
        - **Hierarchy**: League → Division → Team
        - Click on segments to zoom in/out
        """)


        # Display top 3 teams
        st.subheader("🏆 Top Prospect Systems")
        col1, col2, col3 = st.columns(3)

        columns = [col1, col2, col3]
        for idx, (_, row) in enumerate(team_scores.head(3).iterrows()):
            with columns[idx]:
                team_prospects = ranked_prospects[ranked_prospects['team'] == row['team']].sort_values(
                    'prospect_score', ascending=False
                )
                render_prospect_preview({
                    'player_name': f"#{idx + 1} {row['team']}",
                    'position': division_mapping.get(row['team'], "Unknown"),
                    'prospect_score': row['total_score'],
                    'mlb_team': row['team']
                }, idx + 1, team_prospects)

        # Show remaining teams
        st.markdown("### Remaining Teams")
        remaining_teams = team_scores.iloc[3:]

        for i, (_, row) in enumerate(remaining_teams.iterrows()):
            team_prospects = ranked_prospects[ranked_prospects['team'] == row['team']].sort_values(
                'prospect_score', ascending=False
            )
            render_prospect_preview({
                'player_name': f"#{i + 4} {row['team']}",
                'position': division_mapping.get(row['team'], "Unknown"),
                'prospect_score': row['total_score'],
                'mlb_team': row['team']
            }, i + 4, team_prospects)

        # Add legend for color scale
        st.markdown("### Color Scale Legend")
        st.markdown("""
        <div style="display: flex; flex-direction: column; gap: 0.5rem; margin: 1rem 0;">
            <div style="display: flex; height: 2rem; border-radius: 4px; background: linear-gradient(90deg, #DC143C 0%, #4169E1 100%);"></div>
            <div style="display: flex; justify-content: space-between;">
                <span>#1 Rank</span>
                <span>#15</span>
                <span>#30 Rank</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"An error occurred while processing prospect data: {str(e)}")