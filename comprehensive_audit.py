#!/usr/bin/env python3
"""
Comprehensive audit to find all remaining prospect team mismatches
"""

import pandas as pd
from components.prospects import normalize_name
from utils import fetch_api_data

def comprehensive_audit():
    """Run comprehensive audit and fix all remaining issues"""
    
    print("🔍 Running comprehensive prospect audit...")
    
    # Load all data
    prospect_import = pd.read_csv("attached_assets/ABL-Import.csv")
    prospect_import['clean_name'] = prospect_import['Name'].fillna('').astype(str).apply(normalize_name)
    
    trades = pd.read_csv("attached_assets/Fantrax-Transaction-History-Trades-ABL Season 5.csv")
    
    # Get current roster data
    data = fetch_api_data()
    roster_data = data['roster_data']
    roster_data['clean_name'] = roster_data['player_name'].fillna('').astype(str).apply(normalize_name)
    
    # Create current team mapping
    current_teams = {}
    for _, player in roster_data.iterrows():
        team = player.get('team_name', player.get('team', 'Unknown'))
        current_teams[player['clean_name']] = team
    
    print(f"Loaded {len(prospect_import)} prospects and {len(current_teams)} current roster players")
    
    # Find all mismatches
    mismatches = []
    traded_away = []
    
    for _, prospect in prospect_import.iterrows():
        name = prospect['Name']
        clean_name = prospect['clean_name']
        listed_team = prospect['MLB Team']
        
        if clean_name in current_teams:
            current_team = current_teams[clean_name]
            if current_team != listed_team:
                mismatches.append({
                    'name': name,
                    'listed_team': listed_team,
                    'current_team': current_team,
                    'rank': prospect.get('Rank', 999)
                })
        else:
            # Check if player was traded away
            trade_matches = trades[trades['Player'].apply(lambda x: normalize_name(str(x))) == clean_name]
            if len(trade_matches) > 0:
                latest_trade = trade_matches.iloc[-1]
                traded_away.append({
                    'name': name,
                    'listed_team': listed_team,
                    'traded_to': latest_trade['To'],
                    'trade_date': latest_trade['Date (EDT)']
                })
    
    print(f"\n🚨 Found {len(mismatches)} team assignment mismatches:")
    if mismatches:
        print("-" * 80)
        for mismatch in sorted(mismatches, key=lambda x: x['rank'])[:20]:  # Show top 20
            print(f"{mismatch['name']:<25} {mismatch['listed_team']:<18} → {mismatch['current_team']}")
    
    print(f"\n📤 Found {len(traded_away)} players traded away (not in current rosters):")
    if traded_away:
        print("-" * 80)
        for trade in traded_away[:10]:  # Show top 10
            print(f"{trade['name']:<25} listed as {trade['listed_team']:<12} → traded to {trade['traded_to']}")
    
    # Fix mismatches
    if mismatches:
        print(f"\n🔧 Fixing {len(mismatches)} mismatches...")
        updated = 0
        for mismatch in mismatches:
            idx = prospect_import[prospect_import['Name'] == mismatch['name']].index[0]
            prospect_import.at[idx, 'MLB Team'] = mismatch['current_team']
            updated += 1
        
        # Remove the helper column before saving
        prospect_import.drop('clean_name', axis=1, inplace=True)
        prospect_import.to_csv("attached_assets/ABL-Import.csv", index=False)
        print(f"✅ Fixed {updated} prospect team assignments")
    
    return len(mismatches), len(traded_away)

if __name__ == "__main__":
    comprehensive_audit()