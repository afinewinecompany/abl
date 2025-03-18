import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from typing import Dict
import unicodedata

def render(roster_data: Dict):
    """Main render function for prospects page"""
    st.markdown("## 🌟 Prospect Analysis")

    # Process data
    mlb_ids_df = pd.DataFrame()  # TODO: Replace with actual MLB IDs data
    player_id_cache = create_player_id_cache(mlb_ids_df)

    # Only apply styles and render components when explicitly called
    apply_styles()
    render_handbook_viewer()

    # Process and display prospects
    if roster_data:
        process_and_display_prospects(roster_data, player_id_cache)

def process_and_display_prospects(roster_data: Dict, player_id_cache: Dict[str, str]):
    """Process and display prospect data"""
    try:
        # Load division data
        divisions_df = pd.read_csv("attached_assets/divisions.csv", header=None, names=['division', 'team'])
        division_mapping = dict(zip(divisions_df['team'], divisions_df['division']))

        # Read and process prospect scores
        prospect_import = pd.read_csv("attached_assets/ABL-Import.csv")
        prospect_import['Name'] = prospect_import['Name'].apply(normalize_name)

        # Get all minor league players (ensure no duplicates)
        minors_players = roster_data[roster_data['status'].str.upper() == 'MINORS'].copy()
        minors_players['clean_name'] = minors_players['player_name'].apply(normalize_name)
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
            'prospect_score': ['sum', 'mean']        }).reset_index()

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
    return f"https://img.mlbstatic.com/mlb-photos/image/upload/w_213,d_people:generic:headshot:silo:current.png,q_auto:best,f_auto/v1/people/{mlbam_id}/headshot/67/current"

