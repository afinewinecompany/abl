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

def render(roster_data: pd.DataFrame):
    """Render roster information section"""
    st.header("Team Rosters")

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
    display_columns = ['player_name', 'position', 'mlb_team', 'status', 'salary']
    st.dataframe(
        active_roster[display_columns],
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
            reserve_roster[display_columns],
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
        st.subheader("⭐ Minor League Players")
        st.dataframe(
            minors_roster[display_columns],
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

    # Position breakdown
    st.subheader("Position Distribution")
    position_counts = team_roster['position'].value_counts()
    st.bar_chart(position_counts)