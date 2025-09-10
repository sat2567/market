import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

def fetch_global_indices():
    url = "https://www.moneycontrol.com/markets/global-indices/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # Fetch the page content
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all tables with market data
        tables = soup.find_all('table', {'class': 'mctable1'})
        
        if not tables:
            return "No market data tables found on the page."
        
        # Dictionary to store all market data
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
        
        # Save to JSON file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"market_data_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(market_data, f, indent=4)
            
        return f"Data successfully saved to {filename}"
    
    except Exception as e:
        return f"An error occurred: {str(e)}"

if __name__ == "__main__":
    result = fetch_global_indices()
    print(result)
