#!/usr/bin/env python3
"""
Fix specific prospect trades that were missed
"""

import pandas as pd
from components.prospects import normalize_name

def fix_specific_trades():
    """Fix specific traded players that were missed"""
    
    print("🔧 Fixing specific traded players...")
    
    # Load current data
    prospect_import = pd.read_csv("attached_assets/ABL-Import.csv")
    
    # Specific fixes based on trade history
    specific_fixes = [
        ("Aidan Smith", "Boston Red Sox"),      # Athletics → Boston Red Sox
        ("Bishop Letson", "Cleveland Guardians"), # Athletics → Cleveland Guardians  
        ("Luke Dickerson", "Houston Astros"),   # Athletics → Houston Astros
    ]
    
    updated_count = 0
    for player_name, correct_team in specific_fixes:
        # Find player in prospect data
        matches = prospect_import[prospect_import['Name'].apply(normalize_name) == normalize_name(player_name)]
        
        if len(matches) > 0:
            idx = matches.index[0]
            current_team = prospect_import.at[idx, 'MLB Team']
            
            if current_team != correct_team:
                print(f"Updating {player_name}: {current_team} → {correct_team}")
                prospect_import.at[idx, 'MLB Team'] = correct_team
                updated_count += 1
            else:
                print(f"✅ {player_name} already correctly assigned to {correct_team}")
        else:
            print(f"⚠️ Player not found: {player_name}")
    
    # Save updated data
    if updated_count > 0:
        prospect_import.to_csv("attached_assets/ABL-Import.csv", index=False)
        print(f"✅ Updated {updated_count} specific prospect assignments")
        return True
    else:
        print("ℹ️ No updates needed")
        return False

if __name__ == "__main__":
    fix_specific_trades()