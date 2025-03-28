import streamlit as st
import os
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def save_token(token, league_id):
    """Save token to .env file"""
    # First check if .env exists
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            env_content = f.read()
    else:
        env_content = ""
    
    # Write updated content with token
    with open(".env", "w") as f:
        # Remove existing FANTRAX_TOKEN line if it exists
        env_lines = [line for line in env_content.split("\n") if not line.startswith("FANTRAX_TOKEN=")]
        
        # Write back existing lines
        for line in env_lines:
            if line.strip():
                f.write(f"{line}\n")
        
        # Add league ID if not found
        if not any(line.startswith("LEAGUE_ID=") for line in env_lines):
            f.write(f"LEAGUE_ID={league_id}\n")
        
        # Add the token
        f.write(f"FANTRAX_TOKEN={token}\n")
    
    logger.info("✅ Token saved to .env file")
    return True

def streamlit_login_form():
    """Streamlit interface for manual Fantrax token entry"""
    st.markdown("""
    ### How to Get Your Fantrax Authentication Token
    
    Since Replit can't run a browser automatically, you'll need to get your Fantrax token manually:
    
    1. Open your browser and go to [Fantrax](https://www.fantrax.com)
    2. Log in to your account
    3. After logging in, press **F12** to open Developer Tools
    4. Go to the **Application** tab
    5. In the left sidebar, expand **Local Storage** and click on **https://www.fantrax.com**
    6. Look for the key named **fx.token** in the list
    7. Copy the value (it's a long string of characters)
    8. Paste it in the form below
    
    ![Instructions](https://i.imgur.com/jGXsQ9C.png)
    """)
    
    with st.form("fantrax_token_form"):
        token = st.text_input("Fantrax Token (from fx.token in Local Storage)", help="The token from your browser's Local Storage")
        league_id = st.text_input("League ID", value=os.getenv("LEAGUE_ID", ""), help="Your Fantrax league ID (found in the URL when viewing your league)")
        
        submitted = st.form_submit_button("Save Token")
        
        if submitted:
            if token and league_id:
                # Save the token
                if save_token(token, league_id):
                    st.success("✅ Authentication token saved successfully!")
                    
                    # Reload environment variables
                    load_dotenv()
                    
                    # Reload the page to use the new token
                    st.rerun()
            else:
                st.error("⚠️ Please provide both the token and league ID")

# Command-line functionality has been removed as it would require Selenium
# which does not work in the Replit environment

if __name__ == "__main__":
    print("This script is meant to be imported, not run directly.")
    print("Please use the Streamlit interface to authenticate with Fantrax.")