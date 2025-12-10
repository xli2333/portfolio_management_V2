import akshare as ak
import sys
import os
import urllib.request

# Print env vars to see what we are dealing with
print("Env Proxy Vars (Before):", {k:v for k,v in os.environ.items() if 'PROXY' in k.upper()})
print("System Proxies (urllib):", urllib.request.getproxies())

# FORCE REMOVE PROXY
# os.environ['NO_PROXY'] = '*'
# if 'HTTP_PROXY' in os.environ: del os.environ['HTTP_PROXY']
# if 'HTTPS_PROXY' in os.environ: del os.environ['HTTPS_PROXY']
# if 'http_proxy' in os.environ: del os.environ['http_proxy']
# if 'https_proxy' in os.environ: del os.environ['https_proxy']
# if 'ALL_PROXY' in os.environ: del os.environ['ALL_PROXY']
# if 'all_proxy' in os.environ: del os.environ['all_proxy']

print("Env Proxy Vars (After):", {k:v for k,v in os.environ.items() if 'PROXY' in k.upper()})

print("Testing native akshare...")
try:
    df = ak.stock_zh_a_hist(symbol="600000", period="daily", start_date="20230101", end_date="20230201", adjust="qfq")
    print(f"Success! Got {len(df)} rows.")
except Exception as e:
    print(f"Native akshare failed: {e}")
