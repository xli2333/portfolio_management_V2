
from flask import Flask
import akshare as ak
import sys
import os

# Create a minimal Flask app context
app = Flask(__name__)

def fetch_data():
    print("Testing akshare inside Flask context...")
    with app.app_context():
        try:
            # Mimic exactly what DataFetcher does now (clearing proxies)
            old_proxies = {}
            proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']
            for var in proxy_vars:
                if var in os.environ:
                    old_proxies[var] = os.environ[var]
                    del os.environ[var]
            os.environ['NO_PROXY'] = '*'
            
            print("Fetching data for 688766...")
            df = ak.stock_zh_a_hist(symbol="688766", period="daily", start_date="20250101", end_date="20251119", adjust="qfq")
            print(f"Success! Got {len(df)} rows.")
            print(df.tail(3))
            
        except Exception as e:
            print(f"FAIL: {e}")

if __name__ == "__main__":
    fetch_data()
