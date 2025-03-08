import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io

def calculate_remaining_salary(team_roster: pd.DataFrame, team_name: str, salary_cap: float = 260.0) -> float:
    """Calculate remaining salary for a team based on current roster"""
    if team_roster.empty:
        return salary_cap

    # Filter for the team and exclude MINORS players
    team_data = team_roster[
        (team_roster['team'] == team_name) & 
        (team_roster['status'].str.upper() != 'MINORS')
    ]

    # Get current salary
    current_salary = team_data['salary'].sum()
    return salary_cap - current_salary

def initialize_session_state():
    """Initialize session state variables"""
    if 'auction_settings' not in st.session_state:
        st.session_state.auction_settings = {
            'salary_cap': 260.0,
            'nomination_limit': 1,
            'initial_bid_timer': 12,  # hours
            'extension_threshold': 8,  # hours
            'bid_increment': 0.5,
            'minimum_bid': 1.0
        }

    if 'available_players' not in st.session_state:
        st.session_state.available_players = pd.DataFrame(
            columns=['player_name', 'position', 'mlb_team', 'status', 'salary']
        )

    if 'auction_nominations' not in st.session_state:
        st.session_state.auction_nominations = pd.DataFrame(
            columns=['player_name', 'nominated_by', 'nominated_at', 'current_bid', 
                    'winning_team', 'bid_end_time', 'status']
        )

    if 'auction_bids' not in st.session_state:
        st.session_state.auction_bids = pd.DataFrame(
            columns=['player_name', 'team_name', 'bid_amount', 'bid_time']
        )

def process_fantrax_players(df: pd.DataFrame) -> pd.DataFrame:
    """Process Fantrax players CSV into required format"""
    return pd.DataFrame({
        'player_name': df['Player'],
        'position': df['Position'],
        'mlb_team': df['Team'],
        'status': df['Status'],
        'salary': pd.to_numeric(df['Salary'], errors='coerce').fillna(0)
    })

def render_settings():
    """Render auction draft settings section"""
    st.subheader("⚙️ Draft Settings")

    settings = st.session_state.auction_settings

    col1, col2 = st.columns(2)

    with col1:
        settings['salary_cap'] = st.number_input(
            "Salary Cap ($)",
            min_value=1.0,
            value=float(settings['salary_cap']),
            step=1.0,
            help="Maximum amount each team can spend"
        )

        settings['nomination_limit'] = st.number_input(
            "Nominations Per Team",
            min_value=1,
            value=int(settings['nomination_limit']),
            help="Number of players each team can nominate"
        )

        settings['bid_increment'] = st.number_input(
            "Minimum Bid Increment ($)",
            min_value=0.1,
            value=float(settings['bid_increment']),
            step=0.1,
            help="Minimum amount to increase bid by"
        )

    with col2:
        settings['initial_bid_timer'] = st.number_input(
            "Initial Bid Timer (hours)",
            min_value=1,
            value=int(settings['initial_bid_timer']),
            help="How long nominations stay active"
        )

        settings['extension_threshold'] = st.number_input(
            "Extension Threshold (hours)",
            min_value=1,
            value=int(settings['extension_threshold']),
            help="Time remaining that triggers extension on new bid"
        )

        settings['minimum_bid'] = st.number_input(
            "Minimum Starting Bid ($)",
            min_value=0.5,
            value=float(settings['minimum_bid']),
            step=0.5,
            help="Minimum amount for initial nomination"
        )

    # Player list upload
    st.subheader("📄 Player List")
    uploaded_file = st.file_uploader(
        "Upload Player List (CSV)",
        type=['csv'],
        help="Upload the Fantrax players export CSV"
    )

    if uploaded_file is not None:
        try:
            # Read CSV file
            df = pd.read_csv(uploaded_file)
            required_columns = ['Player', 'Position', 'Team', 'Status', 'Salary']

            # Verify columns
            if not all(col in df.columns for col in required_columns):
                st.error("CSV file must be a Fantrax players export with required columns")
                return

            # Process and update available players
            processed_df = process_fantrax_players(df)
            st.session_state.available_players = processed_df
            st.success(f"Successfully loaded {len(processed_df)} players!")

            # Preview the data
            st.dataframe(
                processed_df.head(),
                column_config={
                    "player_name": "Player",
                    "position": "Position",
                    "mlb_team": "MLB Team",
                    "status": "Status",
                    "salary": st.column_config.NumberColumn(
                        "Salary",
                        format="$%.2f"
                    )
                }
            )

        except Exception as e:
            st.error(f"Error loading CSV file: {str(e)}")

