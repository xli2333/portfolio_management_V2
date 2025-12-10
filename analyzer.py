"""Stock Technical Analyzer - Clean implementation.

Key responsibilities:
- Fetch stock info and OHLCV data
- Compute technical indicators & patterns
- Generate base and advanced signals
- Produce a comprehensive score
- Provide helpers for price info, key indicator snapshot, MA levels
"""

import sys
import io
import json
from datetime import datetime
from typing import Dict

import numpy as np
import pandas as pd

# Fix Windows console encoding for stdout
# if sys.platform == "win32":
#     sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from data_fetcher import DataFetcher
from indicators import TechnicalIndicators, PatternRecognizer
from signals import SignalGenerator
from advanced_indicators import (
    compute_supertrend,
    compute_ichimoku,
    compute_donchian,
    compute_keltner,
    compute_moneyflow,
    compute_momentum_extra,
    compute_regime_features,
    compute_vwma,
    compute_fibonacci_levels,
)
from advanced_signals import AdvancedSignalGenerator


class StockAnalyzer:
    def __init__(self, use_proxy: bool = True):
        self.fetcher = DataFetcher(use_proxy=use_proxy)
        self.data = None
        self.stock_info = None
        self.indicators = None
        self.patterns = None
        self.signals = None
        self.extra_indicators = None
        self.综合评分 = None
        self.last_error = None  # Store specific error messages

    def analyze(self, symbol: str, days: int = 120, period: str = "daily") -> bool:
        """Run full analysis pipeline."""
        self.last_error = None
        
        try:
            # 1) stock info
            try:
                self.stock_info = self.fetcher.get_stock_info(symbol)
                if not self.stock_info:
                    self.last_error = f"Stock info not found for symbol: {symbol}"
                    print(self.last_error)
                    return False
            except Exception as e:
                self.last_error = f"Error fetching stock info: {str(e)}"
                print(self.last_error)
                return False

            # 2) OHLCV data
            try:
                self.data = self.fetcher.get_stock_data(symbol, days=days, period=period)
                if self.data is None or len(self.data) == 0:
                    self.last_error = f"No historical data found for {symbol} (period={period})"
                    print(self.last_error)
                    return False
            except Exception as e:
                self.last_error = f"Error fetching historical data: {str(e)}"
                print(self.last_error)
                return False

            # 3) technical indicators
            try:
                indicator_calc = TechnicalIndicators(self.data)
                self.indicators = indicator_calc.calculate_all()
            except Exception as e:
                 self.last_error = f"Indicator calculation failed: {str(e)}"
                 print(self.last_error)
                 return False

            # 4) patterns
            recognizer = PatternRecognizer(self.data)
            self.patterns = recognizer.detect_all_patterns()

            # 5) base signals + score (legacy)
            base_signal_gen = SignalGenerator(self.data, self.indicators, self.patterns)
            base_signals = base_signal_gen.generate_all_signals()

            # 6) advanced indicators + signals + score
            extra_ind = {}
            try:
                extra_ind.update(compute_supertrend(self.data))
                extra_ind.update(compute_ichimoku(self.data))
                extra_ind.update(compute_donchian(self.data))
                extra_ind.update(compute_keltner(self.data))
                extra_ind.update(compute_moneyflow(self.data))
                extra_ind.update(compute_momentum_extra(self.data))
                extra_ind.update(compute_vwma(self.data))
                extra_ind.update(compute_fibonacci_levels(self.data))
                extra_ind.update(compute_regime_features(self.data, self.indicators))
            except Exception as e:
                # If any advanced indicator fails, log but continue with available ones
                print(f"Warning: Advanced indicators partial failure: {e}")
            
            self.extra_indicators = extra_ind

            adv_gen = AdvancedSignalGenerator(self.data, self.indicators, extra_ind)
            adv_signals = adv_gen.generate()
            self.signals = {**base_signals, **adv_signals}
            self.综合评分 = adv_gen.score(self.signals)

            return True
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.last_error = f"Unexpected analyzer crash: {str(e)}"
            return False

    def get_price_info(self) -> Dict:
        if self.data is None:
            return {}
        latest = self.data.iloc[-1]
        prev = self.data.iloc[-2] if len(self.data) > 1 else latest
        return {
            'date': str(latest['date']),
            'open': float(latest['open']),
            'close': float(latest['close']),
            'high': float(latest['high']),
            'low': float(latest['low']),
            'volume': float(latest['volume']),
            'amount': float(latest['amount']) if 'amount' in latest else 0.0,
            'change': float(latest['close'] - prev['close']) if len(self.data) > 1 else 0.0,
            'change_pct': float(latest['change_pct']) if 'change_pct' in latest else 0.0,
        }

    def get_key_indicators(self) -> Dict:
        if self.indicators is None:
            return {}
        def _last(name):
            v = self.indicators.get(name)
            if v is None:
                return np.nan
            return float(v[-1]) if len(v) else np.nan

        return {
            'RSI_14': _last('RSI_14'),
            'K': _last('K'),
            'D': _last('D'),
            'J': _last('J'),
            'MACD': _last('MACD'),
            'MACD_Signal': _last('MACD_Signal'),
            'ADX': _last('ADX'),
            'ATR': _last('ATR'),
            'CCI': _last('CCI'),
            'WILLR': _last('WILLR'),
        }

    def get_ma_levels(self) -> Dict:
        if self.indicators is None:
            return {}
        ma_keys = ['SMA_5', 'SMA_10', 'SMA_20', 'SMA_60', 'SMA_120', 'SMA_250', 'EMA_12', 'EMA_26', 'EMA_50']
        levels = {}
        for k in ma_keys:
            if k in self.indicators and len(self.indicators[k]) > 0:
                levels[k] = float(self.indicators[k][-1])
        return levels

    # Optional: exporting helpers
    def export_to_json(self, filepath: str):
        if self.data is None:
            print('No data to export')
            return

        def clean_obj(obj):
            """Recursively convert numpy types to python types for JSON serialization."""
            if isinstance(obj, dict):
                return {k: clean_obj(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [clean_obj(item) for item in obj]
            elif isinstance(obj, np.ndarray):
                return clean_obj(obj.tolist())
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return None if (np.isnan(obj) or np.isinf(obj)) else float(obj)
            elif isinstance(obj, float):
                return None if (np.isnan(obj) or np.isinf(obj)) else obj
            return obj

        raw_result = {
            'stock_info': self.stock_info,
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'price_info': self.get_price_info(),
            'key_indicators': self.get_key_indicators(),
            'ma_levels': self.get_ma_levels(),
            'patterns': self.patterns,
            'signals': self.signals,
            'comprehensive_score': self.综合评分,
            'advanced_indicators': self.extra_indicators,
        }
        
        final_result = clean_obj(raw_result)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(final_result, f, ensure_ascii=False, indent=2)
        print(f'[OK] Exported JSON: {filepath}')


if __name__ == '__main__':
    print('Standalone run example')
    sym = input('输入股票代码: ').strip() or '000001'
    analyzer = StockAnalyzer(use_proxy=True)
    if analyzer.analyze(sym, days=120):
        print(json.dumps({
            'price': analyzer.get_price_info(),
            'score': analyzer.综合评分,
        }, ensure_ascii=False, indent=2))

