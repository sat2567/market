import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import os
import json
import plotly.express as px
from pathlib import Path

# Set page configuration
st.set_page_config(
    page_title="Global Market Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {font-size:24px; font-weight: bold; color: #1f77b4;}
    .market-card {border-radius: 10px; padding: 15px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);}
    .positive-change {color: #2ecc71;}
    .negative-change {color: #e74c3c;}
    .last-updated {font-size: 12px; color: #7f8c8d; text-align: right;}
    </style>
""", unsafe_allow_html=True)

# File paths
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
DATA_FILE = DATA_DIR / "market_data.json"
CACHE_DURATION = 3600  # 1 hour in seconds

def fetch_market_data():
    """Fetch market data from Moneycontrol"""
    url = "https://www.moneycontrol.com/markets/global-indices/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all tables with market data
        tables = soup.find_all('table', {'class': 'mctable1'})
        
        if not tables:
            return {"error": "No market data tables found on the page.", "timestamp": datetime.now().isoformat()}
        
        market_data = {}
        
        # Process each table
        for table in tables:
            # Get the table title (market region)
            title = table.find_previous('h2')
            if title:
                title = title.text.strip()
            else:
                title = f"Market_Table_{len(market_data) + 1}"
            
            # Extract table data
            df = pd.read_html(str(table))[0]
            market_data[title] = df.to_dict('records')
        
        # Add timestamp
        market_data["last_updated"] = datetime.now().isoformat()
        
        # Save to file
        with open(DATA_FILE, 'w') as f:
            json.dump(market_data, f)
            
        return market_data
    
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}", "timestamp": datetime.now().isoformat()}

def load_cached_data():
    """Load cached data if it exists and is not expired"""
    if not DATA_FILE.exists():
        return None
        
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            
        # Check if data is expired
        last_updated = datetime.fromisoformat(data.get("last_updated", "1970-01-01"))
        if (datetime.now() - last_updated).total_seconds() < CACHE_DURATION:
            return data
        return None
    except Exception:
        return None

def format_change(change_str):
    """Format the change value with color"""
    if not isinstance(change_str, str):
        return change_str
    
    try:
        change = float(change_str.replace('%', '').replace(',', '').strip())
        if change > 0:
            return f'<span class="positive-change">+{change:.2f}%</span>'
        elif change < 0:
            return f'<span class="negative-change">{change:.2f}%</span>'
        return f'{change:.2f}%'
    except:
        return change_str

def display_market_data(data):
    """Display market data in Streamlit"""
    st.title("🌍 Global Market Dashboard")
    
    # Last updated time
    last_updated = datetime.fromisoformat(data.get("last_updated", datetime.now().isoformat()))
    st.markdown(f"<div class='last-updated'>Last updated: {last_updated.strftime('%Y-%m-%d %H:%M:%S')}</div>", unsafe_allow_html=True)
    
    # Remove the timestamp from data
    data.pop("last_updated", None)
    
    # Display each market section
    for section, rows in data.items():
        if not rows:
            continue
            
        st.markdown(f"### {section}")
        
        # Convert to DataFrame for better display
        df = pd.DataFrame(rows)
        
        # Format the change columns if they exist
        change_columns = [col for col in df.columns if 'change' in col.lower() or 'chg' in col.lower()]
        
        # Display the table
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                col: st.column_config.NumberColumn(
                    col,
                    format="%.2f" if df[col].dtype == 'float64' else None
                ) for col in df.columns
            }
        )
        
        # Add a line chart for the first numeric column if available
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
        if len(numeric_cols) > 0:
            chart_col = numeric_cols[0]
            fig = px.line(df, y=chart_col, x=df.index, title=f"{section} - {chart_col}")
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")

def main():
    # Check if we have cached data
    data = load_cached_data()
    
    # If no cached data or data is expired, fetch new data
    if data is None:
        with st.spinner('Fetching latest market data...'):
            data = fetch_market_data()
    
    # Display the data
    if data and "error" not in data:
        display_market_data(data)
    else:
        st.error("Failed to fetch market data. Please try again later.")
        if data and "error" in data:
            st.error(data["error"])
    
    # Add a refresh button
    if st.button("🔄 Refresh Data"):
        with st.spinner('Fetching latest market data...'):
            data = fetch_market_data()
            if data and "error" not in data:
                st.rerun()

if __name__ == "__main__":
    main()
