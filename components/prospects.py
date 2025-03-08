import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Dict

def normalize_name(name: str) -> str:
    """Normalize player name from [last], [first] to [first] [last]"""
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
    # Exponential decay scoring - higher ranked prospects worth more
    return 100 * (0.95 ** (ranking - 1))

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

        # Display top 3 prospect systems
        st.subheader("🏆 Top Prospect Systems")
        col1, col2, col3 = st.columns(3)

        # Display top 3 teams in cards
        for idx, (col, (_, row)) in enumerate(zip([col1, col2, col3], team_scores.head(3).iterrows())):
            with col:
                division = division_mapping.get(row['team'], "Unknown")
                color = division_colors.get(division, "#00ff88")

                # Get team's prospects
                team_prospects = ranked_prospects[ranked_prospects['team'] == row['team']].sort_values(
                    'prospect_score', ascending=False
                )
                top_3_prospects = team_prospects.head(3)

                # Create an expander with preview of top 3 prospects
                with st.expander(f"#{idx + 1} {row['team']}", expanded=False):
                    # Team header and stats
                    st.markdown(f"""
                    <div style="
                        padding: 1rem;
                        background-color: #1a1c23;
                        border-radius: 10px;
                        border-left: 5px solid {color};
                        margin: 0.5rem 0;
                        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    ">
                        <div style="display: flex; justify-content: space-between; margin-top: 0.5rem;">
                            <div>
                                <p style="margin:0; font-size: 0.8rem; color: #888;">System Score</p>
                                <p style="margin:0; font-size: 1.2rem; color: #fafafa;">{row['total_score']:.1f}</p>
                            </div>
                            <div style="text-align: right;">
                                <p style="margin:0; font-size: 0.8rem; color: #888;">Ranked Prospects</p>
                                <p style="margin:0; font-size: 1.2rem; color: #fafafa;">{int(row['ranked_prospects'])}</p>
                            </div>
                        </div>
                        <p style="margin:0.5rem 0 0 0; font-size: 0.8rem; color: #888;">{division}</p>
                    </div>
                    """, unsafe_allow_html=True)

                    # Preview of top 3 prospects (outside expander)
                    st.markdown("##### Top Prospects Preview")
                    for _, prospect in top_3_prospects.iterrows():
                        rank_color = "#00ff88" if pd.notna(prospect['Ranking']) else "#888"
                        st.markdown(f"""
                        <div style="
                            padding: 0.5rem;
                            background-color: #1a1c23;
                            border-radius: 8px;
                            margin: 0.25rem 0;
                            border-left: 3px solid {color};
                        ">
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
                        """, unsafe_allow_html=True)

                    # Full prospect list header
                    st.markdown("##### Complete Prospect List")

                    # Show all team's prospects
                    if not team_prospects.empty:
                        for _, prospect in team_prospects.iterrows():
                            rank_color = "#00ff88" if pd.notna(prospect['Ranking']) else "#888"
                            st.markdown(f"""
                            <div style="
                                padding: 0.75rem;
                                background-color: #1a1c23;
                                border-radius: 8px;
                                margin: 0.5rem 0;
                                border-left: 4px solid {color};
                            ">
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
                            """, unsafe_allow_html=True)
                    else:
                        st.info("No prospects found for this team.")

        # Show remaining teams in single column
        st.markdown("### Complete System Rankings")
        remaining_teams = team_scores.iloc[3:]

        for i, (_, row) in enumerate(remaining_teams.iterrows()):
            division = division_mapping.get(row['team'], "Unknown")
            color = division_colors.get(division, "#00ff88")

            # Get team's prospects
            team_prospects = ranked_prospects[ranked_prospects['team'] == row['team']].sort_values(
                'prospect_score', ascending=False
            )
            top_3_prospects = team_prospects.head(3)

            # Create an expander for each team
            with st.expander(f"#{i + 4} {row['team']}", expanded=False):
                # Team header and stats
                st.markdown(f"""
                <div style="
                    padding: 0.75rem;
                    background-color: #1a1c23;
                    border-radius: 8px;
                    margin: 0.5rem 0;
                    border-left: 4px solid {color};
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-weight: bold;">{row['team']}</div>
                            <div style="font-size: 0.8rem; color: #888;">{division}</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-weight: bold; font-size: 1.2rem;">{row['total_score']:.1f}</div>
                            <div style="font-size: 0.8rem; color: #888;">{int(row['ranked_prospects'])} Ranked</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Preview of top 3 prospects
                st.markdown("##### Top Prospects Preview")
                for _, prospect in top_3_prospects.iterrows():
                    rank_color = "#00ff88" if pd.notna(prospect['Ranking']) else "#888"
                    st.markdown(f"""
                    <div style="
                        padding: 0.5rem;
                        background-color: #1a1c23;
                        border-radius: 8px;
                        margin: 0.25rem 0;
                        border-left: 3px solid {color};
                    ">
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
                    """, unsafe_allow_html=True)

                # Full prospect list header
                st.markdown("##### Complete Prospect List")

                # Show all team's prospects
                if not team_prospects.empty:
                    for _, prospect in team_prospects.iterrows():
                        rank_color = "#00ff88" if pd.notna(prospect['Ranking']) else "#888"
                        st.markdown(f"""
                        <div style="
                            padding: 0.75rem;
                            background-color: #1a1c23;
                            border-radius: 8px;
                            margin: 0.5rem 0;
                            border-left: 4px solid {color};
                        ">
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
                        """, unsafe_allow_html=True)
                else:
                    st.info("No prospects found for this team.")

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