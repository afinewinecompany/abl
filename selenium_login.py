import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def save_credentials(username, password, league_id):
    """Save credentials to .env file"""
    with open(".env", "w") as f:
        f.write(f"FANTRAX_USERNAME={username}\n")
        f.write(f"FANTRAX_PASSWORD={password}\n")
        f.write(f"LEAGUE_ID={league_id}\n")
    
    logger.info("Credentials saved to .env file")

def fantrax_login(username, password, league_id, show_progress=None):
    """
    Login to Fantrax and extract authentication token
    
    Args:
        username: Fantrax username
        password: Fantrax password
        league_id: Fantrax league ID
        show_progress: Optional callback function to update progress
    
    Returns:
        bool: True if login successful and token saved, False otherwise
    """
    if show_progress:
        show_progress("Setting up browser...")
    
    # Configure Chrome options for headless mode
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    
    try:
        if show_progress:
            show_progress("Starting browser...")
        
        # Start Chrome browser
        driver = webdriver.Chrome(options=options)
        
        # Navigate to Fantrax login page
        if show_progress:
            show_progress("Navigating to Fantrax login page...")
        
        driver.get("https://www.fantrax.com/fantasy/login")
        time.sleep(2)
        
        # Find and fill in login form
        if show_progress:
            show_progress("Entering credentials...")
        
        # Wait for login form to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "loginUsername"))
        )
        
        username_field = driver.find_element(By.ID, "loginUsername")
        password_field = driver.find_element(By.ID, "loginPassword")
        
        username_field.clear()
        password_field.clear()
        
        username_field.send_keys(username)
        password_field.send_keys(password)
        
        # Submit form
        if show_progress:
            show_progress("Logging in...")
        
        password_field.send_keys(Keys.RETURN)
        
        # Wait for login to complete
        time.sleep(3)
        
        # Navigate to league page
        if show_progress:
            show_progress("Navigating to league page...")
        
        matchup_url = f"https://www.fantrax.com/fantasy/league/{league_id}/livescoring?mobileMatchupView=false"
        driver.get(matchup_url)
        time.sleep(2)
        
        # Extract token from local storage
        if show_progress:
            show_progress("Extracting authentication token...")
        
        token = driver.execute_script("return window.localStorage.getItem('fx.token');")
        
        # Close browser
        driver.quit()
        
        # Save token if found
        if token:
            if show_progress:
                show_progress("Saving token...")
            
            # Save credentials first
            save_credentials(username, password, league_id)
            
            # Then append token
            with open(".env", "a") as f:
                f.write(f"FANTRAX_TOKEN={token}\n")
            
            logger.info("✅ Token saved to .env")
            
            if show_progress:
                show_progress("Login successful!")
            
            return True
        else:
            logger.error("❌ Login failed. No token found.")
            
            if show_progress:
                show_progress("Login failed. No token found.")
            
            return False
    
    except Exception as e:
        logger.error(f"❌ Error during login: {e}")
        
        if show_progress:
            show_progress(f"Error during login: {e}")
        
        return False

def streamlit_login_form():
    """Streamlit interface for Fantrax login"""
    st.header("🔐 Fantrax Authentication")
    
    with st.form("fantrax_login"):
        username = st.text_input("Username", value=os.getenv("FANTRAX_USERNAME", ""))
        password = st.text_input("Password", type="password", value=os.getenv("FANTRAX_PASSWORD", ""))
        league_id = st.text_input("League ID", value=os.getenv("LEAGUE_ID", ""))
        
        submitted = st.form_submit_button("Login")
        
        if submitted:
            progress_placeholder = st.empty()
            
            def update_progress(message):
                progress_placeholder.info(message)
            
            result = fantrax_login(username, password, league_id, update_progress)
            
            if result:
                st.success("Login successful! Token has been saved.")
                # Reload the page to use the new token
                st.rerun()
            else:
                st.error("Login failed. Please check your credentials and try again.")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Login to Fantrax")
    parser.add_argument("--username", help="Fantrax username")
    parser.add_argument("--password", help="Fantrax password")
    parser.add_argument("--league_id", help="Fantrax league ID")
    
    args = parser.parse_args()
    
    username = args.username or os.getenv("FANTRAX_USERNAME")
    password = args.password or os.getenv("FANTRAX_PASSWORD")
    league_id = args.league_id or os.getenv("LEAGUE_ID")
    
    if not all([username, password, league_id]):
        print("Please provide username, password, and league ID")
        exit(1)
    
    fantrax_login(username, password, league_id)