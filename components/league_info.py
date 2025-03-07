import streamlit as st
from typing import Dict

def render(league_data: Dict):
    """Render league information section"""
    st.header("League Information")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("League Name", league_data['name'])
        st.metric("Season", league_data['season'])

    with col2:
        st.metric("Number of Teams", league_data['teams'])
        st.metric("Sport", league_data['sport'])

    with col3:
        st.metric("Draft Type", league_data['scoring_type'])
        st.metric("Scoring Period", league_data['scoring_period'])

    st.divider()