
import akshare as ak
import sys
import os
import pandas as pd
import time

# Target stock and period
SYMBOL = "600000"
START_DATE = "20240101"
END_DATE = "20251119"

def try_fetch(name):
    print(f"\n--- Testing Configuration: {name} ---")
    print(f"Environment Keys: {[k for k in os.environ.keys() if 'PROXY' in k.upper()]}")
    if 'HTTP_PROXY' in os.environ:
        print(f"HTTP_PROXY: {os.environ['HTTP_PROXY']}")
    
    try:
        df = ak.stock_zh_a_hist(
            symbol=SYMBOL, 
            period="daily", 
            start_date=START_DATE, 
            end_date=END_DATE, 
            adjust="qfq"
        )
        if df is not None and not df.empty:
            print(f"✅ SUCCESS! Got {len(df)} rows.")
            return True
        else:
            print("❌ FAILED: Returned empty data.")
    except Exception as e:
        print(f"❌ FAILED: {e}")
    return False

def run_tests():
    # 1. System Default (Inherited)
    print("Initializing...")
    base_env = os.environ.copy()
    
    # Test 1: Default
    if try_fetch("1. System Default"):
        return

    # Test 2: Force Direct (Delete Proxy Vars)
    os.environ.update(base_env)
    for k in list(os.environ.keys()):
        if 'PROXY' in k.upper():
            del os.environ[k]
    
    if try_fetch("2. Force Direct (Deleted Vars)"):
        return

    # Test 3: Force Direct + NO_PROXY='*'
    os.environ.update(base_env)
    for k in list(os.environ.keys()):
        if 'PROXY' in k.upper():
            del os.environ[k]
    os.environ['NO_PROXY'] = '*'
    
    if try_fetch("3. Force Direct + NO_PROXY='*'"):
        return

    # Test 4: Force Specific Proxy (if known 7897)
    # os.environ.update(base_env)
    # proxy_url = "http://127.0.0.1:7897"
    # os.environ['HTTP_PROXY'] = proxy_url
    # os.environ['HTTPS_PROXY'] = proxy_url
    # if 'NO_PROXY' in os.environ: del os.environ['NO_PROXY']
    
    # if try_fetch(f"4. Force Specific Proxy ({proxy_url})"):
    #     return

if __name__ == "__main__":
    run_tests()
