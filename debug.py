import traceback
import streamlit as st
import os
from api_client import FantraxAPI
from utils import fetch_api_data

print("Debugging startup...")
print(f"Current dir: {os.getcwd()}")
print(f"Env vars: FANTRAX_USERNAME={os.environ.get('FANTRAX_USERNAME')}, FANTRAX_PASSWORD={os.environ.get('FANTRAX_PASSWORD') and '***'}")

try:
    # Test 1: Check API Client directly
    print("\n--- Test 1: API Client Direct Test ---")
    api = FantraxAPI()
    print("API initialized")
    mock_data = api._get_mock_data("getMatchups")
    print(f"Mock data: {len(mock_data) if isinstance(mock_data, list) else 'Not a list'}")
    
    # Test 2: Try fetching data via utils function
    print("\n--- Test 2: Utils fetch_api_data Test ---")
    try:
        data = fetch_api_data()
        if data:
            print("Data fetched successfully")
            print(f"Keys in data: {list(data.keys())}")
            if 'matchups_data' in data:
                print(f"Matchups data: {len(data['matchups_data']) if data['matchups_data'] else 'None'}")
            else:
                print("No matchups_data key in data")
        else:
            print("fetch_api_data returned None")
    except Exception as e:
        print(f"Error in fetch_api_data: {str(e)}")
        print(traceback.format_exc())
    
except Exception as e:
    print('ERROR:', str(e))
    print(traceback.format_exc())