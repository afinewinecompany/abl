from pathlib import Path
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
        # Handle non-string input, including NA/None values
        if pd.isna(name):
            return ""
        if not isinstance(name, str):
            return str(name).strip()

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
        # Read and process prospect scores with error handling
        prospect_import = pd.read_csv("attached_assets/ABL-Import.csv", na_values=['NA', ''], keep_default_na=True)
        prospect_import['Name'] = prospect_import['Name'].fillna('').astype(str).apply(normalize_name)

        # Get all minor league players (ensure no duplicates)
        minors_players = roster_data[roster_data['status'].str.upper() == 'MINORS'].copy()
        minors_players['clean_name'] = minors_players['player_name'].fillna('').astype(str).apply(normalize_name)
        minors_players = minors_players.drop_duplicates(subset=['clean_name'], keep='first')

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
        ranked_prospects = ranked_prospects.drop_duplicates(subset=['clean_name'], keep='first')
        ranked_prospects.rename(columns={'MLB Team': 'mlb_team'}, inplace=True)

        # Render top 100 header and scrollable list
        render_top_100_header(ranked_prospects, player_id_cache)

        # Calculate team rankings
        team_scores = ranked_prospects.groupby('team').agg({
            'prospect_score': ['sum', 'mean']
        }).reset_index()

        team_scores.columns = ['team', 'total_score', 'avg_score']
        team_scores = team_scores.sort_values('total_score', ascending=False)
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
                    'prospect_score': row['total_score'],
                    'mlb_team': row['team']
                }, idx + 1, team_prospects, player_id_cache)

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
            }, i + 4, team_prospects, player_id_cache)

        # Add handbook viewer at the bottom
        render_handbook_viewer()

    except Exception as e:
        st.error(f"Error processing prospect data: {str(e)}")
        return

