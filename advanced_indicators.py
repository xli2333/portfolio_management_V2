"""
Advanced technical indicators for comprehensive analysis.
"""

from typing import Dict
import numpy as np
import pandas as pd
import talib
from config import INDICATOR_PARAMS


def _ema(series: np.ndarray, period: int) -> np.ndarray:
    return talib.EMA(series.astype(float), timeperiod=period)


def _sma(series: np.ndarray, period: int) -> np.ndarray:
    return talib.SMA(series.astype(float), timeperiod=period)


def compute_supertrend(data: pd.DataFrame) -> Dict[str, np.ndarray]:
    params = INDICATOR_PARAMS.get('SUPER_TREND', {'atr_period': 10, 'multiplier': 3.0})
    atr_period = params['atr_period']
    mult = float(params['multiplier'])

    high = data['high'].astype(float).values
    low = data['low'].astype(float).values
    close = data['close'].astype(float).values

    atr = talib.ATR(high, low, close, timeperiod=atr_period)
    # Basic bands
    hl2 = (high + low) / 2.0
    upper_basic = hl2 + mult * atr
    lower_basic = hl2 - mult * atr

    n = len(close)
    upper = np.copy(upper_basic)
    lower = np.copy(lower_basic)
    trend = np.full(n, np.nan)

    # Final bands and trend direction
    for i in range(1, n):
        upper[i] = min(upper_basic[i], upper[i - 1]) if not np.isnan(upper[i-1]) else upper_basic[i]
        lower[i] = max(lower_basic[i], lower[i - 1]) if not np.isnan(lower[i-1]) else lower_basic[i]

        if np.isnan(trend[i-1]):
            # initialize trend with first non-nan
            trend[i] = 1 if close[i] >= upper[i - 1] else -1
        else:
            if trend[i-1] == 1:
                if close[i] < lower[i]:
                    trend[i] = -1
                    upper[i] = upper_basic[i]
                else:
                    trend[i] = 1
            else:
                if close[i] > upper[i]:
                    trend[i] = 1
                    lower[i] = lower_basic[i]
                else:
                    trend[i] = -1

    supertrend = np.where(trend == 1, lower, upper)

    return {
        'ST_Upper': upper,
        'ST_Lower': lower,
        'SuperTrend': supertrend,
        'ST_Direction': trend,  # 1 bull, -1 bear
    }


def compute_ichimoku(data: pd.DataFrame) -> Dict[str, np.ndarray]:
    p = INDICATOR_PARAMS.get('ICHIMOKU', {'conversion': 9, 'base': 26, 'span_b': 52, 'displacement': 26})
    high = data['high'].astype(float).values
    low = data['low'].astype(float).values
    close = data['close'].astype(float).values

    conv = int(p['conversion'])
    base = int(p['base'])
    span_b = int(p['span_b'])

    def rolling_mid(h, l, period):
        hh = talib.MAX(h, timeperiod=period)
        ll = talib.MIN(l, timeperiod=period)
        return (hh + ll) / 2.0

    tenkan = rolling_mid(high, low, conv)
    kijun = rolling_mid(high, low, base)
    senkou_a = (tenkan + kijun) / 2.0
    senkou_b = rolling_mid(high, low, span_b)

    # shift forward by base periods; fill with nan at beginning to align
    disp = int(p['displacement'])
    def fwd_shift(arr, k):
        res = np.full_like(arr, np.nan)
        if k <= 0:
            return arr
        res[k:] = arr[:-k]
        return res

    senkou_a_fwd = fwd_shift(senkou_a, disp)
    senkou_b_fwd = fwd_shift(senkou_b, disp)
    chikou = np.full_like(close, np.nan)
    # lagging span is close shifted back by base
    if disp > 0:
        chikou[:-disp] = close[disp:]

    return {
        'Ichimoku_Tenkan': tenkan,
        'Ichimoku_Kijun': kijun,
        'Ichimoku_SenkouA': senkou_a_fwd,
        'Ichimoku_SenkouB': senkou_b_fwd,
        'Ichimoku_Chikou': chikou,
    }


