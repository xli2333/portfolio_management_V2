"""
Configuration for Stock Technical Analyzer
"""

import os

# Data Fetching Settings
DEFAULT_DAYS = 120
DEFAULT_ADJUST = 'qfq'

# Output Settings
OUTPUT_DIR = 'output'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Indicator Parameters
INDICATOR_PARAMS = {
    'SMA': {'periods': [5, 10, 20, 60, 120, 250]},
    'EMA': {'periods': [12, 26, 50]},
    'RSI': {'periods': [6, 12, 14, 24]},
    'KDJ': {'fastk_period': 9, 'slowk_period': 3, 'slowd_period': 3},
    'MACD': {'fastperiod': 12, 'slowperiod': 26, 'signalperiod': 9},
    'BBANDS': {'timeperiod': 20, 'nbdevup': 2, 'nbdevdn': 2},
    'ATR': {'timeperiod': 14},
    'ADX': {'timeperiod': 14},
    # Advanced
    'SUPER_TREND': {'atr_period': 10, 'multiplier': 3.0},
    'ICHIMOKU': {'conversion': 9, 'base': 26, 'span_b': 52, 'displacement': 26},
    'DONCHIAN': {'period': 20},
    'KELTNER': {'ema_period': 20, 'atr_multiplier': 2.0},
    'MFI': {'timeperiod': 14},
    'CMF': {'timeperiod': 20},
    'EOM': {'timeperiod': 14},
    'FORCE': {'timeperiod': 13},
    'PPO': {'fastperiod': 12, 'slowperiod': 26, 'signalperiod': 9},
    'TSI': {'long': 25, 'short': 13, 'signal': 7},
    'DPO': {'timeperiod': 20},
    'KAMA': {'timeperiod': 30},
    'DEMA': {'timeperiod': 20},
    'TEMA': {'timeperiod': 20},
    'VWMA': {'period': 20},
    'FIBONACCI': {'lookback': 120}
}

# Signal Thresholds
SIGNAL_THRESHOLDS = {
    'RSI': {'oversold': 30, 'overbought': 70},
    'KDJ': {'oversold': 20, 'overbought': 80},
    'ADX': {'strong_trend': 25, 'weak_trend': 20},
    'WILLR': {'oversold': -80, 'overbought': -20},
}

# Regime Thresholds
REGIME_THRESHOLDS = {
    'ADX_trend': 25,
    'BB_width_low': 5.0,
    'ATR_pct_trend': 2.0,
}