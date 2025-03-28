import streamlit as st
import pandas as pd
from fantrax_scraper import scrape_fantrax_standings

def render():
    """
    Render the Fantrax standings page
    """
    st.subheader("Fantrax League Standings")
    
    # Add input for league URL with a default value
    league_url = st.text_input(
        "Fantrax League URL or API Endpoint",
        value="https://www.fantrax.com/fxea/general/getStandings?leagueId=grx2lginm1v4p5jd",
        help="Enter the URL of your Fantrax league standings page or direct API endpoint"
    )
    
    # Show explanation of API endpoint vs league URL
    with st.expander("About Fantrax URLs and API Endpoints"):
        st.markdown("""
        You can use either:
        
        1. **API Endpoint URL** (recommended): 
           - Format: `https://www.fantrax.com/fxea/general/getStandings?leagueId=YOUR_LEAGUE_ID`
           - More reliable and returns cleaner data
           - Replace `YOUR_LEAGUE_ID` with your actual league ID
        
        2. **League Standings Page URL**:
           - Format: `https://www.fantrax.com/fantasy/league/YOUR_LEAGUE_ID/standings`
           - The scraper will attempt to extract the league ID and construct the API URL
        """)
        st.info("Your league ID is usually a string like 'grx2lginm1v4p5jd' in the URL of your Fantrax league.")
    
    # Add a fetch button
    if st.button("Fetch Standings", use_container_width=True):
        with st.spinner("Fetching standings data..."):
            try:
                # Call the scraper
                standings_df = scrape_fantrax_standings(league_url)
                
                # Store the results in session state for persistence
                st.session_state.fantrax_standings = standings_df
                st.success("Standings data fetched successfully!")
            except Exception as e:
                st.error(f"Error fetching standings: {str(e)}")
    
    # Display the standings if available
    if 'fantrax_standings' in st.session_state and st.session_state.fantrax_standings is not None:
        try:
            df = st.session_state.fantrax_standings
            
            # Add styling options
            st.write("### Current Standings")
            
            # Format the table with improved styling
            # Add custom CSS to improve the table appearance
            st.markdown("""
            <style>
            .standings-table {
                font-family: Arial, sans-serif;
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }
            .standings-table th {
                background-color: rgba(26, 28, 35, 0.8);
                color: white;
                font-weight: bold;
                text-align: left;
                padding: 12px 8px;
                border-bottom: 2px solid #ff3030;
            }
            .standings-table td {
                padding: 10px 8px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
            .standings-table tr:nth-child(even) {
                background-color: rgba(26, 28, 35, 0.4);
            }
            .standings-table tr:hover {
                background-color: rgba(255, 48, 48, 0.1);
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Convert the dataframe to HTML and style it
            html_table = df.to_html(classes='standings-table', index=False)
            st.markdown(html_table, unsafe_allow_html=True)
            
            # Add download option
            csv = df.to_csv(index=False)
            st.download_button(
                "Download Standings as CSV",
                csv,
                "fantrax_standings.csv",
                "text/csv",
                key='download-csv'
            )
            
            # Add analytics section
            if not df.empty:
                st.write("### Standings Analytics")
                
                # Check if we have columns for wins, losses, ties
                numeric_columns = df.select_dtypes(include=['float64', 'int64']).columns
                if len(numeric_columns) > 0:
                    # Create some basic analytics visualizations
                    st.subheader("Team Performance")
                    selected_stat = st.selectbox(
                        "Select a statistic to visualize", 
                        options=numeric_columns
                    )
                    
                    if selected_stat:
                        # Sort the dataframe by the selected stat
                        sorted_df = df.sort_values(by=selected_stat, ascending=False)
                        
                        # Create a bar chart
                        st.bar_chart(
                            data=sorted_df.set_index(sorted_df.columns[0])[selected_stat],
                            use_container_width=True
                        )
                
        except Exception as e:
            st.error(f"Error displaying standings: {str(e)}")
            st.write("Raw data:")
            st.write(st.session_state.fantrax_standings)
    else:
        st.info("Click 'Fetch Standings' to load the standings data.")
        
    # Add information about the standings
    with st.expander("About Fantrax Standings"):
        st.markdown("""
        This component fetches standings data directly from the Fantrax API for real-time league standings.
        
        **How it works:**
        1. Enter your Fantrax league standings URL or API endpoint
        2. Click 'Fetch Standings' to load the data
        3. View the styled standings table
        4. Analyze the standings with the visualization tools
        5. Download the standings data as a CSV file
        
        **Benefits of using the API:**
        - Get more complete, accurate data than scraping the public web page
        - Access additional stats that might not be visible on the public page
        - More reliable data retrieval that's less likely to break with website changes
        
        The data is automatically refreshed each time you click the 'Fetch Standings' button.
        """)