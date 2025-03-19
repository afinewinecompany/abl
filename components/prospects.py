from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from typing import Dict
import unicodedata

# Add GM mapping at the top of the file with other constants
GM_MAPPING = {
    "Pittsburgh Pirates": "Duke",
    "Toronto Blue Jays": "Gary",
    "Milwaukee Brewers": "Zack",
    "San Francisco Giants": "Rourke",
    "Los Angeles Angels": "Cal",
    "Oakland Athletics": "Dylan",
    "Athletics": "Dylan",  # Handle both variations
    "Arizona Diamondbacks": "Carpy",
    "Tampa Bay Rays": "Kevin",
    "Baltimore Orioles": "Steve",
    "Detroit Tigers": "John",
    "Miami Marlins": "Other Frank",
    "Cincinnati Reds": "Linny",
    "New York Mets": "Matt",
    "Los Angeles Dodgers": "Joe",
    "Chicago Cubs": "Frank",
    "Philadelphia Phillies": "Adam",
    "New York Yankees": "Gary",
    "Texas Rangers": "Sam",
    "Atlanta Braves": "Aidan",
    "Colorado Rockies": "Allen",
    "Kansas City Royals": "Brendan",
    "San Diego Padres": "Greg",
    "Chicago White Sox": "Tom",
    "Washington Nationals": "Jordan & Cim",
    "Houston Astros": "Evan",
    "Saint Louis Cardinals": "Jeff",
    "Cardinals": "Jeff",  # Handle variations
    "Boston Red Sox": "Don",
    "Minnesota Twins": "Tyler",
    "Cleveland Guardians": "Mark",
    "Seattle Mariners": "Seth"
}

def normalize_name(name: str) -> str:
    """Normalize player name for comparison"""
    try:
        if pd.isna(name):
            return ""
        if not isinstance(name, str):
            return str(name).strip()

        name = name.lower()
        name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII')

        # Handle special cases first
        if "de jesus gonzalez" in name or "gonzalez, josuar" in name:
            return "josuar gonzalez"

        if ',' in name:
            last, first = name.split(',', 1)
            name = f"{first.strip()} {last.strip()}"

        name = name.split('(')[0].strip()
        name = name.split(' - ')[0].strip()
        name = name.replace('.', '').strip()
        name = ' '.join(name.split())

        return name
    except Exception as e:
        st.error(f"Error normalizing name '{name}': {str(e)}")
        return str(name).strip() if name is not None else ""

