import pandas as pd
import math

# Load MVP data
mvp_data = pd.read_csv("attached_assets/MVP-Player-List.csv")

def calculate_comprehensive_player_value(row):
    """Calculate comprehensive player value using all MVP metrics"""
    # Extract values with safe conversion
    fpts = pd.to_numeric(row.get('FPts', 0), errors='coerce') or 0
    fpg = pd.to_numeric(row.get('FP/G', 0), errors='coerce') or 0
    age = pd.to_numeric(row.get('Age', 30), errors='coerce') or 30
    salary = pd.to_numeric(row.get('Salary', 0), errors='coerce') or 0
    contract = row.get('Contract', '1st')
    position = row.get('Position', 'OF')
    
    # Set max values (from the data)
    max_fpts = mvp_data['FPts'].max() if 'FPts' in mvp_data.columns else 400
    max_fpg = mvp_data['FP/G'].max() if 'FP/G' in mvp_data.columns else 25
    max_salary = mvp_data['Salary'].max() if 'Salary' in mvp_data.columns else 70
    
    # Fantasy Points component (45% weight)
    fpts_score = min(1.0, fpts / max_fpts) if max_fpts > 0 else 0
    
    # Fantasy Points per Game component (25% weight)
    fpg_score = min(1.0, fpg / max_fpg) if max_fpg > 0 else 0
    
    # Position value component (5% weight)
    position_values = {
        'C': 1.0,      # Catcher - most scarce
        'SS': 0.9,     # Shortstop
        '2B': 0.8,     # Second base
        '3B': 0.7,     # Third base
        '1B': 0.6,     # First base
        'CF': 0.7,     # Center field
        'LF': 0.5,     # Left field
        'RF': 0.5,     # Right field
        'OF': 0.5,     # Outfield
        'DH': 0.4,     # DH
        'SP': 0.9,     # Starting pitcher
        'RP': 0.6,     # Relief pitcher
        'UT': 0.8      # Utility
    }
    
    pos_score = 0
    if position:
        positions = [p.strip() for p in str(position).split(',')]
        pos_score = max([position_values.get(pos, 0.5) for pos in positions])
    
    # Contract value component (10% weight)
    contract_values = {'2050': 1.0, '2045': 0.9, '2040': 0.8, '2035': 0.7, '2029': 0.6, '2028': 0.5, '2027': 0.4, '2026': 0.3, '2025': 0.2, '1st': 0.1}
    contract_score = contract_values.get(str(contract), 0.1)
    
    # Age factor (10% weight) - younger is better, peak around 26-28
    if age <= 35:
        age_score = max(0, (35 - age) / 10)
    else:
        age_score = 0
    
    # Salary efficiency (5% weight)
    salary_efficiency = 1.0 - (salary / max_salary) if max_salary > 0 else 0.5
    
    # Combine all components
    total_score = (
        fpts_score * 0.45 +      # Fantasy points (45%)
        fpg_score * 0.25 +       # Points per game (25%)
        pos_score * 0.05 +       # Position value
        contract_score * 0.10 +  # Contract value
        age_score * 0.10 +       # Age factor
        salary_efficiency * 0.05 # Salary efficiency
    )
    
    # Scale to 0-100 range
    return total_score * 100

# Calculate raw MVP values
mvp_raw_values = {}
for _, row in mvp_data.iterrows():
    player_name = row.get('Player', '')
    if player_name:
        mvp_raw_values[player_name] = calculate_comprehensive_player_value(row)

# Apply quadratic scaling
mvp_values = {}
if mvp_raw_values:
    max_value = max(mvp_raw_values.values())
    for player_name, raw_value in mvp_raw_values.items():
        normalized = raw_value / max_value if max_value > 0 else 0
        # Quadratic scaling
        scaled = normalized ** 2
        mvp_values[player_name] = scaled * max_value

# Check for outliers first
print("INVESTIGATING DATA QUALITY:")
print("=" * 60)
raw_sorted = sorted(mvp_raw_values.items(), key=lambda x: x[1], reverse=True)
print("Top 5 raw scores:")
for i, (player, score) in enumerate(raw_sorted[:5], 1):
    print(f"{i}. {player}: {score:.2f}")

print(f"\nLarge gap detected between #1 ({raw_sorted[0][1]:.2f}) and #2 ({raw_sorted[1][1]:.2f})")

# Check the problematic player's data
problem_player = raw_sorted[0][0]
player_row = mvp_data[mvp_data['Player'] == problem_player]
if not player_row.empty:
    print(f"\n{problem_player} data:")
    for col in ['FPts', 'FP/G', 'Age', 'Salary', 'Contract', 'Position']:
        print(f"  {col}: {player_row.iloc[0].get(col, 'N/A')}")

# Remove outlier and recalculate
print(f"\nRemoving outlier '{problem_player}' and recalculating...")
filtered_raw_values = {k: v for k, v in mvp_raw_values.items() if k != problem_player}

# Apply quadratic scaling to filtered data
filtered_mvp_values = {}
if filtered_raw_values:
    max_value = max(filtered_raw_values.values())
    for player_name, raw_value in filtered_raw_values.items():
        normalized = raw_value / max_value if max_value > 0 else 0
        scaled = normalized ** 2
        filtered_mvp_values[player_name] = scaled * max_value

# Get top 20 players by quadratic-scaled values (without outlier)
top_players = sorted(filtered_mvp_values.items(), key=lambda x: x[1], reverse=True)[:20]

print("\nTOP 20 PLAYERS WITH QUADRATIC SCALING (OUTLIER REMOVED):")
print("=" * 70)
for i, (player, score) in enumerate(top_players, 1):
    raw_score = filtered_raw_values.get(player, 0)
    print(f"{i:2d}. {player:25} | Raw: {raw_score:6.2f} | Scaled: {score:6.2f}")

print("\n" + "=" * 70)
print(f"Max raw value (filtered): {max(filtered_raw_values.values()):.2f}")
print(f"Max scaled value (filtered): {max(filtered_mvp_values.values()):.2f}")
print(f"Scaling effect: Top player gets {max(filtered_mvp_values.values()) / max(filtered_raw_values.values()):.3f}x of original")