from data_fetcher import DataFetcher
import pandas as pd

def test_ashare_fetch():
    print("Initializing DataFetcher...")
    fetcher = DataFetcher()
    
    # 测试代码：贵州茅台 (600519)
    symbol = "600519" 
    
    # 1. 测试日线 (Daily)
    print(f"\n[Testing] Fetching Daily data for {symbol}...")
    df_daily = fetcher.get_stock_data(symbol, period="daily")
    if df_daily is not None and not df_daily.empty:
        print("✅ Daily Fetch Success")
        print(f"Rows: {len(df_daily)}")
        print("Last 3 rows:")
        print(df_daily[['date', 'open', 'close', 'high', 'low', 'volume']].tail(3))
    else:
        print("❌ Daily Fetch Failed")

    # 2. 测试周线 (Weekly - Resampled)
    print(f"\n[Testing] Fetching Weekly data (Resampled) for {symbol}...")
    df_weekly = fetcher.get_stock_data(symbol, period="weekly")
    if df_weekly is not None and not df_weekly.empty:
        print("✅ Weekly Fetch Success")
        print(f"Rows: {len(df_weekly)}")
        print("Last 3 rows:")
        print(df_weekly[['date', 'open', 'close', 'high', 'low', 'volume', 'change_pct']].tail(3))
        
        # 简单验证一下是不是周五
        last_date = pd.to_datetime(df_weekly.iloc[-1]['date'])
        print(f"Last Candle Date: {last_date.date()} (Weekday: {last_date.weekday() + 1}, Expect 5 for Friday)")
    else:
        print("❌ Weekly Fetch Failed")

    # 3. 测试月线 (Monthly - Resampled)
    print(f"\n[Testing] Fetching Monthly data (Resampled) for {symbol}...")
    df_monthly = fetcher.get_stock_data(symbol, period="monthly")
    if df_monthly is not None and not df_monthly.empty:
        print("✅ Monthly Fetch Success")
        print(f"Rows: {len(df_monthly)}")
        print("Last 3 rows:")
        print(df_monthly[['date', 'open', 'close', 'high', 'low', 'volume', 'change_pct']].tail(3))
    else:
        print("❌ Monthly Fetch Failed")

if __name__ == "__main__":
    # 设置 pandas 显示选项以便查看
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    test_ashare_fetch()
