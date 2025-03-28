import streamlit as st
from typing import Any, Dict
import pandas as pd
from unified_api_client import unified_client

@st.cache_data
def fetch_unified_data():
    """
    Fetch all required data from the unified API client.
    Returns processed data or None if an error occurs.
    """
    try:
        return unified_client.fetch_all_data()
    except Exception as e:
        with st.sidebar:
            st.error(f"❌ Error loading data: {str(e)}")
        return None

def format_percentage(value: float) -> str:
    """Format percentage values"""
    return f"{value:.3f}%"

def safe_get(data: dict, key: str, default: Any = None) -> Any:
    """Safely get value from dictionary"""
    return data.get(key, default)

def calculate_stats(df: pd.DataFrame, column: str) -> Dict[str, float]:
    """Calculate basic statistics for a DataFrame column"""
    return {
        'mean': df[column].mean(),
        'median': df[column].median(),
        'max': df[column].max(),
        'min': df[column].min()
    }

# Keep these functions for backward compatibility
@st.cache_data
def fetch_api_data():
    """
    Legacy function for backward compatibility.
    Now uses the unified API client.
    """
    return fetch_unified_data()

@st.cache_data
def fetch_fantrax_data():
    """
    Legacy function for backward compatibility.
    Now uses the unified API client.
    """
    return fetch_unified_data()