def render(roster_data: pd.DataFrame):
    """Main render function for prospects page"""
    st.header("🌟 Prospect Analysis")

    # Load division data
    divisions_df = pd.read_csv("attached_assets/divisions.csv", header=None, names=['division', 'team'])
    division_mapping = dict(zip(divisions_df['team'], divisions_df['division']))

    # Load MLB player IDs and create cache
    mlb_ids_df = pd.read_csv("attached_assets/mlb_player_ids-2.csv")
    player_id_cache = create_player_id_cache(mlb_ids_df)

    try:
        # Load and process prospect scores
        prospect_import = pd.read_csv("attached_assets/ABL-Import.csv", na_values=['NA', ''], keep_default_na=True)
        prospect_import['Name'] = prospect_import['Name'].fillna('').astype(str).apply(normalize_name)

        # Get all players that could be prospects (MINORS, ACTIVE, or RESERVE)
        prospects_data = roster_data.copy()
        prospects_data['clean_name'] = prospects_data['player_name'].fillna('').astype(str).apply(normalize_name)
        prospects_data = prospects_data.drop_duplicates(subset=['clean_name'], keep='first')

        # Merge with import data - ensure we keep all ranked players
        ranked_prospects = pd.merge(
            prospects_data,
            prospect_import[['Name', 'Position', 'MLB Team', 'Score', 'Rank']],
            left_on='clean_name',
            right_on=prospect_import['Name'].apply(normalize_name),
            how='outer'  # Changed to outer join to keep all players
        )

        # Fill missing values and clean up
        ranked_prospects['prospect_score'] = ranked_prospects['Score'].fillna(0)
        ranked_prospects['player_name'] = ranked_prospects['player_name'].fillna(ranked_prospects['Name'])
        ranked_prospects['position'] = ranked_prospects['Position'].fillna(ranked_prospects['position'])
        ranked_prospects['mlb_team'] = ranked_prospects['MLB Team'].fillna(ranked_prospects['team'])

        # Remove duplicates but keep the one with rank if available
        ranked_prospects = ranked_prospects.sort_values('Rank').drop_duplicates(
            subset=['Name'],
            keep='first'
        )

        # Rename columns for consistency
        ranked_prospects.rename(columns={
            'MLB Team': 'mlb_team',
            'Position': 'position'
        }, inplace=True)

        # Calculate global min/max scores for consistent color scaling
        global_max_score = ranked_prospects['prospect_score'].max()
        global_min_score = ranked_prospects['prospect_score'].min()

        # First render the Top 100 prospects list
        render_top_100_header(ranked_prospects, player_id_cache, global_max_score, global_min_score)

        # Calculate team rankings using average score
        team_scores = ranked_prospects.groupby('team').agg({
            'prospect_score': ['sum', 'mean', 'count']
        }).reset_index()

        team_scores.columns = ['team', 'total_score', 'avg_score', 'prospect_count']
        team_scores = team_scores.sort_values('avg_score', ascending=False)
        team_scores = team_scores.reset_index(drop=True)
        team_scores.index = team_scores.index + 1

        # Create and display sunburst visualization
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
                    'prospect_score': row['avg_score'],
                    'mlb_team': row['team']
                }, idx + 1, team_prospects, player_id_cache, global_max_score, global_min_score)

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
                'prospect_score': row['avg_score'],
                'mlb_team': row['team']
            }, i + 4, team_prospects, player_id_cache, global_max_score, global_min_score)

    except Exception as e:
        st.error(f"Error processing prospect data: {str(e)}")
        return

def create_player_id_cache(mlb_ids_df: pd.DataFrame) -> Dict[str, str]:
    """Create a cache of normalized player names to MLBAMID"""
    cache = {}
    try:
        for _, row in mlb_ids_df.iterrows():
            try:
                # Handle empty or NA values
                if pd.isna(row['Last']) or pd.isna(row['First']) or pd.isna(row['MLBAMID']):
                    continue

                # Create full name from First and Last
                name = normalize_name(f"{row['First']} {row['Last']}")

                # Only add if we have a valid name and MLBAMID
                if name and str(row['MLBAMID']).strip():
                    cache[name] = str(row['MLBAMID'])

                    # Add alternative name formats
                    alt_name = normalize_name(f"{row['Last']}, {row['First']}")
                    if alt_name:
                        cache[alt_name] = str(row['MLBAMID'])

            except Exception as e:
                st.warning(f"Error processing player ID row: {str(e)}")
                continue

    except Exception as e:
        st.error(f"Error creating player ID cache: {str(e)}")
    return cache

def get_headshot_url(mlbam_id: str) -> str:
    """Generate MLB/MILB headshot URL from player ID"""
    try:
        if not mlbam_id:
            return ""

        # Try different URL formats in order of preference
        urls = [
            # MILB format with c_fill
            f"https://img.mlbstatic.com/mlb-photos/image/upload/c_fill,g_auto/w_180/v1/people/{mlbam_id}/headshot/milb/current",
            # MLB format with d_people generic
            f"https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/{mlbam_id}/headshot/67/current",
            # MILB format with w_120
            f"https://img.mlbstatic.com/mlb-photos/image/upload/w_120,h_180,g_auto,c_fill/v1/people/{mlbam_id}/headshot/milb/current",
            # MLB format with 67
            f"https://img.mlbstatic.com/mlb-photos/image/upload/w_120,h_180,g_auto,c_fill/v1/people/{mlbam_id}/headshot/67/current",
            # MLB images format
            f"https://img.mlbstatic.com/mlb-images/image/upload/q_auto/mlb/{mlbam_id}",
            # Fallback MLB format
            f"https://img.mlbstatic.com/mlb-photos/image/upload/w_213,d_people:generic:headshot:silo:current.png,q_auto:best,f_auto/v1/people/{mlbam_id}/headshot/67/current"
        ]

        return urls[0]  # Return primary URL, let onerror handler try others
    except Exception as e:
        st.warning(f"Error generating headshot URL for ID {mlbam_id}: {str(e)}")
        return ""

