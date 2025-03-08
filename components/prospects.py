import streamlit as st
import pandas as pd
import plotly.express as px
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

def calculate_prospect_score(ranking: int) -> float:
    """Calculate prospect score based on ranking"""
    if pd.isna(ranking):
        return 0
    return 100 * (0.95 ** (ranking - 1))

def render_prospect_preview(prospect, color):
    """Render a single prospect preview card"""
    rank_color = "#00ff88" if pd.notna(prospect['Ranking']) else "#888"
    return f"""
    <div style="
        padding: 0.5rem;
        background-color: #1a1c23;
        border-radius: 8px;
        margin: 0.25rem 0;
        border-left: 3px solid {color};
        transition: all 0.3s ease;
        cursor: pointer;
        transform-origin: center;
    "
    onmouseover="this.style.transform='scale(1.02)';
                 this.style.boxShadow='0 8px 16px rgba(0,0,0,0.2)';
                 this.style.borderLeftWidth='6px';
                 this.style.backgroundColor='#22242c';"
    onmouseout="this.style.transform='scale(1)';
                this.style.boxShadow='none';
                this.style.borderLeftWidth='3px';
                this.style.backgroundColor='#1a1c23';"
    >
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-weight: bold;">{prospect['player_name']}</div>
                <div style="font-size: 0.8rem; color: #888;">
                    {prospect['position']} | Score: {prospect['prospect_score']:.1f}
                </div>
            </div>
            <div style="text-align: right;">
                <div style="color: {rank_color};">
                    {f"#{int(prospect['Ranking'])}" if pd.notna(prospect['Ranking']) else "Unranked"}
                </div>
            </div>
        </div>
    </div>
    """

