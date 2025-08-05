#!/usr/bin/env python3
"""
Audit script to identify prospect team assignment mismatches after trades
"""

import pandas as pd
import sys
from components.prospects import normalize_name

def audit_prospect_teams():
    """Audit prospect team assignments against current roster data"""
    
    print("🔍 Auditing prospect team assignments...")
    
    # Load prospect data
    try:
        prospect_import = pd.read_csv("attached_assets/ABL-Import.csv", na_values=['NA', ''], keep_default_na=True)
        prospect_import['clean_name'] = prospect_import['Name'].fillna('').astype(str).apply(normalize_name)
        print(f"✅ Loaded {len(prospect_import)} prospects from ABL-Import.csv")
    except Exception as e:
        print(f"❌ Error loading prospect data: {e}")
        return
    
    # Load trade history
    try:
        trades = pd.read_csv("attached_assets/Fantrax-Transaction-History-Trades-ABL Season 5.csv")
        print(f"✅ Loaded {len(trades)} trade records")
    except Exception as e:
        print(f"❌ Error loading trade data: {e}")
        return
    
    # Load current roster data (simulated from API fetch)
    try:
        from utils import fetch_api_data
        data = fetch_api_data()
        if data and 'roster_data' in data:
            roster_data = data['roster_data']
            roster_data['clean_name'] = roster_data['player_name'].fillna('').astype(str).apply(normalize_name)
            print(f"✅ Loaded {len(roster_data)} players from current rosters")
        else:
            print("❌ Could not fetch current roster data")
            return
    except Exception as e:
        print(f"❌ Error fetching roster data: {e}")
        return
    
    print("\n" + "="*60)
    print("PROSPECT TEAM ASSIGNMENT AUDIT")
    print("="*60)
    
    mismatches = []
    
    # Check each prospect against current roster data
    for _, prospect in prospect_import.iterrows():
        name = prospect['Name']
        clean_name = prospect['clean_name']
        listed_team = prospect['MLB Team']
        
        # Find this player in current roster data
        current_roster_matches = roster_data[roster_data['clean_name'] == clean_name]
        
        if len(current_roster_matches) > 0:
            # Check what columns are available
            first_match = current_roster_matches.iloc[0]
            if 'team_name' in first_match:
                current_team = first_match['team_name']
            elif 'team' in first_match:
                current_team = first_match['team']
            else:
                print(f"Available columns: {list(first_match.index)}")
                continue
            
            if current_team != listed_team:
                mismatches.append({
                    'rank': prospect['Rank'],
                    'name': name,
                    'listed_team': listed_team,
                    'current_team': current_team,
                    'score': prospect['Score']
                })
        else:
            # Player not found in current rosters
            print(f"⚠️  Player not found in current rosters: {name} (listed as {listed_team})")
    
    if mismatches:
        print(f"\n🚨 Found {len(mismatches)} team assignment mismatches:")
        print("-" * 80)
        print(f"{'RANK':<6} {'PLAYER NAME':<25} {'LISTED TEAM':<18} {'CURRENT TEAM':<18} {'SCORE':<8}")
        print("-" * 80)
        
        for mismatch in sorted(mismatches, key=lambda x: x['rank']):
            print(f"{mismatch['rank']:<6} {mismatch['name']:<25} {mismatch['listed_team']:<18} {mismatch['current_team']:<18} {mismatch['score']:<8.2f}")
    else:
        print("\n✅ No team assignment mismatches found!")
    
    # Check for recent trades involving top prospects
    print(f"\n📊 Checking recent trades involving top 50 prospects...")
    top_50_names = set(prospect_import[prospect_import['Rank'] <= 50]['clean_name'])
    
    recent_prospect_trades = []
    for _, trade in trades.iterrows():
        player_name = trade['Player']
        clean_trade_name = normalize_name(str(player_name))
        
        if clean_trade_name in top_50_names:
            recent_prospect_trades.append({
                'player': player_name,
                'from_team': trade['From'],
                'to_team': trade['To'],
                'date': trade['Date (EDT)']
            })
    
    if recent_prospect_trades:
        print(f"\n🔄 Found {len(recent_prospect_trades)} recent trades involving top 50 prospects:")
        print("-" * 70)
        print(f"{'PLAYER':<25} {'FROM':<18} {'TO':<18} {'DATE':<12}")
        print("-" * 70)
        
        for trade in recent_prospect_trades:
            print(f"{trade['player']:<25} {trade['from_team']:<18} {trade['to_team']:<18} {trade['date'][:12]}")
    else:
        print("No recent trades involving top 50 prospects found.")
    
    return mismatches

if __name__ == "__main__":
    audit_prospect_teams()