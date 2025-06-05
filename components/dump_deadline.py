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
        
        # Load MVP data for comprehensive player values
        mvp_data = pd.read_csv("attached_assets/MVP-Player-List.csv")
        
        def calculate_comprehensive_player_value(player_data):
            """Calculate comprehensive player value using all MVP metrics"""
            # Clean and prepare data
            age = pd.to_numeric(player_data.get('Age', 25), errors='coerce')
            salary = pd.to_numeric(player_data.get('Salary', 1), errors='coerce')
            fpts = pd.to_numeric(player_data.get('FPts', 0), errors='coerce')
            fpg = pd.to_numeric(player_data.get('FP/G', 0), errors='coerce')
            contract = str(player_data.get('Contract', '2025'))
            position = str(player_data.get('Position', 'UT'))
            
            # Normalize values to 0-1 scale based on dataset ranges
            max_fpts = mvp_data['FPts'].max() if 'FPts' in mvp_data.columns else 400
            max_fpg = mvp_data['FP/G'].max() if 'FP/G' in mvp_data.columns else 25
            max_salary = mvp_data['Salary'].max() if 'Salary' in mvp_data.columns else 70
            
            # Fantasy Points component (40% weight) - primary performance metric
            fpts_score = min(1.0, fpts / max_fpts) if max_fpts > 0 else 0
            
            # Fantasy Points per Game component (30% weight) - health/consistency factor
            fpg_score = min(1.0, fpg / max_fpg) if max_fpg > 0 else 0
            
            # Position value component (10% weight) - scarcity-based
            position_values = {
                'C': 1.0,      # Catcher - most scarce
                'SS': 0.9,     # Shortstop
                '2B': 0.85,    # Second base
                '3B': 0.8,     # Third base
                'CF': 0.75,    # Center field
                'SP': 0.7,     # Starting pitcher
                '1B': 0.65,    # First base
                'LF': 0.6, 'RF': 0.6,  # Corner outfield
                'RP': 0.5,     # Relief pitcher
                'UT': 0.55,    # Utility
                'DH': 0.4      # Designated hitter
            }
            # Get highest position value for multi-position players
            pos_score = 0
            for pos in position.split(','):
                pos_clean = pos.strip()
                if pos_clean in position_values:
                    pos_score = max(pos_score, position_values[pos_clean])
            
            # Contract value component (10% weight) - longer contracts more valuable for young players
            contract_values = {
                '2050': 1.0, '2045': 0.95, '2040': 0.9, '2035': 0.85, 
                '2029': 0.8, '2028': 0.7, '2027': 0.6, '2026': 0.5, 
                '2025': 0.3, '1st': 0.2
            }
            contract_score = contract_values.get(contract, 0.1)
            
            # Age factor (10% weight) - younger players more valuable (increased from 5%)
            age_score = max(0, (35 - age) / 15) if age <= 35 else 0
            
            # Salary efficiency (10% weight) - lower salary relative to performance is better (increased from 5%)
            salary_efficiency = 1.0 - (salary / max_salary) if max_salary > 0 else 0.5
            
            # Combine all components
            total_score = (
                fpts_score * 0.40 +      # Fantasy points
                fpg_score * 0.30 +       # Points per game (increased from 25%)
                pos_score * 0.10 +       # Position value
                contract_score * 0.10 +  # Contract value (reduced from 15%)
                age_score * 0.05 +       # Age factor
                salary_efficiency * 0.05 # Salary efficiency
            )
            
            # Scale to 0-100 range
            return total_score * 100
        
        # Calculate comprehensive values for all MVP players
        mvp_values = {}
        for _, row in mvp_data.iterrows():
            player_name = row.get('Player', '')
            if player_name:
                mvp_values[player_name] = calculate_comprehensive_player_value(row)
        
        # Load prospect data for additional player values
        try:
            prospect_data = pd.read_csv("attached_assets/ABL-Import.csv")
            prospect_values = {}
            for _, row in prospect_data.iterrows():
                if pd.notna(row.get('Name')):
                    player_name = row['Name']
                    prospect_score = pd.to_numeric(row.get('Score', 0), errors='coerce')
                    if pd.notna(prospect_score):
                        # Check if player also appears in MVP data with actual fantasy points
                        base_multiplier = 4  # Default 0-40 range
                        
                        if player_name in mvp_values:
                            # Player is in both lists - check if they have MLB production
                            player_mvp_row = mvp_data[mvp_data['Player'] == player_name]
                            if not player_mvp_row.empty:
                                fpts = pd.to_numeric(player_mvp_row.iloc[0].get('FPts', 0), errors='coerce')
                                if fpts > 0:
                                    # Player has MLB production - significantly reduce prospect score
                                    # Focus more on MLB performance than prospect grade
                                    base_multiplier = 1.5  # Reduce to 0-15 range for players with MLB performance
                        
                        prospect_values[player_name] = prospect_score * base_multiplier
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
        
        # Team colors and logos mapping
        def get_team_colors(team_name):
            """Get team colors for styling"""
            team_colors = {
                'Arizona Diamondbacks': {'primary': '#A71930', 'secondary': '#000000'},
                'Atlanta Braves': {'primary': '#CE1141', 'secondary': '#13274F'},
                'Baltimore Orioles': {'primary': '#DF4601', 'secondary': '#000000'},
                'Boston Red Sox': {'primary': '#BD3039', 'secondary': '#0C2340'},
                'Chicago Cubs': {'primary': '#0E3386', 'secondary': '#CC3433'},
                'Chicago White Sox': {'primary': '#27251F', 'secondary': '#C4CED4'},
                'Cincinnati Reds': {'primary': '#C6011F', 'secondary': '#000000'},
                'Cleveland Guardians': {'primary': '#E31937', 'secondary': '#002653'},
                'Colorado Rockies': {'primary': '#33006F', 'secondary': '#C4CED4'},
                'Detroit Tigers': {'primary': '#0C2340', 'secondary': '#FA4616'},
                'Houston Astros': {'primary': '#002D62', 'secondary': '#EB6E1F'},
                'Kansas City Royals': {'primary': '#004687', 'secondary': '#BD9B60'},
                'Los Angeles Angels': {'primary': '#BA0021', 'secondary': '#003263'},
                'Los Angeles Dodgers': {'primary': '#005A9C', 'secondary': '#FFFFFF'},
                'Miami Marlins': {'primary': '#00A3E0', 'secondary': '#EF3340'},
                'Milwaukee Brewers': {'primary': '#FFC52F', 'secondary': '#12284B'},
                'Minnesota Twins': {'primary': '#002B5C', 'secondary': '#D31145'},
                'New York Mets': {'primary': '#002D72', 'secondary': '#FF5910'},
                'New York Yankees': {'primary': '#132448', 'secondary': '#C4CED4'},
                'Oakland Athletics': {'primary': '#003831', 'secondary': '#EFB21E'},
                'Philadelphia Phillies': {'primary': '#E81828', 'secondary': '#002D72'},
                'Pittsburgh Pirates': {'primary': '#FDB827', 'secondary': '#27251F'},
                'San Diego Padres': {'primary': '#2F241D', 'secondary': '#FFC425'},
                'San Francisco Giants': {'primary': '#FD5A1E', 'secondary': '#27251F'},
                'Seattle Mariners': {'primary': '#0C2C56', 'secondary': '#005C5C'},
                'St. Louis Cardinals': {'primary': '#C41E3A', 'secondary': '#FEDB00'},
                'Saint Louis Cardinals': {'primary': '#C41E3A', 'secondary': '#FEDB00'},
                'Tampa Bay Rays': {'primary': '#092C5C', 'secondary': '#8FBCE6'},
                'Texas Rangers': {'primary': '#003278', 'secondary': '#C0111F'},
                'Toronto Blue Jays': {'primary': '#134A8E', 'secondary': '#1D2D5C'},
                'Washington Nationals': {'primary': '#AB0003', 'secondary': '#14225A'}
            }
            return team_colors.get(team_name, {'primary': '#333333', 'secondary': '#666666'})

        # Calculate values for each trade
        def get_player_value(player_name):
            """Get combined value of a player from MVP and prospect rankings"""
            mvp_val = mvp_values.get(player_name, 0)
            prospect_val = prospect_values.get(player_name, 0)
            
            # Rule: If player has both MVP and prospect scores, but zero FPts, ignore MVP score
            if mvp_val > 0 and prospect_val > 0:
                # Check if player has zero fantasy points in MVP data
                player_row = mvp_data[mvp_data['Player'] == player_name]
                if not player_row.empty:
                    fpts = pd.to_numeric(player_row.iloc[0].get('FPts', 0), errors='coerce')
                    if fpts == 0:
                        # Player has no MLB production, use only prospect value
                        return prospect_val
            
            return mvp_val + prospect_val
        
        def get_player_value_breakdown(player_name):
            """Get detailed breakdown of player value"""
            mvp_val = mvp_values.get(player_name, 0)
            prospect_val = prospect_values.get(player_name, 0)
            
            # Apply the same logic as get_player_value
            effective_mvp_val = mvp_val
            mvp_details = ""
            zero_fpts_override = False
            reduced_prospect_override = False
            
            if mvp_val > 0 and prospect_val > 0:
                # Check if player has fantasy points in MVP data
                player_row = mvp_data[mvp_data['Player'] == player_name]
                if not player_row.empty:
                    row = player_row.iloc[0]
                    fpts = pd.to_numeric(row.get('FPts', 0), errors='coerce')
                    fpg = pd.to_numeric(row.get('FP/G', 0), errors='coerce')
                    
                    if fpts == 0:
                        # Player has no MLB production, ignore MVP value
                        effective_mvp_val = 0
                        zero_fpts_override = True
                        mvp_details = "No MLB FPts - using prospect value only"
                    else:
                        # Player has MLB production - prospect score was reduced
                        reduced_prospect_override = True
                        mvp_details = f"FPts: {fpts:.1f}, FP/G: {fpg:.1f} (prospect score reduced)"
            elif player_name in mvp_values and mvp_val > 0:
                # Get details for MVP-only players
                player_row = mvp_data[mvp_data['Player'] == player_name]
                if not player_row.empty:
                    row = player_row.iloc[0]
                    fpts = pd.to_numeric(row.get('FPts', 0), errors='coerce')
                    fpg = pd.to_numeric(row.get('FP/G', 0), errors='coerce')
                    mvp_details = f"FPts: {fpts:.1f}, FP/G: {fpg:.1f}"
            
            total_val = effective_mvp_val + prospect_val
            
            # Determine primary source
            if zero_fpts_override:
                source = 'Prospect (MLB inactive)'
            elif effective_mvp_val > prospect_val:
                source = 'MLB'
            elif prospect_val > 0:
                source = 'Prospect'
            else:
                source = 'Unknown'
            
            return {
                'mvp_value': effective_mvp_val,
                'prospect_value': prospect_val,
                'total_value': total_val,
                'source': source,
                'details': mvp_details
            }
        
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
                    colors = get_team_colors(team)
                    
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, {colors['primary']} 0%, {colors['secondary']} 100%);
                        border-radius: 10px;
                        padding: 1rem;
                        margin-bottom: 10px;
                        color: white;
                    ">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <span style="font-size: 1.2rem; font-weight: bold;">#{i+1} {team}</span>
                            </div>
                            <div style="text-align: right;">
                                <div style="font-size: 1.1rem; font-weight: bold;">+{stats['total_value']:.1f} pts</div>
                                <div style="font-size: 0.9rem; opacity: 0.8;">{stats['trade_count']} trades</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.write("### 🔻 Biggest Trade Losers")
            for i, (team, stats) in enumerate(sorted_teams[-5:]):
                if stats['total_value'] < 0:
                    colors = get_team_colors(team)
                    
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, {colors['primary']} 0%, {colors['secondary']} 100%);
                        border-radius: 10px;
                        padding: 1rem;
                        margin-bottom: 10px;
                        color: white;
                        opacity: 0.8;
                    ">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <span style="font-size: 1.2rem; font-weight: bold;">#{len(sorted_teams)-4+i} {team}</span>
                            </div>
                            <div style="text-align: right;">
                                <div style="font-size: 1.1rem; font-weight: bold;">{stats['total_value']:.1f} pts</div>
                                <div style="font-size: 0.9rem; opacity: 0.8;">{stats['trade_count']} trades</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
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
                    winner_colors = get_team_colors(winner)
                    loser_colors = get_team_colors(loser)
                    
                    st.write(f"### Trade #{i+1}: {trade['date'].strftime('%B %d, %Y')}")
                    
                    # Team comparison with styling
                    col1, col2, col3 = st.columns([5, 1, 5])
                    
                    with col1:
                        st.markdown(f"""
                        <div style="
                            background: linear-gradient(135deg, {winner_colors['primary']} 0%, {winner_colors['secondary']} 100%);
                            border-radius: 10px;
                            padding: 1rem;
                            color: white;
                            text-align: center;
                        ">
                            <h4 style="margin: 0; color: white;">🏆 WINNER</h4>
                            <h3 style="margin: 0.5rem 0; color: white;">{winner}</h3>
                            <div style="font-size: 1.2rem; font-weight: bold;">+{trade['team_values'][winner]:.1f} pts</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Show what winner received
                        st.write("**Received:**")
                        received_items = [item for item in trade['trade_details'][winner] if item['direction'] == 'received']
                        winner_received_total = 0
                        for item in received_items:
                            winner_received_total += item['value']
                            if "Draft Pick" in item['item']:
                                st.write(f"• {item['item']} - {item['value']:.1f} pts")
                            elif "Budget Amount" in item['item']:
                                st.write(f"• {item['item']} - {item['value']:.1f} pts")
                            else:
                                # Show player breakdown
                                breakdown = get_player_value_breakdown(item['item'])
                                mvp_part = f"MVP: {breakdown['mvp_value']:.1f}" if breakdown['mvp_value'] > 0 else ""
                                prospect_part = f"Prospect: {breakdown['prospect_value']:.1f}" if breakdown['prospect_value'] > 0 else ""
                                parts = [p for p in [mvp_part, prospect_part] if p]
                                detail = f" ({', '.join(parts)})" if parts else ""
                                st.write(f"• {item['item']} - {item['value']:.1f} pts{detail}")
                        
                        # Show what winner gave up
                        st.write("**Gave Up:**")
                        gave_items = [item for item in trade['trade_details'][winner] if item['direction'] == 'gave']
                        winner_gave_total = 0
                        for item in gave_items:
                            winner_gave_total += item['value']
                            if "Draft Pick" in item['item']:
                                st.write(f"• {item['item']} - {item['value']:.1f} pts")
                            elif "Budget Amount" in item['item']:
                                st.write(f"• {item['item']} - {item['value']:.1f} pts")
                            else:
                                # Show player breakdown
                                breakdown = get_player_value_breakdown(item['item'])
                                mvp_part = f"MVP: {breakdown['mvp_value']:.1f}" if breakdown['mvp_value'] > 0 else ""
                                prospect_part = f"Prospect: {breakdown['prospect_value']:.1f}" if breakdown['prospect_value'] > 0 else ""
                                parts = [p for p in [mvp_part, prospect_part] if p]
                                detail = f" ({', '.join(parts)})" if parts else ""
                                st.write(f"• {item['item']} - {item['value']:.1f} pts{detail}")
                        
                        st.write(f"**Net Value: +{winner_received_total - winner_gave_total:.1f} pts**")
                    
                    with col2:
                        st.markdown("<div style='text-align: center; padding-top: 3rem; font-size: 2rem;'>⚖️</div>", unsafe_allow_html=True)
                    
                    with col3:
                        st.markdown(f"""
                        <div style="
                            background: linear-gradient(135deg, {loser_colors['primary']} 0%, {loser_colors['secondary']} 100%);
                            border-radius: 10px;
                            padding: 1rem;
                            color: white;
                            text-align: center;
                            opacity: 0.7;
                        ">
                            <h4 style="margin: 0; color: white;">📉 LOSER</h4>
                            <h3 style="margin: 0.5rem 0; color: white;">{loser}</h3>
                            <div style="font-size: 1.2rem; font-weight: bold;">{trade['team_values'][loser]:.1f} pts</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Show what loser received
                        st.write("**Received:**")
                        loser_received_items = [item for item in trade['trade_details'][loser] if item['direction'] == 'received']
                        loser_received_total = 0
                        for item in loser_received_items:
                            loser_received_total += item['value']
                            if "Draft Pick" in item['item']:
                                st.write(f"• {item['item']} - {item['value']:.1f} pts")
                            elif "Budget Amount" in item['item']:
                                st.write(f"• {item['item']} - {item['value']:.1f} pts")
                            else:
                                # Show player breakdown
                                breakdown = get_player_value_breakdown(item['item'])
                                mvp_part = f"MVP: {breakdown['mvp_value']:.1f}" if breakdown['mvp_value'] > 0 else ""
                                prospect_part = f"Prospect: {breakdown['prospect_value']:.1f}" if breakdown['prospect_value'] > 0 else ""
                                parts = [p for p in [mvp_part, prospect_part] if p]
                                detail = f" ({', '.join(parts)})" if parts else ""
                                st.write(f"• {item['item']} - {item['value']:.1f} pts{detail}")
                        
                        # Show what loser gave up
                        st.write("**Gave Up:**")
                        gave_items = [item for item in trade['trade_details'][loser] if item['direction'] == 'gave']
                        loser_gave_total = 0
                        for item in gave_items:
                            loser_gave_total += item['value']
                            if "Draft Pick" in item['item']:
                                st.write(f"• {item['item']} - {item['value']:.1f} pts")
                            elif "Budget Amount" in item['item']:
                                st.write(f"• {item['item']} - {item['value']:.1f} pts")
                            else:
                                # Show player breakdown
                                breakdown = get_player_value_breakdown(item['item'])
                                mvp_part = f"MVP: {breakdown['mvp_value']:.1f}" if breakdown['mvp_value'] > 0 else ""
                                prospect_part = f"Prospect: {breakdown['prospect_value']:.1f}" if breakdown['prospect_value'] > 0 else ""
                                parts = [p for p in [mvp_part, prospect_part] if p]
                                detail = f" ({', '.join(parts)})" if parts else ""
                                st.write(f"• {item['item']} - {item['value']:.1f} pts{detail}")
                        
                        st.write(f"**Net Value: {loser_received_total - loser_gave_total:.1f} pts**")
                    
                    # Summary
                    st.markdown(f"""
                    <div style="
                        background: rgba(255, 255, 255, 0.1);
                        border-radius: 5px;
                        padding: 0.5rem;
                        text-align: center;
                        margin: 1rem 0;
                    ">
                        <strong>Value Difference: {trade['value_difference']:.1f} points</strong>
                    </div>
                    """, unsafe_allow_html=True)
                    
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