def render_team_card(team, team_rank, score, ranked_prospects, division, color, top_3_prospects, all_prospects):
    """Render a team card with prospect preview and expandable full list"""
    preview_html = "".join([render_prospect_preview(prospect, color) 
                           for _, prospect in top_3_prospects.iterrows()])

    # Prepare all prospects HTML for the expander
    all_prospects_html = ""
    if not all_prospects.empty:
        for _, prospect in all_prospects.iterrows():
            rank_color = "#00ff88" if pd.notna(prospect['Ranking']) else "#888"
            all_prospects_html += f"""
            <div style="
                padding: 0.75rem;
                background-color: #1a1c23;
                border-radius: 8px;
                margin: 0.5rem 0;
                border-left: 4px solid {color};
                transition: all 0.3s ease;
                cursor: pointer;
                transform-origin: center;
            "
            onmouseover="this.style.transform='scale(1.02)';
                        this.style.boxShadow='0 8px 16px rgba(0,0,0,0.2)';
                        this.style.borderLeftWidth='6px';
                        this.style.backgroundColor='#22242c';"
            onmouseout="this.style.transform='scale(1)';
                       this.style.boxShadow='none';
                       this.style.borderLeftWidth='4px';
                       this.style.backgroundColor='#1a1c23';"
            >
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-weight: bold; font-size: 1.1rem;">{prospect['player_name']}</div>
                        <div style="font-size: 0.9rem; color: #888;">
                            {prospect['position']} | {prospect['mlb_team']} | Score: {prospect['prospect_score']:.1f}
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-weight: bold; color: {rank_color};">
                            {f"Rank #{int(prospect['Ranking'])}" if pd.notna(prospect['Ranking']) else "Unranked"}
                        </div>
                        <div style="font-size: 0.8rem; color: #888;">
                            {f"Tier {prospect['Tier']}" if pd.notna(prospect['Tier']) else ""}
                            {f" | ETA: {prospect['ETA']}" if pd.notna(prospect['ETA']) else ""}
                        </div>
                    </div>
                </div>
            </div>
            """

    return {
        'header': f"""
        <div style="
            padding: 1rem;
            background-color: #1a1c23;
            border-radius: 10px;
            border-left: 5px solid {color};
            margin: 0.5rem 0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
            cursor: pointer;
            transform-origin: center;
        "
        onmouseover="this.style.transform='scale(1.01)';
                     this.style.boxShadow='0 8px 16px rgba(0,0,0,0.2)';
                     this.style.borderLeftWidth='8px';"
        onmouseout="this.style.transform='scale(1)';
                    this.style.boxShadow='0 4px 6px rgba(0,0,0,0.1)';
                    this.style.borderLeftWidth='5px';"
        >
            <div style="display: flex; justify-content: space-between; margin-bottom: 1rem;">
                <div>
                    <div style="font-weight: bold; font-size: 1.2rem;">#{team_rank} {team}</div>
                    <div style="font-size: 0.8rem; color: #888;">{division}</div>
                </div>
                <div style="text-align: right;">
                    <div style="font-weight: bold; font-size: 1.2rem;">{score:.1f}</div>
                    <div style="font-size: 0.8rem; color: #888;">{int(ranked_prospects)} Ranked</div>
                </div>
            </div>
            <div style="margin-top: 0.5rem;">
                <div style="font-size: 0.9rem; color: #888; margin-bottom: 0.5rem;">Top Prospects:</div>
                {preview_html}
            </div>
        </div>
        """,
        'all_prospects': all_prospects_html
    }

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

        # Read and process prospect rankings
        prospect_rankings = pd.read_csv("attached_assets/2025 Dynasty Dugout Offseason Rankings - Jan 25 Prospects.csv")
        prospect_rankings['Player'] = prospect_rankings['Player'].str.strip()
        prospect_rankings['prospect_score'] = prospect_rankings['Ranking'].apply(calculate_prospect_score)

        # Get all minor league players
        minors_players = roster_data[roster_data['status'].str.upper() == 'MINORS'].copy()
        minors_players['clean_name'] = minors_players['player_name'].apply(normalize_name)

        # Merge with rankings
        ranked_prospects = pd.merge(
            minors_players,
            prospect_rankings[['Player', 'Ranking', 'Tier', 'prospect_score', 'Position', 'ETA']],
            left_on='clean_name',
            right_on='Player',
            how='left'
        )

        # Calculate team rankings
        team_scores = ranked_prospects.groupby('team').agg({
            'prospect_score': ['sum', 'mean'],
            'Ranking': lambda x: x.notna().sum()  # Count of ranked prospects
        }).reset_index()
        team_scores.columns = ['team', 'total_score', 'avg_score', 'ranked_prospects']
        team_scores = team_scores.sort_values('total_score', ascending=False)
        team_scores = team_scores.reset_index(drop=True)
        team_scores.index = team_scores.index + 1

        # Display top 3 teams
        st.subheader("🏆 Top Prospect Systems")
        col1, col2, col3 = st.columns(3)

        # Display top 3 teams in cards
        for idx, (col, (rank, row)) in enumerate(zip([col1, col2, col3], team_scores.head(3).iterrows())):
            with col:
                division = division_mapping.get(row['team'], "Unknown")
                color = division_colors.get(division, "#00ff88")

                # Get team's prospects
                team_prospects = ranked_prospects[ranked_prospects['team'] == row['team']].sort_values(
                    'prospect_score', ascending=False
                )
                top_3_prospects = team_prospects.head(3)

                # Render team card
                card = render_team_card(
                    row['team'],
                    rank,
                    row['total_score'],
                    row['ranked_prospects'],
                    division,
                    color,
                    top_3_prospects,
                    team_prospects
                )

                # Display card header with preview
                st.markdown(card['header'], unsafe_allow_html=True)

                # Add expander for full prospect list
                with st.expander("View All Prospects"):
                    st.markdown(card['all_prospects'], unsafe_allow_html=True)

        # Show remaining teams
        st.markdown("### Remaining Teams")

        # Display teams 4-30 in single column
        remaining_teams = team_scores.iloc[3:]
        for rank, row in remaining_teams.iterrows():
            division = division_mapping.get(row['team'], "Unknown")
            color = division_colors.get(division, "#00ff88")

            # Get team's prospects
            team_prospects = ranked_prospects[ranked_prospects['team'] == row['team']].sort_values(
                'prospect_score', ascending=False
            )
            top_3_prospects = team_prospects.head(3)

            # Render team card
            card = render_team_card(
                row['team'],
                rank + 3, # Adjust rank for remaining teams
                row['total_score'],
                row['ranked_prospects'],
                division,
                color,
                top_3_prospects,
                team_prospects
            )

            # Display card header with preview
            st.markdown(card['header'], unsafe_allow_html=True)

            # Add expander for full prospect list
            with st.expander("View All Prospects"):
                st.markdown(card['all_prospects'], unsafe_allow_html=True)

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

        # Tier Distribution
        with st.expander("📊 League-wide Tier Distribution"):
            tier_dist = ranked_prospects[ranked_prospects['Tier'].notna()].groupby(['team', 'Tier']).size().unstack(fill_value=0)

            fig = px.bar(
                tier_dist,
                title='Prospect Tier Distribution by Team',
                labels={'value': 'Number of Prospects', 'team': 'Team', 'variable': 'Tier'},
                barmode='group'
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"An error occurred while processing prospect data: {str(e)}")