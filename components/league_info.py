import streamlit as st
from typing import Dict

def render(league_data: Dict):
    """Render league information section"""
    st.header("League Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("League Name", league_data['name'])
        st.metric("Season", league_data['season'])
        
    with col2:
        st.metric("Number of Teams", league_data['teams'])
        st.metric("Scoring Type", league_data['scoring_type'])
    
    st.divider()