def get_player_headshot_html(player_name: str, player_id_cache: Dict[str, str]) -> str:
    """Get player headshot HTML if available"""
    try:
        # Default fallback MLBAMID for missing headshots
        fallback_mlbamid = "805805"

        # Normalize name for lookup
        search_name = normalize_name(player_name)

        # Get player's MLBAMID if available, otherwise use fallback
        mlbam_id = player_id_cache.get(search_name, fallback_mlbamid)

        # Use a single fallback URL that's known to be reliable
        headshot_url = f"https://img.mlbstatic.com/mlb-photos/image/upload/w_213,d_people:generic:headshot:silo:current.png,q_auto:best,f_auto/v1/people/{mlbam_id}/headshot/67/current"

        return f"""<div class="player-headshot">
            <img src="{headshot_url}" 
                style="width: 60px; height: 60px; border-radius: 50%; object-fit: cover;" 
                alt="{player_name} headshot"
                onerror="this.onerror=null; this.src='https://img.mlbstatic.com/mlb-photos/image/upload/w_213,d_people:generic:headshot:silo:current.png,q_auto:best,f_auto/v1/people/805805/headshot/67/current';">
            </div>"""

    except Exception as e:
        st.warning(f"Error generating headshot HTML for {player_name}: {str(e)}")
        # Still use the fallback image instead of initials
        return f"""<div class="player-headshot">
            <img src="https://img.mlbstatic.com/mlb-photos/image/upload/w_213,d_people:generic:headshot:silo:current.png,q_auto:best,f_auto/v1/people/805805/headshot/67/current" 
                style="width: 60px; height: 60px; border-radius: 50%; object-fit: cover;" 
                alt="Default headshot">
            </div>"""

def get_team_prospects_html(prospects_df: pd.DataFrame, player_id_cache: Dict[str, str], global_max_score: float, global_min_score: float) -> str:
    """Generate HTML for team prospects list"""
    # Calculate total and average scores
    total_score = prospects_df['prospect_score'].sum()
    avg_score = prospects_df['prospect_score'].mean()
    num_prospects = len(prospects_df)

    # Start with container div
    html_parts = [
        '<div style="background: rgba(26, 28, 35, 0.3); border-radius: 8px; padding: 1rem;">',
        f'<div style="font-size: 0.9rem; color: #fafafa; margin-bottom: 1rem;">'
        f'Total System Score: {total_score:.2f} ({num_prospects} prospects)'
        '</div>'
    ]

    # Add each prospect
    for _, prospect in prospects_df.iterrows():
        # Ensure we get clean string values
        player_name = str(prospect.get('player_name', ''))
        position = str(prospect.get('position', ''))
        prospect_score = float(prospect.get('prospect_score', 0))

        # Get headshot HTML
        headshot_html = get_player_headshot_html(player_name, player_id_cache)

        # Start prospect card
        html_parts.append('<div style="padding: 1rem; margin: 0.5rem 0; background: rgba(26, 28, 35, 0.5); border-radius: 8px;">')
        html_parts.append('<div style="display: flex; align-items: center; gap: 1rem;">')

        # Add headshot
        html_parts.append(headshot_html)

        # Add prospect info
        # Clean up position by taking the first occurrence of position code
        clean_position = str(position).replace('position ', '').split('Name:')[0].strip().split()[0]
        html_parts.append(
            f'<div style="flex-grow: 1;">'
            f'<div style="font-size: 1rem; color: white; font-weight: 500; margin-bottom: 0.25rem;">{player_name}</div>'
            f'<div style="font-size: 0.9rem; color: rgba(255, 255, 255, 0.7);">Position: {clean_position}</div>'
            f'<div style="font-size: 0.9rem; color: white; font-weight: 700;">Score: {prospect_score:.2f}</div>'
            f'</div>'
        )

        # Close flex and card divs
        html_parts.append('</div></div>')

    # Close container div
    html_parts.append('</div>')

    return '\n'.join(html_parts)

