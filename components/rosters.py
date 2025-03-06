import streamlit as st
import pandas as pd
import plotly.express as px

def calculate_prospect_score(minors_players: pd.DataFrame) -> float:
    """Calculate team's prospect system score based on rankings"""
    if len(minors_players) == 0:
        return 0.0

    # Lower ranking is better, so we invert the score
    max_rank = 535  # Maximum ranking in the CSV
    scores = [(max_rank - player.get('Ranking', max_rank)) / max_rank for player in minors_players.to_dict('records')]
    return sum(scores)

def render(roster_data: pd.DataFrame):
    """Render roster information section"""
    st.header("Team Rosters")

    # Load prospect rankings
    prospect_rankings = pd.read_csv("attached_assets/2025 Dynasty Dugout Offseason Rankings - Jan 25 Prospects.csv")

    # Add team filter
    teams = roster_data['team'].unique()
    selected_team = st.selectbox("Select Team", teams)

    # Filter data by selected team
    team_roster = roster_data[roster_data['team'] == selected_team]

    # Split roster by status
    active_roster = team_roster[team_roster['status'].isin(['Active', 'Reserve'])]
    minors_roster = team_roster[team_roster['status'] == 'Minors']

    # Display active/reserve roster
    st.subheader("Active Roster")
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
        hide_index=True,
        column_order=["player_name", "position", "mlb_team", "status", "salary"]
    )

    # Display roster statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Active Players", len(active_roster))
    with col2:
        st.metric("Minor Leaguers", len(minors_roster))
    with col3:
        st.metric("Total Salary", f"${active_roster['salary'].sum():,.2f}")
    with col4:
        st.metric("Positions", len(active_roster['position'].unique()))

    # Process and display minors roster with rankings
    st.subheader("Minor League System")

    # Merge minors roster with prospect rankings
    minors_with_rankings = pd.merge(
        minors_roster,
        prospect_rankings,
        left_on='player_name',
        right_on='Player',
        how='left'
    )

    # Calculate system score
    system_score = calculate_prospect_score(minors_with_rankings)
    st.metric("Minor League System Score", f"{system_score:.2f}")

    # Display minors roster with rankings
    if not minors_with_rankings.empty:
        st.dataframe(
            minors_with_rankings,
            column_config={
                "player_name": "Player",
                "position": "Position",
                "mlb_team": "MLB Team",
                "Ranking": st.column_config.NumberColumn(
                    "Prospect Ranking",
                    format="%d"
                ),
                "Tier": "Tier"
            },
            hide_index=True,
            column_order=["player_name", "position", "mlb_team", "Ranking", "Tier"]
        )

        # Show prospect tier distribution
        st.subheader("Prospect Tier Distribution")
        tier_counts = minors_with_rankings['Tier'].value_counts().sort_index()
        st.bar_chart(tier_counts)
    else:
        st.info("No minor league players found for this team.")

    # Position breakdown
    st.subheader("Position Distribution")
    position_counts = active_roster['position'].value_counts()
    fig = px.pie(
        values=position_counts.values,
        names=position_counts.index,
        title="Position Distribution",
        hole=0.4
    )
    st.plotly_chart(fig, use_container_width=True)