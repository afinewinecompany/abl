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
        # Normalize name for lookup
        search_name = normalize_name(player_name)
        mlbam_id = player_id_cache.get(search_name)

        if mlbam_id:
            # Get all possible URLs
            urls = [
                f"https://img.mlbstatic.com/mlb-photos/image/upload/c_fill,g_auto/w_180/v1/people/{mlbam_id}/headshot/milb/current",
                f"https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/{mlbam_id}/headshot/67/current",
                f"https://img.mlbstatic.com/mlb-photos/image/upload/w_120,h_180,g_auto,c_fill/v1/people/{mlbam_id}/headshot/milb/current",
                f"https://img.mlbstatic.com/mlb-photos/image/upload/w_120,h_180,g_auto,c_fill/v1/people/{mlbam_id}/headshot/67/current",
                f"https://img.mlbstatic.com/mlb-images/image/upload/q_auto/mlb/{mlbam_id}",
                f"https://img.mlbstatic.com/mlb-photos/image/upload/w_213,d_people:generic:headshot:silo:current.png,q_auto:best,f_auto/v1/people/{mlbam_id}/headshot/67/current"
            ]

            # Build the onerror chain to try all URLs
            onerror_chain = '; '.join([
                f"this.src='{url}'" for url in urls[1:]
            ])

            return f"""
                <div style="width: 60px; height: 60px; min-width: 60px; border-radius: 50%; overflow: hidden; margin-right: 1rem; background-color: #1a1c23;">
                    <img src="{urls[0]}"
                         style="width: 100%; height: 100%; object-fit: cover;"
                         onerror="this.onerror=null; {onerror_chain};"
                         alt="{player_name} headshot">
                </div>
            """
        else:
            # Generate initials for players without photos
            parts = player_name.split(',')  # Split on comma
            if len(parts) == 2:
                last_name, first_name = parts
                initials = f"{first_name.strip()[0]}{last_name.strip()[0]}"
            else:
                # Fallback to regular split for names without comma
                parts = player_name.split()
                initials = ''.join(part[0].upper() for part in parts[:2] if part)

            # Create initials circle
            return f"""
                <div style="width: 60px; height: 60px; min-width: 60px; border-radius: 50%; overflow: hidden; margin-right: 1rem; background-color: #1a1c23; display: flex; align-items: center; justify-content: center;">
                    <div style="color: white; font-size: 20px; font-weight: bold;">{initials}</div>
                </div>
            """
    except Exception as e:
        st.warning(f"Error generating headshot HTML for {player_name}: {str(e)}")
        return ""

