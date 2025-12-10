"""
Data Fetcher Module (A-Share + US-Stock Support)
Features:
1. Default Fetch Range: 400 days (Natural Days)
2. Auto-detects Market (US/CN)
"""

import sys
import io
import os
import time
import random
import requests
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional

# ================= 配置区域 =================
# 默认获取天数改为 400 天（自然日），以确保能计算年线(MA250)
DEFAULT_DAYS = 400 
DEFAULT_ADJUST = 'qfq'
# ===========================================

# Clean up any potential proxy environment variables to ensure direct connection
# Removed NO_PROXY to allow user-defined proxies
if 'HTTP_PROXY' in os.environ:
    del os.environ['HTTP_PROXY']
if 'HTTPS_PROXY' in os.environ:
    del os.environ['HTTPS_PROXY']

# Random User Agents for "Mocking" IP behavior (though mostly for headers)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
]

def get_sina_symbol(code: str) -> str:
    """Convert 6-digit code to Sina format (sh/sz/bj prefix)."""
    if code.startswith('6'): return f"sh{code}"
    if code.startswith('0') or code.startswith('3'): return f"sz{code}"
    if code.startswith('8') or code.startswith('4'): return f"bj{code}"
    return code

class DataFetcher:
    """
    Stock Data Fetcher
    Supports:
    - China A-Shares (6-digit codes, e.g., '600519')
    - US Stocks (Ticker symbols, e.g., 'AAPL', 'NVDA')
    """

    def __init__(self, use_proxy: bool = False):
        # Proxy support removed as requested
        pass

    def get_stock_data(
        self,
        symbol: str,
        days: int = DEFAULT_DAYS,
        adjust: str = DEFAULT_ADJUST,
        period: str = "daily"
    ) -> Optional[pd.DataFrame]:
        """
        Fetch historical stock data. Auto-detects A-Share vs US-Stock.
        """
        end_date = datetime.now()
        
        # Calculate start date
        multiplier = 1
        if period == "weekly": multiplier = 5
        elif period == "monthly": multiplier = 22
        
        # 使用传入的 days (默认400)
        start_date = end_date - timedelta(days=days * multiplier)
        
        start_date_str = start_date.strftime("%Y%m%d")
        end_date_str = end_date.strftime("%Y%m%d")

        # 判断是否为美股 (如果不全是数字，则认为是美股)
        is_us_stock = not symbol.isdigit()
        market_name = "US-Stock" if is_us_stock else "A-Share"

        print(f"Fetching {symbol} ({market_name}) from {start_date_str} ({days} days)...")

        try:
            df = None
            if is_us_stock:
                # === 美股接口 (ak.stock_us_daily) ===
                try:
                    df = ak.stock_us_daily(symbol=symbol, adjust=adjust)
                except Exception as e:
                    print(f"Akshare US fetch error: {e}")
                    return None
                
                if df is not None and not df.empty:
                    # 统一列名
                    df.rename(columns={
                        'date': 'date', 'open': 'open', 'high': 'high', 'low': 'low', 
                        'close': 'close', 'volume': 'volume'
                    }, inplace=True)
                    
                    # 过滤日期范围
                    df['date'] = pd.to_datetime(df['date'])
                    mask = (df['date'] >= start_date) & (df['date'] <= end_date)
                    df = df.loc[mask].copy()

                    # 处理美股的周K/月K重采样 (Resampling)
                    if period in ['weekly', 'monthly']:
                        # 设置日期索引
                        df.set_index('date', inplace=True)
                        
                        # 确定重采样规则 (W=周, M=月)
                        # W-FRI 表示每周五结束
                        rule = 'W-FRI' if period == 'weekly' else 'M'
                        
                        agg_dict = {
                            'open': 'first',
                            'high': 'max',
                            'low': 'min',
                            'close': 'last',
                            'volume': 'sum'
                        }
                        # 如果 amount 存在则聚合
                        if 'amount' in df.columns:
                            agg_dict['amount'] = 'sum'
                        # 只有 volume > 0 的行才有效 (避免引入假期产生的空行)
                        # 但 resample 会生成所有周期，需 dropna
                        
                        df_resampled = df.resample(rule).agg(agg_dict)
                        df_resampled.dropna(subset=['open', 'close'], inplace=True) # 移除无交易数据的周期
                        
                        # 重算涨跌幅
                        df_resampled['change_pct'] = df_resampled['close'].pct_change() * 100
                        
                        # 重置索引，让 date 变回列
                        df = df_resampled.reset_index()

                    # 转回字符串格式 YYYY-MM-DD
                    df['date'] = df['date'].dt.strftime('%Y-%m-%d')
                    
                    # 补充缺失字段
                    if 'amount' not in df.columns: df['amount'] = df['volume'] * df['close']
                    if 'change_pct' not in df.columns: df['change_pct'] = df['close'].pct_change() * 100

            else:
                # === A股接口 (Method A: Eastmoney / Method B: Sina) ===
                # Primary source, usually fastest and most detailed
                # Modify: Always fetch daily data, then resample locally if needed (Same as US Logic)
                # Add Retry Logic and Fallback
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        # Random wait to reduce pressure
                        if attempt > 0:
                            wait_time = random.uniform(0.5, 2.0)
                            print(f"  Retry {attempt}/{max_retries-1} after {wait_time:.1f}s...")
                            time.sleep(wait_time)

                        # Strategy 1: Eastmoney (stock_zh_a_hist) - Preferred
                        try:
                            df = ak.stock_zh_a_hist(
                                symbol=symbol,
                                period="daily", # Force daily
                                start_date=start_date_str,
                                end_date=end_date_str,
                                adjust=adjust
                            )
                        except Exception as e1:
                            print(f"  [!] Eastmoney failed: {e1}")
                            # Strategy 2: Sina (stock_zh_a_daily) - Fallback
                            # Note: Sina API often requires prefix
                            print("  [->] Switching to Sina interface...")
                            sina_symbol = get_sina_symbol(symbol)
                            df = ak.stock_zh_a_daily(
                                symbol=sina_symbol,
                                start_date=start_date_str,
                                end_date=end_date_str,
                                adjust=adjust
                            )
                        
                        if df is not None and not df.empty:
                            break # Success, exit loop
                            
                    except Exception as e:
                        print(f"  [!] Attempt {attempt+1} failed: {e}")
                        if attempt == max_retries - 1:
                            print("  [!] All retries failed for A-Share fetch.")
                            df = None

                if df is not None and not df.empty:
                    # 统一列名
                    # Handle both Eastmoney (Chinese) and Sina (English/mixed) columns
                    rename_map = {
                        '日期': 'date', '股票代码': 'code', '开盘': 'open', '收盘': 'close', 
                        '最高': 'high', '最低': 'low', '成交量': 'volume', '成交额': 'amount', 
                        '振幅': 'amplitude', '涨跌幅': 'change_pct', '涨跌额': 'change', 
                        '换手率': 'turnover'
                    }
                    df.rename(columns=rename_map, inplace=True)
                    
                    # 确保数值列为 float 类型
                    numeric_cols = ['open', 'close', 'high', 'low', 'volume', 'amount']
                    for col in numeric_cols:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors='coerce')

                    # 处理 A 股的周K/月K重采样 (Resampling) - 逻辑与美股一致
                    if period in ['weekly', 'monthly']:
                        # 转换日期格式进行索引
                        df['date'] = pd.to_datetime(df['date'])
                        df.set_index('date', inplace=True)
                        
                        # 确定重采样规则 (W=周, M=月)
                        # W-FRI 表示每周五结束
                        rule = 'W-FRI' if period == 'weekly' else 'M'
                        
                        agg_dict = {
                            'open': 'first',
                            'high': 'max',
                            'low': 'min',
                            'close': 'last',
                            'volume': 'sum'
                        }
                        # 如果 amount 存在则聚合
                        if 'amount' in df.columns:
                            agg_dict['amount'] = 'sum'
                            
                        df_resampled = df.resample(rule).agg(agg_dict)
                        df_resampled.dropna(subset=['open', 'close'], inplace=True) # 移除无交易数据的周期
                        
                        # 重算涨跌幅
                        df_resampled['change_pct'] = df_resampled['close'].pct_change() * 100
                        
                        # 重置索引，让 date 变回列
                        df = df_resampled.reset_index()

            # === 通用数据清洗 ===
            if df is None or df.empty:
                print(f"[!] Data for {symbol} is empty. Check symbol or network.")
                return None

            # 确保数值列为 float 类型
            numeric_cols = ['open', 'close', 'high', 'low', 'volume', 'amount']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            # 确保 date 是字符串 (YYYY-MM-DD)
            if not df.empty and 'date' in df.columns:
                first_date = df['date'].iloc[0]
                if not isinstance(first_date, str):
                     df['date'] = df['date'].apply(lambda x: x.strftime('%Y-%m-%d') if hasattr(x, 'strftime') else str(x))

            print(f"[OK] Successfully fetched {len(df)} rows")
            return df

        except Exception as e:
            print(f"[!] Fetch error: {e}")
            return None

    def get_stock_info(self, symbol: str) -> Optional[dict]:
        """
        Fetch stock basic info (Name, Code).
        """
        # 美股直接返回代码
        if not symbol.isdigit():
             return {'code': symbol, 'name': symbol}

        # A股: 尝试使用个股详情接口 (Method 1)
        # 这个接口只查询单只股票，速度快，不查全量列表
        try:
            df = ak.stock_individual_info_em(symbol=symbol)
            # 返回的 DataFrame 通常有 item 和 value 两列
            # 我们寻找 item 为 '股票简称' 的那一行
            if df is not None and not df.empty:
                # 过滤出股票简称
                name_row = df[df['item'] == '股票简称']
                if not name_row.empty:
                    stock_name = name_row.iloc[0]['value']
                    return {'code': symbol, 'name': stock_name}
        except Exception as e:
            print(f"[!] Name fetch error (Method 1): {e}")
            # 出错时不崩溃，直接回退

        # Fallback: 如果获取失败，直接返回代码
        return {'code': symbol, 'name': symbol}

    def get_usdcny_rate(self) -> float:
        """
        Return fixed USD/CNY exchange rate (7.1) as configured.
        Real-time fetch is disabled.
        """
        return 7.1

    def get_realtime_batch(self, symbols: list) -> dict:
        """
        Fetch real-time price snapshot for a list of symbols.
        Returns a dict: { '600519': { 'price': 1500.0, 'name': '贵州茅台', 'pct': 1.5, ... }, ... }
        """
        results = {}
        
        # Unified handling for both A-Shares and US-Stocks
        # Since the batch interface (ak.stock_zh_a_spot_em) is unstable under current proxy settings,
        # we switch to using the robust 'get_stock_data' method for all symbols.
        for symbol in symbols:
            try:
                # 1. Fetch Price Data (Reuse the working get_stock_data logic)
                # Fetching 5 days is enough to get the latest candle
                df = self.get_stock_data(symbol, days=5, period='daily')
                
                if df is not None and not df.empty:
                    last_row = df.iloc[-1]
                    price = float(last_row['close'])
                    pct = float(last_row['change_pct'])
                    
                    # 2. Fetch Name Information
                    # Default to symbol, try to resolve name if possible
                    name = symbol
                    try:
                        info = self.get_stock_info(symbol)
                        if info and 'name' in info:
                            name = info['name']
                    except Exception:
                        pass # Ignore name fetch errors, stick with symbol
                    
                    results[symbol] = {
                        'price': price,
                        'change_pct': pct,
                        'name': name
                    }
                else:
                    # Data empty
                    results[symbol] = {'price': 0, 'change_pct': 0, 'name': symbol}
            except Exception as e:
                print(f"[!] Realtime fetch error ({symbol}): {e}")
                results[symbol] = {'price': 0, 'change_pct': 0, 'name': symbol}
                
        return results