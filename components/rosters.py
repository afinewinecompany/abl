import streamlit as st
import pandas as pd
import plotly.express as px

def calculate_prospect_score(ranking: int) -> float:
    """Calculate prospect score based on ranking"""
    if pd.isna(ranking):
        return 0
    # Exponential decay scoring - higher ranked prospects worth more
    return 100 * (0.95 ** (ranking - 1))

def render(roster_data: pd.DataFrame):
    """Render roster information section"""
    st.header("Team Rosters")

    # Read prospect rankings
    prospect_rankings = pd.read_csv("attached_assets/2025 Dynasty Dugout Offseason Rankings - Jan 25 Prospects.csv")

    # Clean up prospect data
    prospect_rankings['Player'] = prospect_rankings['Player'].str.strip()
    prospect_rankings['Team'] = prospect_rankings['Team'].str.strip()

    # Calculate prospect scores
    prospect_rankings['prospect_score'] = prospect_rankings['Ranking'].apply(calculate_prospect_score)

    # Add team filter
    teams = roster_data['team'].unique()
    selected_team = st.selectbox("Select Team", teams)

    # Filter data by selected team
    team_roster = roster_data[roster_data['team'] == selected_team]

    # Split roster by status
    active_roster = team_roster[team_roster['status'].str.upper() == 'ACTIVE']
    minors_roster = team_roster[team_roster['status'].str.upper() == 'MINORS']
    # Reserve roster includes IL, DTD, and other non-Active, non-Minors players
    reserve_roster = team_roster[
        ~team_roster['status'].str.upper().isin(['ACTIVE', 'MINORS'])
    ]

    # Display roster statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Players", len(team_roster))
    with col2:
        st.metric("Active Players", len(active_roster))
    with col3:
        st.metric("Total Salary", f"${team_roster['salary'].sum():,.2f}")
    with col4:
        st.metric("Positions", len(team_roster['position'].unique()))

    # Active Roster Section
    st.subheader("📋 Active Roster")
    st.dataframe(
        active_roster,
        column_config={
            "player_name": "Player",
            "position": "Position",
            "mlb_team": "MLB Team",
            "status": "Status",
            "salary": st.column_config.NumberColumn(
                "Salary",
                format="$%.2f"
            )
        },
        hide_index=True
    )

    # Reserve Roster Section
    if not reserve_roster.empty:
        st.subheader("🔄 Reserve Roster")
        st.dataframe(
            reserve_roster,
            column_config={
                "player_name": "Player",
                "position": "Position",
                "mlb_team": "MLB Team",
                "status": "Status",
                "salary": st.column_config.NumberColumn(
                    "Salary",
                    format="$%.2f"
                )
            },
            hide_index=True
        )

    # Minors/Prospects Section
    if not minors_roster.empty:
        st.subheader("⭐ Minor League Prospects")

        # Debug: Show sample names from both datasets
        if st.checkbox("Debug Name Matching", value=False):
            st.write("Sample Minor League Players:", minors_roster['player_name'].head())
            st.write("Sample Prospect Rankings:", prospect_rankings['Player'].head())

        # Merge prospect rankings with minors roster
        minors_with_rankings = pd.merge(
            minors_roster,
            prospect_rankings[['Player', 'Ranking', 'Tier', 'prospect_score']],
            left_on='player_name',
            right_on='Player',
            how='left'
        )

        st.dataframe(
            minors_with_rankings,
            column_config={
                "player_name": "Player",
                "position": "Position",
                "mlb_team": "MLB Team",
                "Ranking": st.column_config.NumberColumn(
                    "Prospect Ranking",
                    help="Overall prospect ranking"
                ),
                "Tier": "Prospect Tier",
                "prospect_score": st.column_config.NumberColumn(
                    "Prospect Score",
                    format="%.1f",
                    help="Calculated prospect value score"
                )
            },
            hide_index=True
        )

    # Position breakdown
    st.subheader("Position Distribution")
    position_counts = team_roster['position'].value_counts()
    st.bar_chart(position_counts)

    # Prospect Power Rankings
    st.subheader("🌟 Prospect Power Rankings")

    # Calculate team prospect scores
    team_prospect_scores = []
    for team in teams:
        team_minors = roster_data[
            (roster_data['team'] == team) & 
            (roster_data['status'].str.upper() == 'MINORS')
        ]

        team_prospects = pd.merge(
            team_minors,
            prospect_rankings[['Player', 'prospect_score']],
            left_on='player_name',
            right_on='Player',
            how='left'
        )

        total_score = team_prospects['prospect_score'].sum()
        avg_score = team_prospects['prospect_score'].mean()
        ranked_prospects = len(team_prospects[team_prospects['prospect_score'] > 0])

        team_prospect_scores.append({
            'team': team,
            'total_score': total_score,
            'average_score': avg_score,
            'ranked_prospects': ranked_prospects
        })

    prospect_rankings_df = pd.DataFrame(team_prospect_scores)
    prospect_rankings_df = prospect_rankings_df.sort_values('total_score', ascending=False)
    prospect_rankings_df = prospect_rankings_df.reset_index(drop=True)
    prospect_rankings_df.index = prospect_rankings_df.index + 1

    st.dataframe(
        prospect_rankings_df,
        column_config={
            "team": "Team",
            "total_score": st.column_config.NumberColumn(
                "Total Prospect Score",
                format="%.1f"
            ),
            "average_score": st.column_config.NumberColumn(
                "Average Prospect Score",
                format="%.1f"
            ),
            "ranked_prospects": "Number of Ranked Prospects"
        },
        hide_index=False
    )

    # Visualize prospect rankings
    fig = px.bar(
        prospect_rankings_df,
        x='team',
        y='total_score',
        title='Team Prospect Power Rankings',
        labels={'team': 'Team', 'total_score': 'Total Prospect Score'},
        color='total_score',
        color_continuous_scale='viridis'
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)