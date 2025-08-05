#!/usr/bin/env python3
"""
Fix prospect team assignments based on current roster data
"""

import pandas as pd
from components.prospects import normalize_name
from utils import fetch_api_data

def fix_prospect_teams():
    """Update prospect team assignments to match current rosters"""
    
    print("🔧 Fixing prospect team assignments...")
    
    # Load current data
    prospect_import = pd.read_csv("attached_assets/ABL-Import.csv")
    prospect_import['clean_name'] = prospect_import['Name'].fillna('').astype(str).apply(normalize_name)
    
    # Get current roster data
    data = fetch_api_data()
    roster_data = data['roster_data']
    roster_data['clean_name'] = roster_data['player_name'].fillna('').astype(str).apply(normalize_name)
    
    # Create mapping of player clean_name to current team
    current_teams = {}
    for _, player in roster_data.iterrows():
        if 'team_name' in player:
            current_teams[player['clean_name']] = player['team_name']
        elif 'team' in player:
            current_teams[player['clean_name']] = player['team']
    
    # Update prospect data
    updated_count = 0
    for idx, prospect in prospect_import.iterrows():
        clean_name = prospect['clean_name']
        if clean_name in current_teams:
            current_team = current_teams[clean_name]
            if prospect['MLB Team'] != current_team:
                print(f"Updating {prospect['Name']}: {prospect['MLB Team']} → {current_team}")
                prospect_import.at[idx, 'MLB Team'] = current_team
                updated_count += 1
    
    # Save updated data
    if updated_count > 0:
        prospect_import.drop('clean_name', axis=1, inplace=True)  # Remove helper column
        prospect_import.to_csv("attached_assets/ABL-Import.csv", index=False)
        print(f"✅ Updated {updated_count} prospect team assignments")
        return True
    else:
        print("ℹ️ No updates needed")
        return False

if __name__ == "__main__":
    fix_prospect_teams()