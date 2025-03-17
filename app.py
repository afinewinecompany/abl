import streamlit as st
from components import league_info, rosters, standings, power_rankings, prospects, projected_rankings
from api_client import FantraxAPI
from data_processor import DataProcessor

st.set_page_config(
    page_title="ABL Analytics",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def main():
    st.title("⚾ ABL Analytics")

    # Initialize session state for league ID
    if 'league_id' not in st.session_state:
        st.session_state.league_id = 'grx2lginm1v4p5jd'  # Default league ID

    # League ID input
    new_league_id = st.text_input(
        "Enter League ID",
        value=st.session_state.league_id,
        help="Enter your Fantrax league ID to load league-specific data"
    )

    # Update league ID if changed
    if new_league_id != st.session_state.league_id:
        st.session_state.league_id = new_league_id
        st.rerun()

    try:
        # Initialize API client and data processor
        api_client = FantraxAPI(league_id=st.session_state.league_id)
        data_processor = DataProcessor()

        # Create tabs
        tabs = st.tabs([
            "🏠 League Info",
            "👥 Team Rosters",
            "🏆 Power Rankings",
            "📈 Projected Rankings"
        ])

        with st.spinner('Loading data...'):
            # Fetch and process league data
            league_data = api_client.get_league_info()
            processed_league_data = data_processor.process_league_info(league_data)

            # Fetch and process roster data
            roster_data = api_client.get_team_rosters()
            player_ids = api_client.get_player_ids()
            processed_roster_data = data_processor.process_rosters(roster_data, player_ids)

            # Fetch and process standings data
            standings_data = api_client.get_standings()
            processed_standings_data = data_processor.process_standings(standings_data)

            # Render each tab
            with tabs[0]:
                league_info.render(processed_league_data)

            with tabs[1]:
                rosters.render(processed_roster_data)

            with tabs[2]:
                power_rankings.render(processed_standings_data)

            with tabs[3]:
                projected_rankings.render(processed_roster_data)

    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        if st.button("Reset to Default League"):
            st.session_state.league_id = 'grx2lginm1v4p5jd'
            st.rerun()

if __name__ == "__main__":
    main()