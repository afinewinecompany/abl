import streamlit as st
import pandas as pd

def render(roster_data: pd.DataFrame):
    """Render roster information section"""
    st.header("Team Rosters")
    
    # Add team filter
    teams = roster_data['team'].unique()
    selected_team = st.selectbox("Select Team", teams)
    
    # Filter data by selected team
    team_roster = roster_data[roster_data['team'] == selected_team]
    
    # Display roster in an interactive table
    st.dataframe(
        team_roster,
        column_config={
            "player_name": "Player",
            "position": "Position",
            "team_mlb": "MLB Team",
            "status": "Status"
        },
        hide_index=True
    )
    
    # Display roster statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Players", len(team_roster))
    with col2:
        st.metric("Active Players", len(team_roster[team_roster['status'] == 'Active']))
    with col3:
        st.metric("Positions", len(team_roster['position'].unique()))
