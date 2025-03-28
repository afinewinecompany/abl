import requests
import pandas as pd
import json
from urllib.parse import urlparse, parse_qs

def scrape_fantrax_standings(league_url: str) -> pd.DataFrame:
    """
    Fetch standings data from Fantrax API.

    Args:
        league_url (str): URL of the Fantrax API endpoint or league page
    
    Returns:
        pd.DataFrame: A DataFrame containing team standings data
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    # Extract league ID if this is a normal league URL
    if "leagueId=" not in league_url and "/fantasy/league/" in league_url:
        # Extract the league ID from URL like https://www.fantrax.com/fantasy/league/grx2lginm1v4p5jd/standings
        parts = league_url.split("/")
        for i, part in enumerate(parts):
            if part == "league" and i+1 < len(parts):
                league_id = parts[i+1].split("?")[0]  # Remove any query params
                # Construct the API URL
                league_url = f"https://www.fantrax.com/fxea/general/getStandings?leagueId={league_id}"
                break
    
    # If it's already an API URL, parse to ensure we have the league ID
    if "fxea/general/getStandings" in league_url:
        parsed_url = urlparse(league_url)
        query_params = parse_qs(parsed_url.query)
        if 'leagueId' not in query_params:
            raise Exception("No league ID found in the API URL.")
    
    # Make the request
    response = requests.get(league_url, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Failed to load data. Status code: {response.status_code}")
    
    try:
        # Parse the JSON response
        data = response.json()
        
        # Check if we got a valid response
        if not isinstance(data, dict):
            raise Exception("Invalid response format from Fantrax API.")
            
        # Extract standings data
        if 'standings' in data:
            standings_data = data['standings']
        else:
            # Try to find standings data in the response
            standings_data = None
            for key, value in data.items():
                if isinstance(value, list) and len(value) > 0 and 'teamId' in value[0]:
                    standings_data = value
                    break
            
            if not standings_data:
                raise Exception("Could not find standings data in the response.")
        
        # Create a pandas DataFrame
        df = pd.json_normalize(standings_data)
        
        # Clean up the column names - remove prefixes like 'stats.' if present
        df.columns = [col.replace('stats.', '') for col in df.columns]
        
        # Ensure we have the team name column
        if 'teamName' not in df.columns and 'name' in df.columns:
            df['teamName'] = df['name']
        
        # Ensure that team name is the first column
        if 'teamName' in df.columns and df.columns[0] != 'teamName':
            cols = ['teamName'] + [col for col in df.columns if col != 'teamName']
            df = df[cols]
            
        return df
        
    except (ValueError, json.JSONDecodeError):
        raise Exception("Failed to parse JSON response from Fantrax API.")