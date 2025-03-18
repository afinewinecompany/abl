import streamlit as st
import pandas as pd

def render():
    """Render the handbook page with team information"""
    st.header("📚 League Handbook")
    
    # Team Manager Data
    team_managers = {
        "Pittsburgh Pirates": "Duke",
        "Toronto Blue Jays": "Gary",
        "Milwaukee Brewers": "Zack",
        "San Francisco Giants": "Rourke",
        "Los Angeles Angels": "Cal",
        "Oakland Athletics": "Dylan",
        "Arizona Diamondbacks": "Carpy",
        "Tampa Bay Rays": "Kevin",
        "Baltimore Orioles": "Steve",
        "Detroit Tigers": "John",
        "Miami Marlins": "Other Frank",
        "Cincinnati Reds": "Linny",
        "New York Mets": "Matt",
        "Los Angeles Dodgers": "Joe",
        "Chicago Cubs": "Frank",
        "Philadelphia Phillies": "Adam",
        "New York Yankees": "Gary",
        "Texas Rangers": "Sam",
        "Atlanta Braves": "Aidan",
        "Colorado Rockies": "Allen",
        "Kansas City Royals": "Brendan",
        "San Diego Padres": "Greg",
        "Chicago White Sox": "Tom",
        "Washington Nationals": "Jordan & Cim",
        "Houston Astros": "Evan",
        "St. Louis Cardinals": "Jeff",
        "Boston Red Sox": "Don",
        "Minnesota Twins": "Tyler",
        "Cleveland Guardians": "Mark",
        "Seattle Mariners": "Seth"
    }

    # Create columns for division display
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("American League")
        
        # AL East
        st.markdown("#### AL East")
        for team in ["New York Yankees", "Boston Red Sox", "Toronto Blue Jays", "Baltimore Orioles", "Tampa Bay Rays"]:
            if team in team_managers:
                st.markdown(f"""
                <div style="
                    padding: 10px;
                    border-radius: 5px;
                    margin: 5px 0;
                    background-color: #1a1c23;
                    border-left: 4px solid #FF6B6B;
                ">
                    <strong>{team}</strong><br>
                    <span style="color: #888;">General Manager: {team_managers[team]}</span>
                </div>
                """, unsafe_allow_html=True)

        # AL Central
        st.markdown("#### AL Central")
        for team in ["Cleveland Guardians", "Chicago White Sox", "Detroit Tigers", "Kansas City Royals", "Minnesota Twins"]:
            if team in team_managers:
                st.markdown(f"""
                <div style="
                    padding: 10px;
                    border-radius: 5px;
                    margin: 5px 0;
                    background-color: #1a1c23;
                    border-left: 4px solid #4ECDC4;
                ">
                    <strong>{team}</strong><br>
                    <span style="color: #888;">General Manager: {team_managers[team]}</span>
                </div>
                """, unsafe_allow_html=True)

        # AL West
        st.markdown("#### AL West")
        for team in ["Houston Astros", "Los Angeles Angels", "Oakland Athletics", "Seattle Mariners", "Texas Rangers"]:
            if team in team_managers:
                st.markdown(f"""
                <div style="
                    padding: 10px;
                    border-radius: 5px;
                    margin: 5px 0;
                    background-color: #1a1c23;
                    border-left: 4px solid #95A5A6;
                ">
                    <strong>{team}</strong><br>
                    <span style="color: #888;">General Manager: {team_managers[team]}</span>
                </div>
                """, unsafe_allow_html=True)

    with col2:
        st.subheader("National League")
        
        # NL East
        st.markdown("#### NL East")
        for team in ["Atlanta Braves", "Miami Marlins", "New York Mets", "Philadelphia Phillies", "Washington Nationals"]:
            if team in team_managers:
                st.markdown(f"""
                <div style="
                    padding: 10px;
                    border-radius: 5px;
                    margin: 5px 0;
                    background-color: #1a1c23;
                    border-left: 4px solid #F39C12;
                ">
                    <strong>{team}</strong><br>
                    <span style="color: #888;">General Manager: {team_managers[team]}</span>
                </div>
                """, unsafe_allow_html=True)

        # NL Central
        st.markdown("#### NL Central")
        for team in ["Chicago Cubs", "Cincinnati Reds", "Milwaukee Brewers", "Pittsburgh Pirates", "St. Louis Cardinals"]:
            if team in team_managers:
                st.markdown(f"""
                <div style="
                    padding: 10px;
                    border-radius: 5px;
                    margin: 5px 0;
                    background-color: #1a1c23;
                    border-left: 4px solid #3498DB;
                ">
                    <strong>{team}</strong><br>
                    <span style="color: #888;">General Manager: {team_managers[team]}</span>
                </div>
                """, unsafe_allow_html=True)

        # NL West
        st.markdown("#### NL West")
        for team in ["Arizona Diamondbacks", "Colorado Rockies", "Los Angeles Dodgers", "San Diego Padres", "San Francisco Giants"]:
            if team in team_managers:
                st.markdown(f"""
                <div style="
                    padding: 10px;
                    border-radius: 5px;
                    margin: 5px 0;
                    background-color: #1a1c23;
                    border-left: 4px solid #2ECC71;
                ">
                    <strong>{team}</strong><br>
                    <span style="color: #888;">General Manager: {team_managers[team]}</span>
                </div>
                """, unsafe_allow_html=True)