def get_player_headshot_html(player_name: str, player_id_cache: Dict[str, str]) -> str:
    """Get player headshot HTML if available"""
    try:
        search_name = normalize_name(player_name)
        mlbam_id = player_id_cache.get(search_name)

        if mlbam_id:
            return f"""
                <div style="width: 60px; height: 60px; min-width: 60px; border-radius: 50%; overflow: hidden; margin-right: 1rem; background-color: #1a1c23;">
                    <img src="{get_headshot_url(mlbam_id)}"
                         style="width: 100%; height: 100%; object-fit: cover;"
                         onerror="this.src='data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgdmlld0JveD0iMCAwIDYwIDYwIj48Y2lyY2xlIGN4PSIzMCIgY3k9IjMwIiByPSIzMCIgZmlsbD0iIzFhMWMyMyIvPjx0ZXh0IHg9IjMwIiB5PSIzNSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjIwIiBmaWxsPSIjZmZmZmZmIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj57aW5pdGlhbHN9PC90ZXh0Pjwvc3ZnPg==';"
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
        pass
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

def render_top_100_header(ranked_prospects: pd.DataFrame, player_id_cache: Dict[str, str]):
    """Render the animated TOP 100 header and scrollable list"""
    # CSS for animated header and cards
    st.markdown("""
        <style>
        @keyframes gradient {
            0% {background-position: 0% 50%;}
            50% {background-position: 100% 50%;}
            100% {background-position: 0% 50%;}
        }
        .top-100-header {
            background: linear-gradient(-45deg, #dc143c, #4169e1, #1e90ff, #dc143c);
            background-size: 400% 400%;
            animation: gradient 15s ease infinite;
            color: white;
            padding: 2rem;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .prospect-card {
            opacity: 0;
            transform: translateY(20px);
            animation: fadeInUp 0.6s ease forwards;
            background: rgba(26, 28, 35, 0.3);
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
            transition: all 0.3s ease;
        }
        .prospect-card.visible {
            opacity: 1;
            transform: translateY(0);
        }

        /* Animation Options */
        .fade-in {
            animation: fadeIn 0.6s ease forwards;
        }
        .slide-up {
            animation: slideUp 0.6s ease forwards;
        }
        .slide-in {
            animation: slideIn 0.6s ease forwards;
        }
        .scale-up {
            animation: scaleUp 0.6s ease forwards;
        }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(40px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateX(-40px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }

        @keyframes scaleUp {
            from {
                opacity: 0;
                transform: scale(0.8);
            }
            to {
                opacity: 1;
                transform: scale(1);
            }
        }
        </style>

        <script>
        const observerCallback = (entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    observer.unobserve(entry.target);
                }
            });
        };

        const observerOptions = {
            root: null,
            rootMargin: '0px',
            threshold: 0.1
        };

        document.addEventListener('DOMContentLoaded', function() {
            const observer = new IntersectionObserver(observerCallback, observerOptions);
            document.querySelectorAll('.prospect-card').forEach(card => {
                observer.observe(card);
                card.style.opacity = '0';
            });
        });
        </script>
        <div class="top-100-header">
            <h1 style="margin:0; font-size: 2.5rem; font-weight: 700;">ABL TOP 100</h1>
            <p style="margin:0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.9;">Fantasy Baseball's Elite Prospects</p>
        </div>
    """, unsafe_allow_html=True)

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

def render_handbook_viewer():
    """Render the PDF handbook viewer section with interactive page flip"""
    st.markdown("""
        <style>
        .handbook-section {
            margin-top: 3rem;
            padding: 2rem;
            background: rgba(26, 28, 35, 0.3);
            border-radius: 10px;
            text-align: center;
        }
        .handbook-button {
            display: inline-block;
            padding: 0.8rem 1.5rem;
            background: linear-gradient(-45deg, #dc143c, #4169e1);
            border: none;
            border-radius: 5px;
            color: white;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .handbook-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        }
        .pdf-modal {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 90%;
            height: 90%;
            background: #1a1c23;
            z-index: 1000;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            display: none;
            flex-direction: column;
            align-items: center;
            padding: 2rem;
            visibility: hidden;
            opacity: 0;
            transition: visibility 0s, opacity 0.3s linear;
        }
        .pdf-modal.active {
            visibility: visible;
            opacity: 1;
            display: flex;
        }
        .book-container {
            width: 100%;
            height: calc(100% - 60px);
            position: relative;
            perspective: 1500px;
        }
        .page {
            width: 50%;
            height: 100%;
            position: absolute;
            right: 0;
            transform-origin: left;
            transition: transform 0.6s cubic-bezier(0.645, 0.045, 0.355, 1);
            cursor: pointer;
            background: white;
            padding: 2rem;
            overflow-y: auto;
        }
        .page.flipped {
            transform: rotateY(-180deg);
        }
        .page-content {
            width: 100%;
            height: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
            backface-visibility: hidden;
            font-size: 14px;
            line-height: 1.6;
            white-space: pre-wrap;
        }
        .page-controls {
            position: absolute;
            bottom: 20px;
            left: 0;
            right: 0;
            display: flex;
            justify-content: center;
            gap: 1rem;
            z-index: 1001;
        }
        .page-button {
            background: rgba(255, 255, 255, 0.1);
            border: none;
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .page-button:hover {
            background: rgba(255, 255, 255, 0.2);
        }
        .page-number {
            color: white;
            font-size: 0.9rem;
            margin: 0 1rem;
        }
        </style>
    """, unsafe_allow_html=True)

    # Load and parse PDF content
    import PyPDF2
    import json
    from io import BytesIO

    def get_pdf_content():
        pdf_path = "attached_assets/2024 ABL Prospect Handbook - Google Docs.pdf"
        pdf_text = []
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                for page in range(num_pages):
                    pdf_text.append(pdf_reader.pages[page].extract_text())
        except Exception as e:
            st.error(f"Error loading PDF: {str(e)}")
            return []
        return pdf_text

    pdf_content = get_pdf_content()
    total_pages = len(pdf_content)

    # Convert PDF content to JSON string for JavaScript
    pdf_content_json = json.dumps(pdf_content)

    # Create JavaScript for page flip functionality
    js_code = f"""
    <script>
    // Initialize variables
    let modal;
    let book;
    let currentPage = 0;
    const totalPages = {total_pages};
    const pdfContent = {pdf_content_json};

    // Wait for DOM content to load
    document.addEventListener('DOMContentLoaded', function() {{
        modal = document.querySelector('.pdf-modal');
        book = document.querySelector('.book-container');

        // Initialize event listeners
        initializeEventListeners();
    }});

    function initializeEventListeners() {{
        // Button click handlers
        document.querySelector('.handbook-button').addEventListener('click', openModal);
        document.querySelector('.close-button').addEventListener('click', closeModal);
        document.querySelector('.next-button').addEventListener('click', () => flipPage('next'));
        document.querySelector('.prev-button').addEventListener('click', () => flipPage('prev'));
    }}

    function openModal() {{
        modal.classList.add('active');
        initializeBook();
    }}

    function closeModal() {{
        modal.classList.remove('active');
    }}

    function updatePageNumber() {{
        document.querySelector('.page-number').textContent = `Page ${{currentPage + 1}} of ${{totalPages}}`;
    }}

    function createPage(pageNum) {{
        const page = document.createElement('div');
        page.className = 'page';
        page.innerHTML = `<div class="page-content">${{pdfContent[pageNum]}}</div>`;
        return page;
    }}

    function initializeBook() {{
        // Clear existing pages
        book.innerHTML = '';

        // Create pages
        for(let i = 0; i < totalPages; i++) {{
            book.appendChild(createPage(i));
        }}

        // Reset to first page
        currentPage = 0;
        updatePageNumber();
    }}

    function flipPage(direction) {{
        const pages = document.querySelectorAll('.page');
        if (direction === 'next' && currentPage < totalPages - 1) {{
            pages[currentPage].classList.add('flipped');
            currentPage++;
            updatePageNumber();
        }} else if (direction === 'prev' && currentPage > 0) {{
            pages[currentPage - 1].classList.remove('flipped');
            currentPage--;
            updatePageNumber();
        }}
    }}
    </script>

    <div class="handbook-section">
        <h2 style="color: white; margin-bottom: 1rem;">📚 2024 ABL Prospect Handbook</h2>
        <p style="color: rgba(255,255,255,0.8); margin-bottom:2rem;">
            Dive deep into our comprehensive prospect analysis with the official handbook
        </p>
        <button class="handbook-button">📖 Open Handbook</button>
    </div>

    <div class="pdf-modal">
        <button class="close-button" style="position: absolute; top: 10px; right: 10px; background: #f44336; border: none; color: white; padding: 10px 20px; border-radius: 5px; cursor: pointer;">Close</button>

        <div class="book-container">
            <!-- Pages will be dynamically added here -->
        </div>

        <div class="page-controls">
            <button class="page-button prev-button">← Previous</button>
            <span class="page-number">Page 1 of {total_pages}</span>
            <button class="page-button next-button">Next →</button>
        </div>
    </div>
    """

    st.markdown(js_code, unsafe_allow_html=True)

def apply_styles():
    """Apply custom styles for the prospects page"""
    st.markdown("""
        <style>
        .stApp {
            background: rgba(26, 28, 35, 0.95);
            backdrop-filter: blur(5px);
        }
        #tsparticles {
            position: fixed;
            width: 100%;
            height: 100%;
            top: 0;
            left: 0;
            z-index: -1;
        }
        </style>
        <script src="https://cdn.jsdelivr.net/npm/tsparticles@2.9.3/tsparticles.bundle.min.js"></script>
        <div id="tsparticles"></div>
        <script>
        window.addEventListener('DOMContentLoaded', (event) => {
            tsParticles.load("tsparticles", {
                particles: {
                    number: {
                        value: 20,
                        density: {
                            enable: true,
                            value_area: 800
                        }
                    },
                    color: {
                        value: "#ffffff"
                    },
                    shape: {
                        type: "circle"
                    },
                    opacity: {
                        value: 0.5,
                        random: false
                    },
                    size: {
                        value: 15,
                        random: true
                    },
                    move: {
                        enable: true,
                        speed: 2,
                        direction: "none",
                        random: true,
                        straight: false,
                        outModes: {
                            default: "bounce"
                        },
                        attract: {
                            enable: false,
                            rotateX: 600,
                            rotateY: 1200
                        }
                    },
                    rotate: {
                        value: 0,
                        random: true,
                        direction: "clockwise",
                        animation: {
                            enable: true,
                            speed: 5,
                            sync: false
                        }
                    },
                    backgroundMask: {
                        enable: true,
                        cover: {
                            color: "#1a1c23"
                        }
                    }
                },
                interactivity: {
                    detectsOn: "window",
                    events: {
                        onHover: {
                            enable: true,
                            mode: "repulse"
                        },
                        resize: true
                    },
                    modes: {
                        repulse: {
                            distance: 100,
                            duration: 0.4
                        }
                    }
                }
            });
        });
        </script>
    """, unsafe_allow_html=True)