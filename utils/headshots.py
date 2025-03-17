import requests
from bs4 import BeautifulSoup
from pybaseball import playerid_lookup
import logging
from typing import Optional

def get_player_headshot(first_name: str, last_name: str) -> Optional[str]:
    """
    Get player headshot URL from Baseball Reference.
    Returns None if headshot cannot be found.
    """
    try:
        # Lookup the player ID
        data = playerid_lookup(last_name, first_name)
        if data.empty:
            return None
            
        player_id = data.key_bbref.iloc[0]
        first_letter = player_id[0]
        url = f"https://www.baseball-reference.com/players/{first_letter}/{player_id}.shtml"
        
        response = requests.get(url)
        if response.status_code != 200:
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        media_div = soup.find('div', class_='media-item multiple')
        
        if media_div:
            img_tags = media_div.find_all('img')
            if img_tags:
                return img_tags[0]['src']  # Return first headshot URL
                
        return None
        
    except Exception as e:
        logging.error(f"Error fetching headshot for {first_name} {last_name}: {str(e)}")
        return None
