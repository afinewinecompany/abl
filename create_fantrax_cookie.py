import pickle
import time
import os
from dotenv import load_dotenv
import streamlit as st
import sys

# Load environment variables
load_dotenv()

def main():
    st.set_page_config(page_title="Fantrax Authentication", layout="wide")
    
    st.title("Fantrax Authentication")
    st.write("""
    ## Creating Authentication Cookie
    
    To use the Fantrax API, we need to create an authentication cookie.
    Unfortunately, Fantrax doesn't provide a direct API authentication method, so we need to use a workaround.
    
    ### Instructions:
    
    1. Install required packages:
       ```
       pip install selenium webdriver-manager
       ```
       
    2. Run the code below on your local computer (not on this Streamlit app):
       ```python
       import pickle
       import time
       from selenium import webdriver
       from selenium.webdriver.chrome.service import Service
       from selenium.webdriver.chrome.options import Options
       from webdriver_manager.chrome import ChromeDriverManager

       service = Service(ChromeDriverManager().install())

       options = Options()
       options.add_argument("--window-size=1920,1600")
       options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36")

       with webdriver.Chrome(service=service, options=options) as driver:
           driver.get("https://www.fantrax.com/login")
           time.sleep(30)  # Give yourself time to log in manually
           pickle.dump(driver.get_cookies(), open("fantraxloggedin.cookie", "wb"))
       ```
       
    3. When the Chrome browser opens, log in to your Fantrax account
    4. Wait 30 seconds for the cookie file to be created
    5. Upload the created 'fantraxloggedin.cookie' file here:
    """)
    
    uploaded_file = st.file_uploader("Upload fantraxloggedin.cookie file", type=["cookie"])
    
    if uploaded_file is not None:
        try:
            # Save the uploaded cookie file
            with open("fantraxloggedin.cookie", "wb") as f:
                f.write(uploaded_file.getvalue())
            
            st.success("Cookie file uploaded successfully! You can now use the Fantrax API.")
            st.info("Please restart the application to apply the changes.")
            
        except Exception as e:
            st.error(f"Error saving cookie file: {str(e)}")

if __name__ == "__main__":
    main()