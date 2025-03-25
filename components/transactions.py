import streamlit as st
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime

def render(transactions_data: List[Dict[str, Any]]):
    """
    Render transactions section with filtering options.
    
    Args:
        transactions_data: List of transaction dictionaries
    """
    # Create an expander for debug information
    with st.expander("Debug Information", expanded=False):
        st.write(f"Transactions data type: {type(transactions_data)}")
        st.write(f"Number of transactions: {len(transactions_data) if isinstance(transactions_data, list) else 'Not a list'}")
        
        if transactions_data and isinstance(transactions_data, list) and len(transactions_data) > 0:
            st.write("First transaction keys:", list(transactions_data[0].keys()))
            st.write("First transaction:", transactions_data[0])
    
    # Ensure transactions_data is a list
    if not isinstance(transactions_data, list):
        st.error("Transactions data is not in the expected format (list expected)")
        st.info("No transaction data available")
        return
        
    # Handle empty list
    if not transactions_data or len(transactions_data) == 0:
        st.info("No transaction data available")
        return
    
    # Create DataFrame from transactions data
    df = pd.DataFrame(transactions_data)
    
    # Extract unique transaction types for filtering
    transaction_types = ["All Types"]
    if 'transaction_type' in df.columns and not df.empty:
        unique_types = df['transaction_type'].unique()
        transaction_types.extend([t for t in unique_types if t and not pd.isna(t)])
    
    # Create sidebar filters
    with st.sidebar:
        st.subheader("Transaction Filters")
        
        # Transaction type filter
        selected_type = st.selectbox(
            "Transaction Type",
            transaction_types,
            index=0
        )
        
        # Team filter
        team_options = ["All Teams"]
        if 'team' in df.columns and not df.empty:
            unique_teams = df['team'].unique()
            team_options.extend([t for t in unique_teams if t and not pd.isna(t)])
        
        selected_team = st.selectbox(
            "Team",
            team_options,
            index=0
        )
        
        # Date range filter
        date_min, date_max = None, None
        date_range = None  # Initialize date_range to avoid 'possibly unbound' error
        
        if 'date' in df.columns and not df.empty:
            try:
                # Convert date strings to datetime objects for filtering
                date_values = []
                for date_str in df['date']:
                    try:
                        if isinstance(date_str, str):
                            date_val = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
                            date_values.append(date_val)
                    except ValueError:
                        pass
                
                if date_values:
                    date_min = min(date_values).date()
                    date_max = max(date_values).date()
                    
                    # Only create the date picker if we have valid min/max dates
                    date_range = st.date_input(
                        "Date Range",
                        value=(date_min, date_max),
                        min_value=date_min,
                        max_value=date_max
                    )
            except Exception as e:
                st.warning(f"Error processing dates: {str(e)}")
        
    # Apply filters to the DataFrame
    filtered_df = df.copy()
    
    # Apply transaction type filter
    if selected_type != "All Types" and 'transaction_type' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['transaction_type'] == selected_type]
    
    # Apply team filter
    if selected_team != "All Teams" and 'team' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['team'] == selected_team]
    
    # Apply date filter if date range is selected
    if 'date' in filtered_df.columns and date_min and date_max and date_range is not None:
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
            
            # Convert strings to datetime for comparison
            def is_date_in_range(date_str):
                try:
                    if isinstance(date_str, str):
                        date_val = datetime.strptime(date_str, "%Y-%m-%d %H:%M").date()
                        return start_date <= date_val <= end_date
                    return False
                except ValueError:
                    return False
            
            filtered_df = filtered_df[filtered_df['date'].apply(is_date_in_range)]
    
    # Display filtered transactions
    st.subheader(f"Filtered Transactions ({len(filtered_df)} results)")
    
    if not filtered_df.empty:
        # Determine columns to display based on available data
        display_columns = []
        
        # Include standard columns
        standard_columns = ['date', 'team', 'player_name', 'count', 'transaction_type', 'finalized']
        for col in standard_columns:
            if col in filtered_df.columns:
                display_columns.append(col)
        
        # If we have a 'players' column that contains lists, we'll handle it specially
        if 'players' in filtered_df.columns:
            # Check if it's a list/array type column
            if filtered_df['players'].apply(lambda x: isinstance(x, (list, tuple))).any():
                # Create a new column with player names as a string
                filtered_df['players_display'] = filtered_df['players'].apply(
                    lambda players: ", ".join([p.get('name', 'Unknown') if isinstance(p, dict) else str(p) for p in players])
                    if isinstance(players, (list, tuple)) else ""
                )
                display_columns.append('players_display')
        
        # Display the dataframe with formatted columns
        st.dataframe(
            filtered_df[display_columns],
            column_config={
                "date": st.column_config.DatetimeColumn("Date"),
                "team": st.column_config.TextColumn("Team"),
                "player_name": st.column_config.TextColumn("Player"),
                "count": st.column_config.NumberColumn("Count"),
                "transaction_type": st.column_config.TextColumn("Type"),
                "finalized": st.column_config.CheckboxColumn("Finalized"),
                "players_display": st.column_config.TextColumn("Players")
            },
            use_container_width=True
        )
    else:
        st.info("No transactions match the selected filters")
    
    # Transaction details section
    if not filtered_df.empty:
        st.subheader("Transaction Details")
        
        # Get list of transaction IDs
        if 'id' in filtered_df.columns:
            transaction_ids = filtered_df['id'].tolist()
            
            # Create a selectbox to choose a specific transaction
            selected_tx_id = st.selectbox(
                "Select Transaction for Details",
                transaction_ids,
                format_func=lambda x: f"ID: {x}"
            )
            
            if selected_tx_id:
                # Get the selected transaction
                selected_tx = filtered_df[filtered_df['id'] == selected_tx_id].iloc[0]
                
                # Display transaction details
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if 'date' in selected_tx:
                        st.metric("Date", selected_tx['date'])
                    if 'team' in selected_tx:
                        st.metric("Team", selected_tx['team'])
                
                with col2:
                    if 'transaction_type' in selected_tx:
                        st.metric("Type", selected_tx['transaction_type'])
                    if 'count' in selected_tx:
                        st.metric("Player Count", selected_tx['count'])
                
                with col3:
                    if 'id' in selected_tx:
                        st.metric("Transaction ID", selected_tx['id'])
                    if 'finalized' in selected_tx:
                        st.metric("Finalized", "Yes" if selected_tx['finalized'] else "No")
                
                # Display players involved in the transaction
                if 'players' in selected_tx and isinstance(selected_tx['players'], (list, tuple)):
                    st.subheader("Players Involved")
                    players = selected_tx['players']
                    
                    if players:
                        # Create a dataframe of players if they are dictionary objects
                        if isinstance(players[0], dict):
                            player_df = pd.DataFrame(players)
                            st.dataframe(player_df)
                        else:
                            # If they're just strings, display as a list
                            st.write(", ".join([str(p) for p in players]))
                    else:
                        st.info("No player details available for this transaction")
        else:
            st.info("No transaction IDs available for detailed view")