def compute_donchian(data: pd.DataFrame) -> Dict[str, np.ndarray]:
    period = int(INDICATOR_PARAMS.get('DONCHIAN', {'period': 20})['period'])
    high = data['high'].astype(float)
    low = data['low'].astype(float)

    upper = high.rolling(window=period, min_periods=1).max().values
    lower = low.rolling(window=period, min_periods=1).min().values
    middle = (upper + lower) / 2.0
    return {
        'Donchian_Upper': upper,
        'Donchian_Lower': lower,
        'Donchian_Middle': middle,
    }


def compute_keltner(data: pd.DataFrame) -> Dict[str, np.ndarray]:
    p = INDICATOR_PARAMS.get('KELTNER', {'ema_period': 20, 'atr_multiplier': 2.0})
    ema_p = int(p['ema_period'])
    mult = float(p['atr_multiplier'])
    high = data['high'].astype(float).values
    low = data['low'].astype(float).values
    close = data['close'].astype(float).values
    tp = (high + low + close) / 3.0
    ema_tp = talib.EMA(tp, timeperiod=ema_p)
    atr = talib.ATR(high, low, close, timeperiod=ema_p)
    upper = ema_tp + mult * atr
    lower = ema_tp - mult * atr
    return {
        'Keltner_Middle': ema_tp,
        'Keltner_Upper': upper,
        'Keltner_Lower': lower,
    }


def compute_moneyflow(data: pd.DataFrame) -> Dict[str, np.ndarray]:
    close = data['close'].astype(float).values
    high = data['high'].astype(float).values
    low = data['low'].astype(float).values
    volume = data['volume'].astype(float).values

    mfi = talib.MFI(high, low, close, volume, timeperiod=int(INDICATOR_PARAMS.get('MFI', {'timeperiod': 14})['timeperiod']))

    # Chaikin Money Flow
    period = int(INDICATOR_PARAMS.get('CMF', {'timeperiod': 20})['timeperiod'])
    mfm = ((close - low) - (high - close)) / np.where((high - low) == 0, 1e-9, (high - low))
    mfv = mfm * volume
    cmf = pd.Series(mfv).rolling(window=period, min_periods=1).sum().values / \
          pd.Series(volume).rolling(window=period, min_periods=1).sum().values

    # Ease of Movement
    eom_period = int(INDICATOR_PARAMS.get('EOM', {'timeperiod': 14})['timeperiod'])
    hl_mid = (high + low) / 2.0
    box_ratio = np.where((high - low) == 0, 1e-9, (high - low)) / volume
    eom = ((hl_mid[1:] - hl_mid[:-1]) / box_ratio[1:])
    eom = np.insert(eom, 0, np.nan)
    eom = pd.Series(eom).rolling(window=eom_period, min_periods=1).mean().values

    # Force Index
    fi_period = int(INDICATOR_PARAMS.get('FORCE', {'timeperiod': 13})['timeperiod'])
    force = np.insert((close[1:] - close[:-1]) * volume[1:], 0, 0.0)
    force = talib.EMA(force, timeperiod=fi_period)

    return {
        'MFI': mfi,
        'CMF': cmf,
        'EOM': eom,
        'ForceIndex': force,
    }