def get_score_color(score: float, max_score: float, min_score: float) -> str:
    """Calculate color for prospect score on a red-to-blue gradient scale"""
    score_percentage = (score - min_score) / (max_score - min_score) if max_score != min_score else 0
    r = int(220 * score_percentage + 65 * (1 - score_percentage))  # Red component
    b = int(65 * score_percentage + 220 * (1 - score_percentage))  # Blue component
    g = 20  # Keep green low for vibrant colors
    return f"#{r:02x}{g:02x}{b:02x}"

def get_rank_color(rank: int, total_ranks: int = 100) -> str:
    """Calculate color for rank number on a red-to-blue gradient scale"""
    # Convert rank to a score percentage (rank 1 = 100%, rank 100 = 0%)
    rank_percentage = (total_ranks - rank) / (total_ranks - 1)
    r = int(220 * rank_percentage + 65 * (1 - rank_percentage))  # Red component
    b = int(65 * rank_percentage + 220 * (1 - rank_percentage))  # Blue component
    g = 20  # Keep green low for vibrant colors
    return f"#{r:02x}{g:02x}{b:02x}"

def render_prospect_preview(prospect, rank: int, team_prospects=None, player_id_cache=None, global_max_score=None, global_min_score=None):
    """Render a single prospect preview card with enhanced styling and animations"""
    # Ensure we have valid team information
    team_name = str(prospect.get('mlb_team', prospect.get('team', 'Unknown')))
    if pd.isna(team_name) or team_name == 'Unknown':
        if "Shaw" in str(prospect.get('player_name', '')):
            team_name = "Pittsburgh Pirates"

    # Get team colors and logo
    team_colors = MLB_TEAM_COLORS.get(team_name, {'primary': '#1a1c23', 'secondary': '#2d2f36', 'accent': '#FFFFFF'})
    team_id = MLB_TEAM_IDS.get(team_name, '')
    logo_url = f"https://www.mlbstatic.com/team-logos/team-cap-on-dark/{team_id}.svg" if team_id else ""

    # Check if this is a team card (has '#' in player_name)
    is_team_card = '#' in str(prospect.get('player_name', ''))

    if is_team_card:
        # Get GM name
        gm_name = GM_MAPPING.get(team_name, 'Unknown')

        # Team card styling
        st.markdown(f"""
            <div class="prospect-card" style="
                background: linear-gradient(135deg, {team_colors['primary']} 0%, {team_colors['secondary']} 100%);
                border-radius: 10px;
                padding: 1.5rem;
                margin: 1rem 0;
                position: relative;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                <div style="
                    position: absolute;
                    left: -10px;
                    top: -10px;
                    width: 40px;
                    height: 40px;
                    background: {team_colors['primary']};
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-weight: bold;
                    border: 2px solid {team_colors['secondary']};
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);">#{rank}</div>
                {f'<img src="{logo_url}" style="position: absolute; right: 20px; top: 50%; transform: translateY(-50%); width: 120px; height: 120px; opacity: 1; z-index: 1;" alt="Team Logo">' if logo_url else ''}
                <div class="prospect-content" style="position: relative; z-index: 2;">
                    <div style="flex-grow: 1;">
                        <div style="
                            font-size: 1.2rem;
                            font-weight: 600;
                            color: white;
                            margin-bottom: 0.25rem;
                            ">{prospect['player_name']}</div>
                        <div style="
                            font-size: 0.9rem;
                            color: rgba(255, 255, 255, 0.8);
                            ">
                            <span style="font-weight: 700;">Score: {prospect['prospect_score']:.2f}</span>
                            <div style="margin-top: 0.5rem; font-size: 0.9rem; color: rgba(255,255,255,0.7);">
                                GM: {gm_name}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    else:
        # Individual player card styling remains the same
        headshot_html = get_player_headshot_html(prospect['player_name'], player_id_cache)
        st.markdown(f"""
            <div class="prospect-card" style="
                background: linear-gradient(135deg, {team_colors['primary']}80 0%, {team_colors['secondary']}80 100%);
                border-radius: 10px;
                padding: 1.5rem;
                margin: 1rem 0;
                position: relative;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                <div style="
                    position: absolute;
                    left: -10px;
                    top: -10px;
                    width: 40px;
                    height: 40px;
                    background: {team_colors['primary']};
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-weight: bold;
                    border: 2px solid {team_colors['secondary']};
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);">#{rank}</div>
                {f'<img src="{logo_url}" style="position: absolute; right: 10px; top: 50%; transform: translateY(-50%); width: 60px; height: 60px; opacity: 0.15; z-index: 1;" alt="Team Logo">' if logo_url else ''}
                <div class="prospect-content" style="position: relative; z-index: 2;">
                    {headshot_html}
                    <div style="flex-grow: 1;">
                        <div style="
                            font-size: 1.2rem;
                            font-weight: 600;
                            color: white;
                            margin-bottom: 0.25rem;
                            ">{prospect['player_name']}</div>
                        <div style="
                            font-size: 0.9rem;
                            color: rgba(255, 255, 255, 0.8);
                            ">
                            <span>{team_name}</span>
                            <span style="margin: 0 0.5rem;">|</span>
                            <span>{prospect['position']}</span>
                            <span style="margin: 0 0.5rem;">|</span>
                            <span>Score: {prospect['prospect_score']:.2f}</span>
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # Show team prospects in expander if available
    if team_prospects is not None:
        with st.expander("View Team Prospects"):
            prospects_html = get_team_prospects_html(team_prospects, player_id_cache, global_max_score, global_min_score)
            st.markdown(prospects_html, unsafe_allow_html=True)