def render_handbook_viewer():
    """Render the PDF handbook viewer section"""
    try:
        import streamlit as st
        from streamlit_pdf_viewer import pdf_viewer
        from pathlib import Path

        st.markdown("""
            <style>
            .handbook-section {
                margin-top: 3rem;
                padding: 2rem;
                background: rgba(26, 28, 35, 0.3);
                border-radius: 10px;
                text-align: center;
                position: relative;
                z-index: 1;
            }
            .handbook-content {
                margin-top: 2rem;
                padding: 2rem;
                background: rgba(26, 28, 35, 0.5);
                border-radius: 8px;
                overflow: hidden;
                position: relative;
                z-index: 1;
            }
            .pdf-viewer {
                width: 100%;
                min-height: 800px;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
            }
            </style>
            <div class="handbook-section">
                <h2 style="color: white; margin-bottom: 1rem;">📚 2024 ABL Prospect Handbook</h2>
                <p style="color: rgba(255,255,255,0.8); margin-bottom: 2rem;">
                    Dive deep into our comprehensive prospect analysis with the official handbook.
                    Use the page controls below to navigate through the handbook.
                </p>
            </div>
        """, unsafe_allow_html=True)

        pdf_path = Path("attached_assets/2024 ABL Prospect Handbook - Google Docs.pdf")

        if not pdf_path.exists():
            st.warning("Handbook PDF file not found. Please ensure the file is present in the assets folder.")
            return

        try:
            with st.container():
                st.markdown('<div class="handbook-content">', unsafe_allow_html=True)
                pdf_viewer(
                    pdf_path.as_posix(),
                    width=800,
                    height=800,
                    show_navigation=True,
                    show_toolbar=True
                )
                st.markdown('</div>', unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error displaying PDF: {str(e)}")
            st.info("Please make sure the PDF file is not corrupted and try again.")

    except ImportError as e:
        st.error(f"Required libraries not found: {str(e)}")
        st.info("Installing required packages...")
        try:
            from replit import packaging
            packaging.install('streamlit-pdf-viewer')
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Failed to install required packages: {str(e)}")

def create_player_id_cache(mlb_ids_df: pd.DataFrame) -> Dict[str, str]:
    """Create a cache of normalized player names to MLBAMID"""
    cache = {}
    for _, row in mlb_ids_df.iterrows():
        try:
            if pd.isna(row['Last']) or pd.isna(row['First']):
                continue
            name = normalize_name(f"{row['First']} {row['Last']}")
            if name and not pd.isna(row['MLBAMID']):
                cache[name] = str(row['MLBAMID'])
        except Exception:
            continue
    return cache

def get_headshot_url(mlbam_id: str) -> str:
    """Generate MLB headshot URL from player ID"""
    # Try both URL patterns for maximum compatibility
    base_url = "https://img.mlbstatic.com/mlb-photos"
    return f"{base_url}/image/upload/v1/people/{mlbam_id}/headshot/67/current"

def get_player_headshot_html(player_name: str, player_id_cache: Dict[str, str]) -> str:
    """Get player headshot HTML if available"""
    try:
        search_name = normalize_name(player_name)
        mlbam_id = player_id_cache.get(search_name)

        if mlbam_id:
            # Add multiple fallback URLs and error handling
            return f"""
                <div style="width: 60px; height: 60px; min-width: 60px; border-radius: 50%; overflow: hidden; margin-right: 1rem; background-color: #1a1c23;">
                    <img src="{get_headshot_url(mlbam_id)}"
                         style="width: 100%; height: 100%; object-fit: cover;"
                         onerror="this.onerror=null; this.src='https://img.mlbstatic.com/mlb-photos/image/upload/v1/people/{mlbam_id}/headshot/current';"
                         alt="{player_name} headshot">
                </div>
            """
        else:
            # Split name and get initials in First Last order
            name_parts = player_name.split(',')  # Split on comma
            if len(name_parts) == 2:
                last_name, first_name = name_parts
                initials = f"{first_name.strip()[0]}{last_name.strip()[0]}"
            else:
                # Fallback to regular split for names without comma
                parts = player_name.split()
                initials = ''.join(part[0].upper() for part in parts[:2])

            return f"""
                <div style="width: 60px; height: 60px; min-width: 60px; border-radius: 50%; overflow: hidden; margin-right: 1rem; background-color: #1a1c23; display: flex; align-items: center; justify-content: center;">
                    <div style="color: white; font-size: 20px; font-weight: bold;">{initials}</div>
                </div>
            """
    except Exception as e:
        st.error(f"Error generating headshot HTML for {player_name}: {str(e)}")
        return ""

def get_team_prospects_html(prospects_df: pd.DataFrame, player_id_cache: Dict[str, str]) -> str:
    """Generate HTML for team prospects list"""
    avg_score = prospects_df['prospect_score'].mean()
    prospects_html = [
        f'<div style="font-size: 0.9rem; color: #fafafa; margin-bottom: 0.5rem;">Team Average Score: {avg_score:.2f}</div>'
    ]

    for _, prospect in prospects_df.iterrows():
        # Get headshot HTML for the prospect using the cache
        headshot_html = get_player_headshot_html(prospect['player_name'], player_id_cache)

        # Use flexbox layout for all prospect entries
        prospects_html.append(
            f'<div style="padding: 0.75rem; margin: 0.25rem 0; background: rgba(26, 28, 35, 0.3); border-radius: 4px;">'
            f'<div style="display: flex; align-items: center; gap: 1rem;">'
            f'{headshot_html}'
            f'<div style="flex-grow: 1;">'
            f'<div style="font-size: 0.95rem; color: #fafafa; font-weight: 500;">{prospect["player_name"]}</div>'
            f'<div style="font-size: 0.85rem; color: rgba(250, 250, 250, 0.7);">'
            f'{prospect["position"]} | Score: {prospect["prospect_score"]:.1f}</div>'
            f'</div>'
            f'</div>'
            f'</div>'
        )

    return "".join(prospects_html)

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

def render_prospect_preview(prospect, rank: int, team_prospects=None, player_id_cache=None):
    """Render a single prospect preview card with native Streamlit expander"""
    color = get_color_for_rank(rank)
    team_id = MLB_TEAM_IDS.get(prospect.get('mlb_team', ''), '')
    logo_url = f"https://www.mlbstatic.com/team-logos/team-cap-on-dark/{team_id}.svg" if team_id else ""

    background_style = f"""
        background-image: url('{logo_url}');
        background-size: contain;
        background-repeat: no-repeat;
        background-position: right;
        background-color: rgba(26, 28, 35, 0.5);
    """ if logo_url else "background-color: rgba(26, 28, 35, 0.5);"

    st.markdown(
        f'<div style="padding: 0.75rem; border-radius: 8px; margin: 0.25rem 0; border-left: 3px solid {color}; {background_style}">',
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
            prospects_html = get_team_prospects_html(team_prospects, player_id_cache)
            st.markdown(prospects_html, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


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

def render_top_100_header(ranked_prospects: pd.DataFrame, player_id_cache: Dict[str, str]):
    """Render the animated TOP 100 header and scrollable list"""
    # Get top 100 prospects sorted by score
    top_100 = ranked_prospects.nlargest(100, 'prospect_score')

    # Display all top 100 prospects
    st.markdown("### 🌟 Top 100 Prospects")

    # Display prospects in order
    for idx, prospect in enumerate(top_100.itertuples(), 1):
        # Get color based on rank (normalize to 100 ranks)
        rank_color = get_color_for_rank(idx, 100)

        # Get headshot HTML for the prospect using the cache
        headshot_html = get_player_headshot_html(prospect.player_name, player_id_cache)

        prospect_card = f'<div class="prospect-card fade-in" style="border-left: 3px solid {rank_color};"><div style="display: flex; align-items: center; gap: 1rem;"><div style="font-size: 1.5rem; font-weight: 700; color: {rank_color}; min-width: 2rem; text-align: center;">#{idx}</div>{headshot_html}<div style="flex-grow: 1;"><div style="font-size: 1rem; color: white; font-weight: 500;">{prospect.player_name}</div><div style="font-size: 0.9rem; color: rgba(255,255,255,0.7);">{prospect.team} | {prospect.position}</div><div style="font-size: 0.8rem; color: rgba(255,255,255,0.6);">Score: {prospect.prospect_score:.2f}</div></div></div></div>'
        st.markdown(prospect_card, unsafe_allow_html=True)

    st.markdown("<hr style='margin: 2rem 0;'>", unsafe_allow_html=True)