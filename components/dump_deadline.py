import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import re

def render():
    """Render the Dump Deadline trade analysis page"""
    st.title("🔥 Dump Deadline Trade Analysis")
    
    st.info("""
    **ABL Trade Deadline Analysis System:**
    - **Player Values**: MVP rankings + prospect rankings combined
    - **FA Budget**: $40 per team × 30 teams = $1,200 total pool
    - **Draft Picks**: Earlier rounds and years more valuable
    - **Trade Winners/Losers**: Based on total value exchanged
    """)
    
    try:
        # Load trade data
        trades_df = pd.read_csv("attached_assets/Fantrax-Transaction-History-Trades-ABL Season 5.csv")
        
        # Load MVP data for player values
        mvp_data = pd.read_csv("attached_assets/MVP-Player-List.csv")
        mvp_values = {}
        for _, row in mvp_data.iterrows():
            # MVP value: inverse of rank (higher rank = lower value)
            mvp_rank = mvp_data.index[mvp_data['Player'] == row['Player']].tolist()[0] + 1
            mvp_values[row['Player']] = max(1, 101 - mvp_rank)  # Scale 1-100
        
        # Load prospect data for additional player values
        try:
            prospect_data = pd.read_csv("attached_assets/ABL-Import.csv")
            prospect_values = {}
            for _, row in prospect_data.iterrows():
                if pd.notna(row.get('Player')):
                    # Prospect value based on ranking position
                    prospect_rank = prospect_data.index[prospect_data['Player'] == row['Player']].tolist()[0] + 1
                    prospect_values[row['Player']] = max(1, 51 - prospect_rank)  # Scale 1-50
        except:
            prospect_values = {}
            st.warning("Could not load prospect data for enhanced valuations")
        
        # Process trades data
        trades_df['Date'] = pd.to_datetime(trades_df['Date (EDT)'])
        trades_df = trades_df.sort_values('Date')
        
        # Group trades by timestamp to identify complete transactions
        trade_groups = {}
        for _, row in trades_df.iterrows():
            key = f"{row['Date']}_{row['Period']}"
            if key not in trade_groups:
                trade_groups[key] = []
            trade_groups[key].append(row)
        
        # Calculate values for each trade
        def get_player_value(player_name):
            """Get combined value of a player from MVP and prospect rankings"""
            mvp_val = mvp_values.get(player_name, 0)
            prospect_val = prospect_values.get(player_name, 0)
            return mvp_val + prospect_val
        
        def get_draft_pick_value(pick_text):
            """Calculate value of draft picks based on year and round"""
            if not isinstance(pick_text, str) or "Draft Pick" not in pick_text:
                return 0
            
            # Extract year and round
            year_match = re.search(r'(\d{4})', pick_text)
            round_match = re.search(r'Round (\d+)', pick_text)
            
            if not year_match or not round_match:
                return 0
            
            year = int(year_match.group(1))
            round_num = int(round_match.group(1))
            
            # Base value decreases with later years and rounds
            current_year = 2025
            year_penalty = (year - current_year) * 5  # 5 point penalty per year
            round_penalty = (round_num - 1) * 10  # 10 point penalty per round
            
            base_value = 50
            return max(1, base_value - year_penalty - round_penalty)
        
        def get_budget_value(budget_text):
            """Extract budget amount and convert to value"""
            if not isinstance(budget_text, str) or "Budget Amount" not in budget_text:
                return 0
            
            amount_match = re.search(r'\$(\d+(?:\.\d+)?)', budget_text)
            if amount_match:
                amount = float(amount_match.group(1))
                # Each dollar is worth 2.5 points (since $40 max per team)
                return amount * 2.5
            return 0
        
        # Analyze each trade group
        trade_analysis = []
        
        for trade_key, trade_items in trade_groups.items():
            if len(trade_items) < 2:  # Skip single-item transactions
                continue
            
            # Identify teams involved
            teams_involved = set()
            for item in trade_items:
                if pd.notna(item['From']) and item['From'] != "(Drop)":
                    teams_involved.add(item['From'])
                if pd.notna(item['To']) and item['To'] != "(Drop)":
                    teams_involved.add(item['To'])
            
            if len(teams_involved) < 2:
                continue
            
            # Calculate values for each team
            team_values = {team: 0 for team in teams_involved}
            trade_details = {team: [] for team in teams_involved}
            
            for item in trade_items:
                from_team = item['From']
                to_team = item['To']
                player = item['Player']
                
                if to_team == "(Drop)":
                    continue
                
                # Calculate item value
                value = 0
                item_type = "Player"
                
                if "Draft Pick" in player:
                    value = get_draft_pick_value(player)
                    item_type = "Draft Pick"
                elif "Budget Amount" in player:
                    value = get_budget_value(player)
                    item_type = "Budget"
                else:
                    value = get_player_value(player)
                
                # Add value to receiving team, subtract from giving team
                if pd.notna(to_team) and to_team in team_values:
                    team_values[to_team] += value
                    trade_details[to_team].append({
                        'item': player,
                        'value': value,
                        'type': item_type,
                        'direction': 'received'
                    })
                
                if pd.notna(from_team) and from_team in team_values and from_team != "(Drop)":
                    team_values[from_team] -= value
                    trade_details[from_team].append({
                        'item': player,
                        'value': value,
                        'type': item_type,
                        'direction': 'gave'
                    })
            
            # Store trade analysis
            trade_analysis.append({
                'date': trade_items[0]['Date'],
                'teams': list(teams_involved),
                'team_values': team_values,
                'trade_details': trade_details,
                'total_value': sum(abs(v) for v in team_values.values()) / 2,  # Divide by 2 to avoid double counting
                'value_difference': max(team_values.values()) - min(team_values.values()),
                'is_lopsided': max(team_values.values()) - min(team_values.values()) > 30
            })
        
        # Sort trades by value difference (most lopsided first)
        trade_analysis.sort(key=lambda x: x['value_difference'], reverse=True)
        
        st.sidebar.success(f"✅ Analyzed {len(trade_analysis)} trade transactions")
        
        # Display analysis tabs
        tab1, tab2, tab3, tab4 = st.tabs(["🏆 Winners & Losers", "📊 Trade Rankings", "⚖️ Most Lopsided", "📈 Trade Activity"])
        
        with tab1:
            st.write("## Team Trade Performance")
            
            # Calculate overall team performance
            team_performance = {}
            for trade in trade_analysis:
                for team, value in trade['team_values'].items():
                    if team not in team_performance:
                        team_performance[team] = {'total_value': 0, 'trade_count': 0}
                    team_performance[team]['total_value'] += value
                    team_performance[team]['trade_count'] += 1
            
            # Sort teams by performance
            sorted_teams = sorted(team_performance.items(), key=lambda x: x[1]['total_value'], reverse=True)
            
            # Display top winners
            st.write("### 🥇 Biggest Trade Winners")
            for i, (team, stats) in enumerate(sorted_teams[:5]):
                if stats['total_value'] > 0:
                    col1, col2, col3, col4 = st.columns([1, 3, 2, 2])
                    with col1:
                        st.markdown(f"**#{i+1}**")
                    with col2:
                        st.markdown(f"**{team}**")
                    with col3:
                        st.metric("Net Value", f"+{stats['total_value']:.1f}")
                    with col4:
                        st.metric("Trades", stats['trade_count'])
            
            st.write("### 🔻 Biggest Trade Losers")
            for i, (team, stats) in enumerate(sorted_teams[-5:]):
                if stats['total_value'] < 0:
                    col1, col2, col3, col4 = st.columns([1, 3, 2, 2])
                    with col1:
                        st.markdown(f"**#{len(sorted_teams)-4+i}**")
                    with col2:
                        st.markdown(f"**{team}**")
                    with col3:
                        st.metric("Net Value", f"{stats['total_value']:.1f}")
                    with col4:
                        st.metric("Trades", stats['trade_count'])
        
        with tab2:
            st.write("## All Trade Transactions")
            
            for i, trade in enumerate(trade_analysis[:20]):  # Show top 20 trades
                with st.expander(f"Trade #{i+1}: {trade['date'].strftime('%B %d, %Y')} - Value Diff: {trade['value_difference']:.1f}"):
                    
                    # Show teams and their net gains/losses
                    st.write("### Team Summary")
                    for team in trade['teams']:
                        net_value = trade['team_values'][team]
                        color = "🟢" if net_value > 0 else "🔴" if net_value < 0 else "🟡"
                        st.write(f"{color} **{team}**: {net_value:+.1f} points")
                    
                    st.write("### Trade Details")
                    for team in trade['teams']:
                        st.write(f"**{team}:**")
                        received = [item for item in trade['trade_details'][team] if item['direction'] == 'received']
                        gave = [item for item in trade['trade_details'][team] if item['direction'] == 'gave']
                        
                        if received:
                            st.write("  Received:")
                            for item in received:
                                st.write(f"    • {item['item']} ({item['type']}) - {item['value']:.1f} pts")
                        
                        if gave:
                            st.write("  Gave:")
                            for item in gave:
                                st.write(f"    • {item['item']} ({item['type']}) - {item['value']:.1f} pts")
                        st.write("")
        
        with tab3:
            st.write("## Most Lopsided Trades")
            
            lopsided_trades = [t for t in trade_analysis if t['is_lopsided']]
            
            if lopsided_trades:
                for i, trade in enumerate(lopsided_trades[:10]):
                    winner = max(trade['team_values'], key=trade['team_values'].get)
                    loser = min(trade['team_values'], key=trade['team_values'].get)
                    
                    st.write(f"### Trade #{i+1}: {trade['date'].strftime('%B %d')}")
                    col1, col2, col3 = st.columns([2, 1, 2])
                    
                    with col1:
                        st.success(f"**Winner: {winner}**")
                        st.write(f"Net gain: +{trade['team_values'][winner]:.1f} pts")
                    
                    with col2:
                        st.write("vs")
                    
                    with col3:
                        st.error(f"**Loser: {loser}**")
                        st.write(f"Net loss: {trade['team_values'][loser]:.1f} pts")
                    
                    st.write(f"**Value Difference:** {trade['value_difference']:.1f} points")
                    st.divider()
            else:
                st.info("No significantly lopsided trades found (>30 point difference)")
        
        with tab4:
            st.write("## Trade Activity Analysis")
            
            # Create timeline chart
            dates = [t['date'] for t in trade_analysis]
            values = [t['total_value'] for t in trade_analysis]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dates,
                y=values,
                mode='markers+lines',
                name='Trade Value',
                marker=dict(size=8, color='blue'),
                line=dict(width=2)
            ))
            
            fig.update_layout(
                title='Trade Activity Over Time',
                xaxis_title='Date',
                yaxis_title='Total Trade Value',
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Summary statistics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Trades", len(trade_analysis))
            
            with col2:
                avg_value = sum(t['total_value'] for t in trade_analysis) / len(trade_analysis) if trade_analysis else 0
                st.metric("Avg Trade Value", f"{avg_value:.1f}")
            
            with col3:
                lopsided_count = len([t for t in trade_analysis if t['is_lopsided']])
                st.metric("Lopsided Trades", lopsided_count)
            
            with col4:
                max_diff = max(t['value_difference'] for t in trade_analysis) if trade_analysis else 0
                st.metric("Max Value Diff", f"{max_diff:.1f}")
        
    except FileNotFoundError:
        st.error("Trade data file not found. Please ensure Fantrax-Transaction-History-Trades-ABL Season 5.csv is in the attached_assets folder.")
    except Exception as e:
        st.error(f"Error loading trade data: {str(e)}")
        st.write("Please check that all required data files are available and properly formatted.")