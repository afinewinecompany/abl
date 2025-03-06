import streamlit as st
from components import league_info, rosters, standings, power_rankings
from api_client import FantraxAPI
from data_processor import DataProcessor

st.set_page_config(
    page_title="Fantasy Baseball Analytics",
    page_icon="⚾",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 4rem;
    }
    h1 {
        color: #1f77b4;
        text-align: center;
        padding: 1rem;
        margin-bottom: 2rem;
        border-bottom: 2px solid #f0f2f6;
    }
    .stMetric {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.title("⚾ Fantasy Baseball League Analytics")

    # Initialize API client
    api_client = FantraxAPI()
    data_processor = DataProcessor()

    # Add refresh button in sidebar with baseball emoji
    if st.sidebar.button("🔄 Refresh Data"):
        st.experimental_rerun()

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
        tab1, tab2, tab3, tab4 = st.tabs([
            "🏠 League Info",
            "👥 Team Rosters",
            "📊 Standings",
            "🏆 Power Rankings"
        ])

        with tab1:
            league_info.render(processed_league_data)

        with tab2:
            rosters.render(processed_roster_data)

        with tab3:
            standings.render(processed_standings_data)

        with tab4:
            power_rankings.render(processed_standings_data)

    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.info("Please try refreshing the page or check your internet connection.")

if __name__ == "__main__":
    main()