def normalize_within_groups(df: pd.DataFrame, group_col: str, value_col: str) -> pd.Series:
    """Normalize values within groups to 0-1 range"""
    return df.groupby(group_col)[value_col].transform(lambda x: (x - x.min()) / (x.max() - x.min()))

def create_sunburst_visualization(team_scores: pd.DataFrame, division_mapping: Dict[str, str]):
    """Create the sunburst visualization with league-wide team comparisons"""
    # Add team abbreviations and division info
    team_scores['team_abbrev'] = team_scores['team'].map(TEAM_ABBREVIATIONS)
    team_scores['division'] = team_scores['team'].map(division_mapping)

    # Ensure numeric columns are finite
    team_scores['total_score'] = team_scores['total_score'].fillna(0)
    team_scores['avg_score'] = team_scores['avg_score'].fillna(0)

    # Create division-level aggregates
    division_scores = team_scores.groupby('division').agg({
        'avg_score': 'mean',
        'total_score': 'sum'
    }).reset_index()

    # Create league-level aggregates
    league_total = team_scores['total_score'].sum()
    league_avg = team_scores['avg_score'].mean()

    # Create hierarchical data
    data = [
        {
            'id': 'league',
            'parent': '',
            'label': 'League',
            'value': float(league_total),  # Ensure float type
            'color': 0.5,
            'avg_score': float(league_avg)  # Ensure float type
        }
    ]

    # Add division level
    for _, div in division_scores.iterrows():
        data.append({
            'id': f"div_{div['division']}",
            'parent': 'league',
            'label': div['division'],
            'value': float(div['total_score']),  # Ensure float type
            'color': float(div['avg_score'] / division_scores['avg_score'].max()),  # Normalize color
            'avg_score': float(div['avg_score'])  # Ensure float type
        })

    # Add team level
    for _, team in team_scores.iterrows():
        data.append({
            'id': f"team_{team['team_abbrev']}",
            'parent': f"div_{team['division']}",
            'label': team['team_abbrev'],
            'value': float(team['total_score']),  # Ensure float type
            'color': float(team['avg_score'] / team_scores['avg_score'].max()),  # Normalize color
            'avg_score': float(team['avg_score'])  # Ensure float type
        })

    # Convert to DataFrame
    df = pd.DataFrame(data)

    # Create sunburst chart with fixed scales
    fig = go.Figure(go.Sunburst(
        ids=df['id'],
        labels=df['label'],
        parents=df['parent'],
        values=df['value'],
        branchvalues='total',
        textinfo='label',
        marker=dict(
            colors=df['color'],
            colorscale='RdYlBu_r',
            showscale=True,
            colorbar=dict(
                title=dict(
                    text='Relative Prospect Score',
                    font=dict(color='white', size=12)
                ),
                tickfont=dict(color='white', size=10),
                len=0.6,
                yanchor='top',
                y=1.0,
                xanchor='center',
                x=0.5,
                orientation='h',
                thickness=20,
                bgcolor='rgba(0,0,0,0)'
            )
        ),
        customdata=df[['avg_score']],
        hovertemplate="<b>%{label}</b><br>Total Score: %{value:.1f}<br>Average Score: %{customdata[0]:.2f}<extra></extra>"
    ))

    # Update layout
    fig.update_layout(
        title=dict(
            text='Prospect System Hierarchy',
            font=dict(color='white', size=24),
            x=0.5,
            xanchor='center',
            y=0.98
        ),
        width=None,
        height=700,
        font=dict(color='white'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=50, l=10, r=10, b=150, pad=0),
        autosize=True
    )

    return fig

