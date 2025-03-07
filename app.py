import streamlit as st
from components import league_info, rosters, standings, power_rankings, prospects
from api_client import FantraxAPI
from data_processor import DataProcessor

st.set_page_config(
    page_title="ABL Analytics",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for dark mode with neon effects
st.markdown("""
<style>
    .main {
        padding: 1rem 2rem;
        background: #0e1117;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background: #1a1c23;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 0 10px rgba(0, 255, 136, 0.2);
    }
    .stTabs [data-baseweb="tab"] {
        height: 4rem;
        font-weight: 600;
        transition: all 0.3s ease;
        color: #fafafa;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #00ff88;
        text-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
    }
    h1 {
        color: #00ff88;
        text-align: center;
        padding: 1.5rem;
        margin-bottom: 2rem;
        font-size: 2.5em;
        font-weight: 700;
        text-shadow: 0 0 20px rgba(0, 255, 136, 0.5);
        background: #1a1c23;
        border-radius: 10px;
        box-shadow: 0 0 15px rgba(0, 255, 136, 0.2);
    }
    .stMetric {
        background-color: #1a1c23;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 0 15px rgba(0, 255, 136, 0.2);
        transition: all 0.3s ease;
    }
    .stMetric:hover {
        transform: translateY(-2px);
        box-shadow: 0 0 20px rgba(0, 255, 136, 0.3);
    }
    .stDataFrame {
        background: #1a1c23;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 0 15px rgba(0, 255, 136, 0.2);
    }
    .css-1d391kg {  /* Streamlit containers */
        background: #1a1c23;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 0 15px rgba(0, 255, 136, 0.2);
        margin-bottom: 2rem;
    }
    /* Custom scrollbar for dark mode */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    ::-webkit-scrollbar-track {
        background: #0e1117;
    }
    ::-webkit-scrollbar-thumb {
        background: #2e3137;
        border-radius: 5px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #00ff88;
    }
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #1a1c23;
    }
    .css-1p05t8e {
        background-color: #0e1117;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.title("⚾ ABL Analytics")

    # Initialize API client
    api_client = FantraxAPI()
    data_processor = DataProcessor()

    # Streamlined sidebar
    with st.sidebar:
        st.markdown("### 🔄 League Controls")
        if st.button("Refresh Data", use_container_width=True):
            st.experimental_rerun()

        st.markdown("---")
        st.markdown("""
        ### About ABL Analytics
        Advanced Baseball League (ABL) analytics platform providing comprehensive insights and analysis.
        """)

    try:
        # Fetch all required data
        league_data = api_client.get_league_info()
        roster_data = api_client.get_team_rosters()
        standings_data = api_client.get_standings()
        player_ids = api_client.get_player_ids()

        # Process data
        processed_league_data = data_processor.process_league_info(league_data)
        processed_roster_data = data_processor.process_rosters(roster_data, player_ids)
        processed_standings_data = data_processor.process_standings(standings_data)

        # Create tabs for different sections
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🏠 League Info",
            "👥 Team Rosters",
            "📊 Standings",
            "🏆 Power Rankings",
            "⭐ Prospects"
        ])

        with tab1:
            league_info.render(processed_league_data)

        with tab2:
            rosters.render(processed_roster_data)

        with tab3:
            standings.render(processed_standings_data)

        with tab4:
            power_rankings.render(processed_standings_data)

        with tab5:
            prospects.render(processed_roster_data)

    except Exception as e:
        st.error(f"An error occurred while loading data. Please try refreshing.")

if __name__ == "__main__":
    main()