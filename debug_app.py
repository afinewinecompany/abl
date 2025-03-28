import streamlit as st
import os
import traceback
from api_client import FantraxAPI
from utils import fetch_api_data
from components import matchups

def main():
    try:
        st.title("⚾ Debug Test App")
        
        # Test fetching data
        try:
            data = fetch_api_data()
            if data:
                st.success("Data fetched successfully!")
                st.write(f"Keys in data: {list(data.keys())}")
                
                # Check for matchups data
                if 'matchups_data' in data and data['matchups_data']:
                    st.success(f"Matchups data found: {len(data['matchups_data'])} matchups")
                    
                    # Try rendering matchups component
                    try:
                        st.header("Matchups Component Test")
                        matchups.render(data['matchups_data'])
                        st.success("Matchups component rendered successfully")
                    except Exception as e:
                        st.error(f"Error rendering matchups component: {str(e)}")
                        st.code(traceback.format_exc())
                else:
                    st.warning("No matchups data found")
                    
                    # Try direct API call
                    try:
                        st.subheader("Trying direct API call")
                        api = FantraxAPI()
                        matchup_data = api.get_selenium_matchups()
                        if matchup_data:
                            st.success(f"Direct API call successful: {len(matchup_data)} matchups")
                            matchups.render(matchup_data)
                        else:
                            st.error("Direct API call returned no data")
                    except Exception as e:
                        st.error(f"Error in direct API call: {str(e)}")
                        st.code(traceback.format_exc())
            else:
                st.error("fetch_api_data returned None")
        except Exception as e:
            st.error(f"Error fetching data: {str(e)}")
            st.code(traceback.format_exc())
    
    except Exception as e:
        st.error(f"Critical error: {str(e)}")
        st.code(traceback.format_exc())

if __name__ == "__main__":
    main()