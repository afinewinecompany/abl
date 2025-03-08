import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def calculate_remaining_salary(team_bids: pd.DataFrame, team_name: str, salary_cap: float = 260.0) -> float:
    """Calculate remaining salary for a team"""
    if team_bids.empty:
        return salary_cap
    team_spent = team_bids[team_bids['winning_team'] == team_name]['bid_amount'].sum()
    return salary_cap - team_spent

def render():
    """Render auction draft section"""
    st.header("🏦 Auction Draft")
    
    # Initialize session state for auction data
    if 'auction_nominations' not in st.session_state:
        st.session_state.auction_nominations = pd.DataFrame(
            columns=['player_name', 'nominated_by', 'nominated_at', 'current_bid', 
                    'winning_team', 'bid_end_time', 'status']
        )
    
    if 'auction_bids' not in st.session_state:
        st.session_state.auction_bids = pd.DataFrame(
            columns=['player_name', 'team_name', 'bid_amount', 'bid_time']
        )

    # Mock team data for testing
    teams = ["Texas Rangers", "Seattle Mariners", "Houston Astros", "Athletics", 
             "Los Angeles Angels", "Cleveland Guardians", "Detroit Tigers", 
             "Minnesota Twins", "Chicago White Sox", "Kansas City Royals"]

    # Create tabs for different auction views
    tab1, tab2, tab3 = st.tabs([
        "📊 Active Auctions",
        "🎯 Nominate Player",
        "📜 Auction History"
    ])

    with tab1:
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
                                min_value=float(auction['current_bid'] + 0.5),
                                step=0.5,
                                key=f"bid_{auction['player_name']}"
                            )
                            if st.button("Place Bid", key=f"bid_button_{auction['player_name']}"):
                                st.success(f"Bid placed: ${new_bid:.2f}")

    with tab2:
        st.subheader("Nominate a Player")
        
        # Select team (this would be automated in production)
        nominating_team = st.selectbox("Select Your Team", teams)
        
        # Calculate remaining salary
        remaining_salary = calculate_remaining_salary(
            st.session_state.auction_bids, 
            nominating_team
        )
        
        st.markdown(f"Remaining Salary: ${remaining_salary:.2f}")
        
        # Nomination form
        with st.form("nomination_form"):
            player_name = st.text_input("Player Name")
            starting_bid = st.number_input("Starting Bid ($)", min_value=1.0, step=0.5)
            
            if st.form_submit_button("Nominate Player"):
                if starting_bid <= remaining_salary:
                    # Add nomination
                    new_nomination = pd.DataFrame([{
                        'player_name': player_name,
                        'nominated_by': nominating_team,
                        'nominated_at': datetime.now(),
                        'current_bid': starting_bid,
                        'winning_team': nominating_team,
                        'bid_end_time': datetime.now() + timedelta(hours=12),
                        'status': 'active'
                    }])
                    
                    st.session_state.auction_nominations = pd.concat([
                        st.session_state.auction_nominations, 
                        new_nomination
                    ], ignore_index=True)
                    
                    st.success(f"Successfully nominated {player_name} at ${starting_bid:.2f}")
                else:
                    st.error("Starting bid exceeds remaining salary cap!")

    with tab3:
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
