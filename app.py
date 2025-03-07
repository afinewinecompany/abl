import streamlit as st
from components import league_info, rosters, standings, power_rankings, prospects
from api_client import FantraxAPI
from data_processor import DataProcessor

st.set_page_config(
    page_title="ABL Analytics",
    page_icon="⚾",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 1rem 2rem;
        background: linear-gradient(to bottom, #ffffff, #f8f9fa);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background: #ffffff;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .stTabs [data-baseweb="tab"] {
        height: 4rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #1f77b4;
        background: #f8f9fa;
    }
    h1 {
        color: #1f77b4;
        text-align: center;
        padding: 1.5rem;
        margin-bottom: 2rem;
        font-size: 2.5em;
        font-weight: 700;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        background: #ffffff;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .stMetric {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        transition: transform 0.3s ease;
    }
    .stMetric:hover {
        transform: translateY(-2px);
    }
    .debug-section {
        margin-top: 2rem;
        padding: 1rem;
        border-radius: 10px;
        background: #f8f9fa;
    }
    .stDataFrame {
        background: #ffffff;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    .css-1d391kg {  /* Streamlit containers */
        background: #ffffff;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.title("⚾ ABL Analytics")

    # Initialize API client
    api_client = FantraxAPI()
    data_processor = DataProcessor()

    # Add refresh button in sidebar with baseball emoji
    with st.sidebar:
        st.markdown("### League Controls")
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.experimental_rerun()

        st.markdown("---")
        st.markdown("### About")
        st.markdown("Advanced Baseball League (ABL) analytics platform for real-time stats and insights.")

    try:
        # Hide API debug output by default
        api_debug = False

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

        # Debug information in collapsible section at bottom
        with st.expander("🔧 Debug Information", expanded=False):
            st.markdown("### API Response Details")
            if st.checkbox("Show API Debug Output", value=False):
                st.json(league_data)
                st.json(roster_data)
                st.json(standings_data)

    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.info("Please try refreshing the page or check your internet connection.")

if __name__ == "__main__":
    main()