def compute_momentum_extra(data: pd.DataFrame) -> Dict[str, np.ndarray]:
    close = data['close'].astype(float).values
    ppo_p = INDICATOR_PARAMS.get('PPO', {'fastperiod': 12, 'slowperiod': 26, 'signalperiod': 9})
    ppo = talib.PPO(close, fastperiod=int(ppo_p['fastperiod']), slowperiod=int(ppo_p['slowperiod']))
    ppo_signal = talib.EMA(ppo, timeperiod=int(ppo_p['signalperiod']))

    # TSI
    tsi_p = INDICATOR_PARAMS.get('TSI', {'long': 25, 'short': 13, 'signal': 7})
    m = np.insert(close[1:] - close[:-1], 0, 0.0)
    ema1 = talib.EMA(m, timeperiod=int(tsi_p['long']))
    ema2 = talib.EMA(ema1, timeperiod=int(tsi_p['short']))
    abs_m = np.abs(m)
    ema1_abs = talib.EMA(abs_m, timeperiod=int(tsi_p['long']))
    ema2_abs = talib.EMA(ema1_abs, timeperiod=int(tsi_p['short']))
    tsi = np.where(ema2_abs == 0, 0.0, 100.0 * ema2 / ema2_abs)
    tsi_signal = talib.EMA(tsi, timeperiod=int(tsi_p['signal']))

    # DPO
    dpo_n = int(INDICATOR_PARAMS.get('DPO', {'timeperiod': 20})['timeperiod'])
    sma = talib.SMA(close, timeperiod=dpo_n)
    shift = int(dpo_n / 2 + 1)
    sma_shift = np.full_like(close, np.nan)
    sma_shift[shift:] = sma[:-shift]
    dpo = close - sma_shift

    # KAMA / DEMA / TEMA
    kama_p = int(INDICATOR_PARAMS.get('KAMA', {'timeperiod': 30})['timeperiod'])
    kama = talib.KAMA(close, timeperiod=kama_p)
    kama_slope = np.insert(kama[1:] - kama[:-1], 0, 0.0)
    dema = talib.DEMA(close, timeperiod=int(INDICATOR_PARAMS.get('DEMA', {'timeperiod': 20})['timeperiod']))
    tema = talib.TEMA(close, timeperiod=int(INDICATOR_PARAMS.get('TEMA', {'timeperiod': 20})['timeperiod']))

    return {
        'PPO': ppo,
        'PPO_Signal': ppo_signal,
        'TSI': tsi,
        'TSI_Signal': tsi_signal,
        'DPO': dpo,
        'KAMA': kama,
        'KAMA_Slope': kama_slope,
        'DEMA': dema,
        'TEMA': tema,
    }


def compute_regime_features(data: pd.DataFrame, base_ind: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
    """Pre-compute features used for regime detection and weighting."""
    close = data['close'].astype(float).values
    res: Dict[str, np.ndarray] = {}

    # BB width (percent of middle)
    upper = base_ind.get('BB_Upper')
    lower = base_ind.get('BB_Lower')
    middle = base_ind.get('BB_Middle')
    if upper is not None and lower is not None and middle is not None:
        width = np.where(middle == 0, np.nan, (upper - lower) / middle * 100.0)
        res['BB_Width'] = width

    # ATR percentage
    atr = base_ind.get('ATR')
    return res


def compute_vwma(data: pd.DataFrame) -> Dict[str, np.ndarray]:
    """
    Compute Volume Weighted Moving Average (VWMA).
    Acts as a dynamic support/resistance level that accounts for volume.
    """
    period = int(INDICATOR_PARAMS.get('VWMA', {'period': 20})['period'])
    close = data['close'].astype(float).values
    volume = data['volume'].astype(float).values
    
    # VWMA = Sum(Price * Volume) / Sum(Volume)
    pv = close * volume
    
    vwma = pd.Series(pv).rolling(window=period, min_periods=period).sum() / \
           pd.Series(volume).rolling(window=period, min_periods=period).sum()
           
    return {
        'VWMA': vwma.values
    }


def compute_fibonacci_levels(data: pd.DataFrame) -> Dict[str, float]:
    """
    Compute dynamic Fibonacci Retracement levels based on recent significant High/Low over a lookback period.
    """
    lookback = int(INDICATOR_PARAMS.get('FIBONACCI', {'lookback': 120})['lookback'])
    highs = data['high'].astype(float).values
    lows = data['low'].astype(float).values
    
    # Look back 'lookback' days or available data
    lb = min(len(highs), lookback)
    if lb < 2:
        return {}
        
    recent_high = np.max(highs[-lb:])
    recent_low = np.min(lows[-lb:])
    
    diff = recent_high - recent_low
    
    return {
        'Fib_High': recent_high,
        'Fib_Low': recent_low,
        'Fib_0.236': recent_high - diff * 0.236,
        'Fib_0.382': recent_high - diff * 0.382,
        'Fib_0.500': recent_high - diff * 0.500,
        'Fib_0.618': recent_high - diff * 0.618,
        'Fib_0.786': recent_high - diff * 0.786,
    }

