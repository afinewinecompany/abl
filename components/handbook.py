
import streamlit as st
import pandas as pd

def render(roster_data: pd.DataFrame):
    """Render handbook section"""
    st.header("📖 League Handbook")
    
    st.markdown("""
    ### Table of Contents
    1. League Structure
    2. Player Eligibility
    3. Scoring System
    4. Trading Rules
    """)

    # League Structure
    st.subheader("1. League Structure")
    st.markdown("""
    - 30 teams divided into 6 divisions
    - American League (AL) and National League (NL) format
    - Regular season followed by playoffs
    """)

    # Player Eligibility
    st.subheader("2. Player Eligibility")
    st.markdown("""
    - Active roster players must be on MLB 40-man rosters
    - Prospects must be under rookie eligibility limits
    - Players can be assigned to active, reserve, or minors status
    """)

    # Scoring System
    st.subheader("3. Scoring System")
    scoring_data = {
        'Action': ['Single', 'Double', 'Triple', 'Home Run', 'RBI', 'Run', 'Walk', 'HBP', 'Stolen Base'],
        'Points': [1, 2, 3, 4, 1, 1, 1, 1, 2]
    }
    st.dataframe(pd.DataFrame(scoring_data))

    # Trading Rules
    st.subheader("4. Trading Rules")
    st.markdown("""
    - All trades must include at least one major league player
    - No trade vetoes unless collusion is suspected
    - Trade deadline follows MLB trade deadline
    """)