def render(roster_data: pd.DataFrame = None):
    """Render auction draft section"""
    st.header("🏦 Auction Draft")

    # Initialize session state
    initialize_session_state()

    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs([
        "⚙️ Settings",
        "📊 Active Auctions",
        "🎯 Nominate Player",
        "📜 Auction History"
    ])

    with tab1:
        render_settings()

    with tab2:
        st.subheader("Active Auctions")
        if st.session_state.auction_nominations.empty:
            st.info("No active auctions at the moment.")
        else:
            active_auctions = st.session_state.auction_nominations[
                st.session_state.auction_nominations['status'] == 'active'
            ]
            for _, auction in active_auctions.iterrows():
                with st.container():
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.markdown(f"### {auction['player_name']}")
                        st.markdown(f"Current Bid: ${auction['current_bid']:.2f}")
                        st.markdown(f"Leading: {auction['winning_team']}")
                    with col2:
                        time_remaining = auction['bid_end_time'] - datetime.now()
                        hours = time_remaining.total_seconds() // 3600
                        minutes = (time_remaining.total_seconds() % 3600) // 60
                        st.markdown(f"Time Remaining: {int(hours)}h {int(minutes)}m")

                        # Only show bid button if auction is still active
                        if time_remaining.total_seconds() > 0:
                            new_bid = st.number_input(
                                "Enter Bid Amount",
                                min_value=float(auction['current_bid'] + st.session_state.auction_settings['bid_increment']),
                                step=st.session_state.auction_settings['bid_increment'],
                                key=f"bid_{auction['player_name']}"
                            )
                            if st.button("Place Bid", key=f"bid_button_{auction['player_name']}"):
                                st.success(f"Bid placed: ${new_bid:.2f}")

    with tab3:
        st.subheader("Nominate a Player")

        # Select team (this would be automated in production)
        teams = ["Texas Rangers", "Seattle Mariners", "Houston Astros", "Athletics", 
                "Los Angeles Angels", "Cleveland Guardians", "Detroit Tigers", 
                "Minnesota Twins", "Chicago White Sox", "Kansas City Royals"]
        nominating_team = st.selectbox("Select Your Team", teams)

        # Calculate remaining salary based on current roster
        remaining_salary = calculate_remaining_salary(
            roster_data if roster_data is not None else pd.DataFrame(),
            nominating_team,
            st.session_state.auction_settings['salary_cap']
        )

        st.markdown(f"Remaining Salary: ${remaining_salary:.2f}")

        # Player search and nomination
        if not st.session_state.available_players.empty:
            search_term = st.text_input("Search Players", "")
            if search_term:
                filtered_players = st.session_state.available_players[
                    st.session_state.available_players['player_name'].str.contains(search_term, case=False)
                ]
                if not filtered_players.empty:
                    selected_player = st.selectbox(
                        "Select Player to Nominate",
                        filtered_players['player_name'].tolist()
                    )

                    with st.form("nomination_form"):
                        starting_bid = st.number_input(
                            "Starting Bid ($)",
                            min_value=st.session_state.auction_settings['minimum_bid'],
                            step=0.5
                        )

                        if st.form_submit_button("Nominate Player"):
                            if starting_bid <= remaining_salary:
                                # Add nomination
                                new_nomination = pd.DataFrame([{
                                    'player_name': selected_player,
                                    'nominated_by': nominating_team,
                                    'nominated_at': datetime.now(),
                                    'current_bid': starting_bid,
                                    'winning_team': nominating_team,
                                    'bid_end_time': datetime.now() + timedelta(hours=st.session_state.auction_settings['initial_bid_timer']),
                                    'status': 'active'
                                }])

                                st.session_state.auction_nominations = pd.concat([
                                    st.session_state.auction_nominations, 
                                    new_nomination
                                ], ignore_index=True)

                                st.success(f"Successfully nominated {selected_player} at ${starting_bid:.2f}")
                            else:
                                st.error("Starting bid exceeds remaining salary cap!")
                else:
                    st.warning("No players found matching your search.")
        else:
            st.warning("Please upload a player list in the Settings tab first.")

    with tab4:
        st.subheader("Completed Auctions")
        if st.session_state.auction_nominations.empty:
            st.info("No completed auctions yet.")
        else:
            completed_auctions = st.session_state.auction_nominations[
                st.session_state.auction_nominations['status'] == 'completed'
            ]
            if completed_auctions.empty:
                st.info("No completed auctions yet.")
            else:
                st.dataframe(
                    completed_auctions,
                    column_config={
                        "player_name": "Player",
                        "winning_team": "Winning Team",
                        "current_bid": st.column_config.NumberColumn(
                            "Winning Bid",
                            format="$%.2f"
                        ),
                        "nominated_at": "Start Time",
                        "bid_end_time": "End Time"
                    }
                )