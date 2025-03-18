import sys
import traceback
import logging
import streamlit as st

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Must be the first Streamlit command
try:
    logger.debug("Setting up page config...")
    st.set_page_config(
        page_title="ABL Analytics",
        page_icon="⚾",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    logger.debug("Page config set successfully")
except Exception as e:
    logger.error(f"Error setting page config: {str(e)}")
    logger.error(traceback.format_exc())
    raise

try:
    logger.debug("Importing components...")
    from components import league_info, rosters, standings, power_rankings, prospects, projected_rankings
    from api_client import FantraxAPI
    from data_processor import DataProcessor
    logger.debug("Components imported successfully")
except Exception as e:
    logger.error(f"Error importing components: {str(e)}")
    logger.error(traceback.format_exc())
    raise

def main():
    try:
        logger.debug("Starting main application...")
        st.title("⚾ ABL Analytics")

        # Initialize API client
        logger.debug("Initializing API client...")
        api_client = FantraxAPI()
        data_processor = DataProcessor()
        logger.debug("API client initialized")

        # Streamlined sidebar
        try:
            logger.debug("Setting up sidebar...")
            with st.sidebar:
                st.markdown("### 🔄 League Controls")
                if st.button("Refresh Data", use_container_width=True):
                    st.experimental_rerun()

                st.markdown("---")
                st.markdown("""
                ### About ABL Analytics
                Advanced Baseball League (ABL) analytics platform providing comprehensive insights and analysis.
                """)
            logger.debug("Sidebar setup complete")
        except Exception as e:
            logger.error(f"Error setting up sidebar: {str(e)}")
            logger.error(traceback.format_exc())
            st.error("Error setting up sidebar - some features may be unavailable")

        try:
            logger.debug("Fetching API data...")
            # Fetch all required data
            league_data = api_client.get_league_info()
            roster_data = api_client.get_team_rosters()
            standings_data = api_client.get_standings()
            player_ids = api_client.get_player_ids()
            logger.debug("API data fetched successfully")

            logger.debug("Processing data...")
            # Process data
            processed_league_data = data_processor.process_league_info(league_data)
            processed_roster_data = data_processor.process_rosters(roster_data, player_ids)
            processed_standings_data = data_processor.process_standings(standings_data)
            logger.debug("Data processing complete")

            logger.debug("Creating tabs...")
            # Create tabs for different sections
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "🏠 League Info",
                "👥 Team Rosters",
                "🏆 Power Rankings",
                "📚 Handbook",
                "📈 Projected Rankings"
            ])
            logger.debug("Tabs created successfully")

            logger.debug("Rendering content in tabs...")
            with tab1:
                league_info.render(processed_league_data)

            with tab2:
                rosters.render(processed_roster_data)

            with tab3:
                power_rankings.render(processed_standings_data)

            with tab4:
                prospects.render(processed_roster_data)

            with tab5:
                projected_rankings.render(processed_roster_data)
            logger.debug("All tabs rendered successfully")

        except Exception as e:
            logger.error(f"An error occurred in main application flow: {str(e)}")
            logger.error(traceback.format_exc())
            st.error("An error occurred while loading data. The application will continue with limited functionality.")

    except Exception as e:
        logger.error(f"Critical error in main function: {str(e)}")
        logger.error(traceback.format_exc())
        st.error("A critical error occurred. Please try refreshing the page.")

if __name__ == "__main__":
    main()