def render_top_100_header(ranked_prospects: pd.DataFrame, player_id_cache: Dict[str, str], global_max_score: float, global_min_score: float):
    """Render the animated TOP 100 header and scrollable list"""
    st.markdown("""
        <style>
        @keyframes gradientText {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        @keyframes glow {
            0% { text-shadow: 0 0 20px rgba(255, 77, 77, 0.5), 0 0 40px rgba(65, 105, 225, 0.3); }
            50% { text-shadow: 0 0 40px rgba(255, 77, 77, 0.8), 0 0 60px rgba(65, 105, 225, 0.5); }
            100% { text-shadow: 0 0 20px rgba(255, 77, 77, 0.5), 0 0 40px rgba(65, 105, 225, 0.3); }
        }
        .top-100-title {
            font-size: 5rem;
            font-weight: 800;
            background: linear-gradient(90deg, 
                #ff4d4d 0%, 
                #4169E1 50%, 
                #ff4d4d 100%);
            background-size: 200% auto;
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: 
                gradientText 3s linear infinite,
                glow 2s ease-in-out infinite;
            margin: 2rem 0;
            padding: 0;
            text-align: center;
        }
        </style>

        <h1 class="top-100-title">ABL TOP 100</h1>
    """, unsafe_allow_html=True)

    # Get top 100 prospects sorted by Rank
    top_100 = ranked_prospects.dropna(subset=['Rank']).sort_values('Rank').head(100)

    # Display prospects in order
    for idx, prospect in enumerate(top_100.itertuples(), 1):
        # Get team colors and logo
        team_colors = MLB_TEAM_COLORS.get(prospect.team,
                                       {'primary': '#1a1c23', 'secondary': '#2df36', 'accent': '#FFFFFF'})
        team_id = MLB_TEAM_IDS.get(prospect.team, '')
        logo_url = f"https://www.mlbstatic.com/team-logos/team-cap-on-dark/{team_id}.svg" if team_id else ""

        # Get headshot HTML
        headshot_html = get_player_headshot_html(prospect.player_name, player_id_cache)

        st.markdown(f"""
            <div class="prospect-card" style="
                background: linear-gradient(135deg, {team_colors['primary']}80 0%, {team_colors['secondary']}80 100%);
                border-radius: 8px;
                padding: 0.75rem;
                margin: 0.5rem 0;
                position: relative;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                transition: transform 0.3s ease, box-shadow 0.3s ease;"
                class="hover-card">
                <style>
                .hover-card {
                    transform: translateY(0);
                    transition: transform 0.3s ease, box-shadow 0.3s ease;
                }
                .hover-card:hover {
                    transform: translateY(-3px);
                    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                }
                </style>
                <div style="
                    position: absolute;
                    left: -8px;
                    top: -8px;
                    width: 30px;
                    height: 30px;
                    background: {team_colors['primary']};
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-size: 0.9rem;
                    font-weight: bold;
                    border: 2px solid {team_colors['secondary']};
                    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);">#{idx}</div>
                {f'<img src="{logo_url}" style="position: absolute; right: 8px; top: 50%; transform: translateY(-50%); width: 40px; height: 40px; opacity: 0.15; z-index: 1;" alt="Team Logo">' if logo_url else ''}
                <div class="prospect-content" style="position: relative; z-index: 2; display: flex; align-items: center; gap: 0.75rem;">
                    {headshot_html}
                    <div style="flex-grow: 1;">
                        <div style="font-size: 0.95rem; font-weight: 600; color: white;">{prospect.player_name}</div>
                        <div style="font-size: 0.8rem; color: rgba(255,255,255,0.8); margin-top: 0.1rem;">
                            {prospect.team} | {str(prospect.position).replace('position ', '').split(',')[0].strip()} | Score: {prospect.prospect_score:.2f}
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr style='margin: 2rem 0;'>", unsafe_allow_html=True)

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
    "Seattle Mariners":"SEA",
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
    "Cardinals": "STL","Saint Louis Cardinals": "STL",
    "St Louis Cardinals": "STL",
    "St. Louis Cardinals": "STL",
    "Arizona Diamondbacks": "ARI",
    "Colorado Rockies": "COL",
    "Los Angeles Dodgers": "LAD",
    "San Diego Padres": "SD",
    "San Francisco Giants": "SF"
}

# Add MLB team ID mapping after TEAM_ABBREVIATIONS
MLB_TEAM_IDS = {
    "Los Angeles Angels": "108",
    "Arizona Diamondbacks": "109",
    "Baltimore Orioles": "110",
    "Boston Red Sox": "111",
    "Chicago Cubs": "112",
    "Cincinnati Reds": "113",
    "Cleveland Guardians": "114",
    "Colorado Rockies": "115",
    "Detroit Tigers": "116",
    "Houston Astros": "117",
    "Kansas City Royals": "118",
    "Los Angeles Dodgers": "119",
    "Washington Nationals": "120",
    "New York Mets": "121",
    "Oakland Athletics": "133",
    "Athletics": "133",  # Add alternative name
    "Pittsburgh Pirates": "134",
    "San Diego Padres": "135",
    "Seattle Mariners": "136",
    "San Francisco Giants": "137",
    "St. Louis Cardinals": "138",
    "Saint Louis Cardinals": "138",
    "St Louis Cardinals": "138",
    "Cardinals": "138",  # Add all variations of Cardinals name
    "Tampa Bay Rays": "139",
    "Texas Rangers": "140",
    "Toronto Blue Jays": "141",
    "Minnesota Twins": "142",
    "Philadelphia Phillies": "143",
    "Atlanta Braves": "144",
    "Chicago White Sox": "145",
    "Miami Marlins": "146",
    "New York Yankees": "147",
    "Milwaukee Brewers": "158"
}

MLB_TEAM_COLORS = {
    "Arizona Diamondbacks": {
        'primary': '#A71930',  # Sedona Red
        'secondary': '#E3D4AD',  # Sonoran Sand
        'accent': '#000000'  # Black
    },
    "Atlanta Braves": {
        'primary': '#CE1141',  # Scarlet
        'secondary': '#13274F',  # Navy Blue
        'accent': '#EAAA00'  # Yellow
    },
    "Baltimore Orioles": {
        'primary': '#DF4601',  # Orange
        'secondary': '#000000',  # Black
        'accent': '#FFFFFF'  # White
    },
    "Boston Red Sox": {
        'primary': '#BD3039',  # Red
        'secondary': '#0C2340',  # Blue
        'accent': '#FFFFFF'  # White
    },
    "Chicago Cubs": {
        'primary': '#0E3386',  # Blue
        'secondary': '#CC3433',  # Red
        'accent': '#FFFFFF'  # White
    },
    "Chicago White Sox": {
        'primary': '#27251F',  # Black
        'secondary': '#C4CED4',  # Silver
        'accent': '#FFFFFF'  # White
    },
    "Cincinnati Reds": {
        'primary': '#C6011F',  # Red
        'secondary': '#000000',  # Black
        'accent': '#FFFFFF'  # White
    },
    "Cleveland Guardians": {
        'primary': '#0C2340',  # Navy Blue
        'secondary': '#E31937',  # Red
        'accent': '#FFFFFF'  # White
    },
    "Colorado Rockies": {
        'primary': '#33006F',  # Rockies Purple
        'secondary': '#C4CED4',  # Silver
        'accent': '#000000'  # Black
    },
    "Detroit Tigers": {
        'primary': '#0C2340',  # Navy Blue
        'secondary': '#FA4616',  # Orange
        'accent': '#FFFFFF'  # White
    },
    "Houston Astros": {
        'primary': '#002D62',  # Navy Blue
        'secondary': '#EB6E1F',  # Orange
        'accent': '#F4911E'  # Light Orange
    },
    "Kansas City Royals": {
        'primary': '#004687',  # Royal Blue
        'secondary': '#BD9B60',  # Gold
        'accent': '#FFFFFF'  # White
    },
    "Los Angeles Angels": {
        'primary': '#003263',  # Blue
        'secondary': '#BA0021',  # Red
        'accent': '#862633'  # Maroon
    },
    "Los Angeles Dodgers": {
        'primary': '#005A9C',  # Dodger Blue
        'secondary': '#EF3E42',  # Red
        'accent': '#A5ACAF'  # Silver
    },
    "Miami Marlins": {
        'primary': '#00A3E0',  # Miami Blue
        'secondary': '#FF6B00',  # Caliente Red
        'accent': '#000000'  # Midnight Black
    },
    "Milwaukee Brewers": {
        'primary': '#12284B',  # Navy Blue
        'secondary': '#FFC52F',  # Yellow
        'accent': '#FFFFFF'  # White
    },
    "Minnesota Twins": {
        'primary': '#002B5C',  # Twins Navy Blue
        'secondary': '#D31145',  # Scarlet Red
        'accent': '#B4975A'  # Kasota Gold
    },
    "New York Mets": {
        'primary': '#002D72',  # Blue
        'secondary': '#FF5910',  # Orange
        'accent': '#FFFFFF'  # White
    },
    "New York Yankees": {
        'primary': '#003087',  # Blue
        'secondary': '#E4002B',  # Red
        'accent': '#0C2340'  # Navy Blue
    },
    "Athletics": {
        'primary': '#003831',  # Green
        'secondary': '#EFB21E',  # Gold
        'accent': '#A2AAAD'  # Gray
    },
    "Philadelphia Phillies": {
        'primary': '#E81828',  # Red
        'secondary': '#002D72',  # Blue
        'accent': '#FFFFFF'  # White
    },
    "Pittsburgh Pirates": {
        'primary': '#27251F',  # Black
        'secondary': '#FDB827',  # Yellow
        'accent': '#FFFFFF'  # White
    },
    "San Diego Padres": {
        'primary': '#2F241D',  # Brown
        'secondary': '#FFC425',  # Gold
        'accent': '#FFFFFF'  # White
    },
    "San Francisco Giants": {
        'primary': '#FD5A1E',  # Orange
        'secondary': '#27251F',  # Black
        'accent': '#EFD19F'  # Beige
    },
    "Seattle Mariners": {
        'primary': '#0C2C56',  # Navy Blue
        'secondary': '#005C5C',  # Northwest Green
        'accent': '#C4CED4'  # Silver
    },
    "Saint Louis Cardinals": {
        'primary':'#C41E3A',  # Red
        'secondary': '#0C2340',  # Navy Blue
        'accent': '#FEDB00'  # Yellow
    },
    "Tampa Bay Rays": {
        'primary': '#092C5C',  # Navy Blue
        'secondary': '#8FBCE6',  # Columbia Blue
        'accent': '#F5D130'  # Yellow
    },
    "Texas Rangers": {
        'primary': '#003278',  # Blue
        'secondary': '#C0111F',  # Red
        'accent': '#FFFFFF'  # White
    },
    "Toronto Blue Jays": {
        'primary': '#134A8E',  # Blue
        'secondary': '#1D2D5C',  # Navy Blue
        'accent': '#E8291C'  # Red
    },
    "Washington Nationals": {
        'primary': '#AB0003',  # Red
        'secondary': '#14225A',  # Navy Blue
        'accent': '#FFFFFF'  # White
    }
}