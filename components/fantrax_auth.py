import streamlit as st
import requests
from typing import Dict, Optional, Tuple
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def login_form() -> Tuple[bool, str]:
    """
    Display Fantrax login form and handle authentication
    Returns a tuple of (success, message)
    """
    st.subheader("🔐 Fantrax Login")
    
    with st.form("fantrax_login"):
        username = st.text_input("Email or Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Log In")
        
        if submit:
            if not username or not password:
                return False, "Please enter both username and password"
            
            success, message, session_data = authenticate_fantrax(username, password)
            if success:
                # Store session data in streamlit session state
                st.session_state.fantrax_auth = session_data
                st.session_state.fantrax_logged_in = True
                st.session_state.fantrax_username = username
                return True, "Login successful!"
            else:
                return False, message
    
    return False, ""

def auto_login() -> Tuple[bool, str]:
    """
    Automatically authenticate using credentials from .env file
    Returns a tuple of (success, message)
    """
    # Get credentials from .env
    username = os.getenv("FANTRAX_EMAIL")
    password = os.getenv("FANTRAX_PASSWORD")
    
    if not username or not password:
        return False, "No credentials found in .env file"
    
    success, message, session_data = authenticate_fantrax(username, password)
    if success:
        # Store session data in streamlit session state
        st.session_state.fantrax_auth = session_data
        st.session_state.fantrax_logged_in = True
        st.session_state.fantrax_username = username
        return True, "Auto-login successful!"
    else:
        return False, message

def authenticate_fantrax(username: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
    """
    Authenticate with Fantrax and return session cookies and tokens
    Returns a tuple of (success, message, session_data)
    """
    try:
        # Create a session to maintain cookies
        session = requests.Session()
        
        # Step 1: First request to get CSRF token and initial cookies
        initial_response = session.get(
            "https://www.fantrax.com/login", 
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )
        
        if initial_response.status_code != 200:
            return False, f"Failed to connect to Fantrax. Status code: {initial_response.status_code}", None
        
        # Step 2: Login request
        login_data = {
            "username": username,
            "password": password,
            "keepMeLoggedIn": True  # Useful for maintaining longer sessions
        }
        
        login_response = session.post(
            "https://www.fantrax.com/fxea/account/login",
            json=login_data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "application/json"
            }
        )
        
        # Check if login was successful
        if login_response.status_code != 200:
            return False, f"Login failed. Status code: {login_response.status_code}", None
        
        try:
            login_json = login_response.json()
            if login_json.get("errorMessage"):
                return False, login_json.get("errorMessage", "Login failed"), None
        except:
            pass  # Response might not be JSON
        
        # Step 3: Verify we're logged in by making a simple authenticated request
        verify_response = session.get(
            "https://www.fantrax.com/fxea/user/getMyProfile",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "application/json"
            }
        )
        
        if verify_response.status_code != 200:
            return False, "Authentication verification failed", None
        
        # Extract and store all relevant cookies
        cookies = {cookie.name: cookie.value for cookie in session.cookies}
        
        # Store headers that might be needed for future requests
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json"
        }
        
        # Return session data
        session_data = {
            "cookies": cookies,
            "headers": headers
        }
        
        return True, "Login successful", session_data
        
    except Exception as e:
        return False, f"Login error: {str(e)}", None

def logout():
    """Remove authentication data from session state"""
    if "fantrax_auth" in st.session_state:
        del st.session_state.fantrax_auth
    if "fantrax_logged_in" in st.session_state:
        del st.session_state.fantrax_logged_in
    if "fantrax_username" in st.session_state:
        del st.session_state.fantrax_username
    
    return True

def is_authenticated() -> bool:
    """Check if user is authenticated"""
    return st.session_state.get("fantrax_logged_in", False)

def get_session_data() -> Optional[Dict]:
    """Get stored session data if available"""
    return st.session_state.get("fantrax_auth", None)

def render_auth_status():
    """Render current authentication status"""
    # If not already authenticated, try auto-login
    if not is_authenticated():
        # Check if this is the first run
        if "attempted_auto_login" not in st.session_state:
            st.session_state.attempted_auto_login = True
            success, message = auto_login()
            if success:
                st.success(message)
                st.rerun()  # Refresh after successful auto-login
            elif st.session_state.get('debug_mode', False):
                st.warning(f"Auto-login failed: {message}")
    
    # Show current authentication status
    if is_authenticated():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.success(f"Logged in as {st.session_state.get('fantrax_username', 'User')}")
        with col2:
            if st.button("Logout"):
                logout()
                # Also clear the auto-login attempt flag
                if "attempted_auto_login" in st.session_state:
                    del st.session_state.attempted_auto_login
                st.rerun()
    else:
        # Only show manual login form if auto-login failed
        if st.session_state.get("attempted_auto_login", False):
            success, message = login_form()
            if message:
                if success:
                    st.success(message)
                    st.rerun()  # Refresh the page after successful login
                else:
                    st.error(message)