def get_team_prospects_html(prospects_df: pd.DataFrame, player_id_cache: Dict[str, str]) -> str:
    """Generate HTML for team prospects list"""
    # Calculate average score
    avg_score = prospects_df['prospect_score'].mean()

    # Start with container div
    html_parts = [
        '<div style="background: rgba(26, 28, 35, 0.3); border-radius: 8px; padding: 1rem;">',
        f'<div style="font-size: 0.9rem; color: #fafafa; margin-bottom: 1rem;">'
        f'Team Average Score: {avg_score:.2f}'
        '</div>'
    ]

    # Add each prospect
    for _, prospect in prospects_df.iterrows():
        search_name = normalize_name(prospect['player_name'])
        mlbam_id = player_id_cache.get(search_name)

        # Start prospect card
        html_parts.append('<div style="padding: 1rem; margin: 0.5rem 0; background: rgba(26, 28, 35, 0.5); border-radius: 8px;">')
        html_parts.append('<div style="display: flex; align-items: center;">')

        # Add headshot or initials
        if mlbam_id:
            headshot_url = f"https://img.mlbstatic.com/mlb-photos/image/upload/w_213,d_people:generic:headshot:silo:current.png,q_auto:best,f_auto/v1/people/{mlbam_id}/headshot/67/current"
            html_parts.append(
                f'<div style="width: 60px; height: 60px; min-width: 60px; border-radius: 50%; overflow: hidden; margin-right: 1rem; background-color: #1a1c23;">'
                f'<img src="{headshot_url}" style="width: 100%; height: 100%; object-fit: cover;" alt="{prospect["player_name"]}">'
                f'</div>'
            )
        else:
            # Generate initials
            parts = prospect['player_name'].split(',')
            if len(parts) == 2:
                last_name, first_name = parts
                initials = f"{first_name.strip()[0]}{last_name.strip()[0]}"
            else:
                parts = prospect['player_name'].split()
                initials = ''.join(part[0].upper() for part in parts[:2] if part)

            html_parts.append(
                f'<div style="width: 60px; height: 60px; min-width: 60px; border-radius: 50%; overflow: hidden; margin-right: 1rem; '
                f'background-color: #1a1c23; display: flex; align-items: center; justify-content: center;">'
                f'<div style="color: white; font-size: 20px; font-weight: bold;">{initials}</div>'
                f'</div>'
            )

        # Add prospect info
        html_parts.append(
            f'<div style="flex-grow: 1;">'
            f'<div style="font-size: 1rem; color: white; font-weight: 500; margin-bottom: 0.25rem;">{prospect["player_name"]}</div>'
            f'<div style="font-size: 0.9rem; color: rgba(255, 255, 255, 0.7);">{prospect["position"]} | Score: {prospect["prospect_score"]:.1f}</div>'
            f'</div>'
        )

        # Close flex and card divs
        html_parts.append('</div></div>')

    # Close container div
    html_parts.append('</div>')

    # Join all parts with newlines for better formatting
    return '\n'.join(html_parts)

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
    """Render a single prospect preview card with enhanced styling and animations"""
    color = get_color_for_rank(rank)
    team_id = MLB_TEAM_IDS.get(prospect.get('mlb_team', ''), '')
    logo_url = f"https://www.mlbstatic.com/team-logos/team-cap-on-dark/{team_id}.svg" if team_id else ""

    # Get team colors from the comprehensive mapping
    team_colors = MLB_TEAM_COLORS.get(str(prospect.get('mlb_team', '')), 
                                    {'primary': '#1a1c23', 'secondary': '#2d2f36', 'accent': '#FFFFFF'})

    st.markdown(f"""
        <style>
        @keyframes slideInUp {{
            from {{
                transform: translateY(50px);
                opacity: 0;
            }}
            to {{
                transform: translateY(0);
                opacity: 1;
            }}
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}
        @keyframes pulse {{
            0% {{ transform: scale(1); }}
            50% {{ transform: scale(1.02); }}
            100% {{ transform: scale(1); }}
        }}
        @keyframes shimmer {{
            0% {{ background-position: -200% center; }}
            100% {{ background-position: 200% center; }}
        }}
        .team-card-{rank} {{
            padding: 2rem;
            border-radius: 16px;
            margin: 1rem 0;
            background: linear-gradient(135deg, 
                {team_colors['primary']} 0%, 
                {team_colors['secondary']} 70%, 
                {team_colors['accent']} 100%);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
            position: relative;
            overflow: hidden;
            animation: slideInUp 0.6s ease-out {rank * 0.1}s both;
            transition: all 0.3s ease;
        }}
        .team-card-{rank}:hover {{
            transform: translateY(-5px);
            box-shadow: 0 12px 48px rgba(0, 0, 0, 0.2);
        }}
        .team-logo-{rank} {{
            position: absolute;
            right: -30px;
            top: 50%;
            transform: translateY(-50%);
            width: 220px;
            height: 220px;
            opacity: 0.12;
            animation: fadeIn 1s ease-out {rank * 0.2}s both;
            filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.2));
        }}
        .rank-badge-{rank} {{
            position: absolute;
            left: -15px;
            top: -15px;
            background: {color};
            color: white;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 1.4rem;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
            animation: fadeIn 0.8s ease-out {rank * 0.15}s both;
            border: 2px solid rgba(255, 255, 255, 0.2);
        }}
        .prospect-content-{rank} {{
            position: relative;
            z-index: 1;
        }}
        .prospect-header-{rank} {{
            font-weight: 800;
            font-size: 1.8rem;
            margin-bottom: 0.8rem;
            color: white;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}
        .prospect-subheader-{rank} {{
            font-size: 1.2rem;
            color: rgba(255, 255, 255, 0.9);
            margin-bottom: 0.4rem;
        }}
        .prospect-score-{rank} {{
            font-size: 1rem;
            color: rgba(255, 255, 255, 0.8);
            background: rgba(0, 0, 0, 0.2);
            padding: 0.4rem 0.8rem;
            border-radius: 20px;
            display: inline-block;
            margin-top: 0.5rem;
        }}
        .prospect-container {{
            background: rgba(0, 0, 0, 0.2);
            border-radius: 12px;
            padding: 1rem;
            margin-top: 1rem;
            animation: fadeInRight 0.5s ease-out;
        }}
        @keyframes fadeInRight {{
            from {{
                opacity: 0;
                transform: translateX(-20px);
            }}
            to {{
                opacity: 1;
                transform: translateX(0);
            }}
        }}
        </style>
    """, unsafe_allow_html=True)

    st.markdown(
        f'<div class="team-card-{rank}">', unsafe_allow_html=True
    )

    # Add rank badge
    st.markdown(
        f'<div class="rank-badge-{rank}">#{rank}</div>', unsafe_allow_html=True
    )

    if logo_url:
        st.markdown(
            f'<img src="{logo_url}" class="team-logo-{rank}" alt="Team Logo">', 
            unsafe_allow_html=True
        )

    # Display team header with enhanced styling
    st.markdown(
        f"""
        <div class="prospect-content-{rank}">
            <div class="prospect-header-{rank}">
                {prospect['player_name']}
            </div>
            <div class="prospect-subheader-{rank}">
                {prospect['position']}
            </div>
            <div class="prospect-score-{rank}">
                Total Score: {prospect['prospect_score']:.1f}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Show prospects in expander with enhanced animation
    if team_prospects is not None:
        with st.expander("View Team Prospects"):
            prospects_html = get_team_prospects_html(team_prospects, player_id_cache)
            st.markdown(f"""
                <div class="prospect-container">
                    {prospects_html}
                </div>
            """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

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
            border-radius:10px;
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
        .slide-up {animation: slideUp 0.6s ease forwards;
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

        prospect_card = f'<div class="prospect-card fade-in" style="border-left: 3px solid {rank_color};"><div style="display: flex; align-items: center; gap: 1rem;"><div style="font-size: 1.5rem; font-weight: 700; color: {rank_color}; min-width: 2rem; text-align: center;">#{idx}</div>{headshot_html}<div style="flex-grow: 1;"><div style="font-size: 1rem; color: white; font-weight:500;">{prospect.player_name}</div><div style="font-size: 0.9rem; color: rgba(255,255,255,0.7);">{prospect.team} | {prospect.position}</div><div style="font-size: 0.8rem; color: rgba(255,255,255,0.6);">Score: {prospect.prospect_score:.2f}</div></div></div></div>'
        st.markdown(prospect_card, unsafe_allow_html=True)

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