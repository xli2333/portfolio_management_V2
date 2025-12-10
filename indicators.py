"""
Technical Indicators Module
计算各类技术指标
"""

import talib
import pandas as pd
import numpy as np
from typing import Dict
from config import INDICATOR_PARAMS


class TechnicalIndicators:
    """技术指标计算器"""

    def __init__(self, data: pd.DataFrame):
        """
        初始化

        Args:
            data: OHLCV数据
        """
        self.data = data
        self.open = data['open'].astype(float).values
        self.high = data['high'].astype(float).values
        self.low = data['low'].astype(float).values
        self.close = data['close'].astype(float).values
        self.volume = data['volume'].astype(float).values

    def calculate_all(self) -> Dict:
        """计算所有指标"""
        indicators = {}

        # 1. 移动平均线
        indicators.update(self.calculate_ma())

        # 2. MACD
        indicators.update(self.calculate_macd())

        # 3. RSI
        indicators.update(self.calculate_rsi())

        # 4. KDJ
        indicators.update(self.calculate_kdj())

        # 5. 布林带
        indicators.update(self.calculate_bbands())

        # 6. 波动率指标
        indicators.update(self.calculate_volatility())

        # 7. 趋势指标
        indicators.update(self.calculate_trend())

        # 8. 成交量指标
        indicators.update(self.calculate_volume())

        # 9. 其他振荡指标
        indicators.update(self.calculate_oscillators())

        return indicators

    def calculate_ma(self) -> Dict:
        """计算移动平均线"""
        result = {}

        # SMA
        for period in INDICATOR_PARAMS['SMA']['periods']:
            result[f'SMA_{period}'] = talib.SMA(self.close, timeperiod=period)

        # EMA
        for period in INDICATOR_PARAMS['EMA']['periods']:
            result[f'EMA_{period}'] = talib.EMA(self.close, timeperiod=period)

        # WMA
        result['WMA_20'] = talib.WMA(self.close, timeperiod=20)

        return result

    def calculate_macd(self) -> Dict:
        """计算MACD"""
        params = INDICATOR_PARAMS['MACD']
        macd, signal, hist = talib.MACD(
            self.close,
            fastperiod=params['fastperiod'],
            slowperiod=params['slowperiod'],
            signalperiod=params['signalperiod']
        )

        return {
            'MACD': macd,
            'MACD_Signal': signal,
            'MACD_Hist': hist
        }

    def calculate_rsi(self) -> Dict:
        """计算RSI"""
        result = {}
        for period in INDICATOR_PARAMS['RSI']['periods']:
            result[f'RSI_{period}'] = talib.RSI(self.close, timeperiod=period)
        return result

    def calculate_kdj(self) -> Dict:
        """计算KDJ"""
        params = INDICATOR_PARAMS['KDJ']
        k, d = talib.STOCH(
            self.high,
            self.low,
            self.close,
            fastk_period=params['fastk_period'],
            slowk_period=params['slowk_period'],
            slowd_period=params['slowd_period']
        )
        j = 3 * k - 2 * d

        return {'K': k, 'D': d, 'J': j}

    def calculate_bbands(self) -> Dict:
        """计算布林带"""
        params = INDICATOR_PARAMS['BBANDS']
        upper, middle, lower = talib.BBANDS(
            self.close,
            timeperiod=params['timeperiod'],
            nbdevup=params['nbdevup'],
            nbdevdn=params['nbdevdn']
        )

        # 计算%B（价格在布林带中的位置）
        pct_b = (self.close - lower) / (upper - lower) * 100

        return {
            'BB_Upper': upper,
            'BB_Middle': middle,
            'BB_Lower': lower,
            'BB_PctB': pct_b
        }

    def calculate_volatility(self) -> Dict:
        """计算波动率指标"""
        atr_period = INDICATOR_PARAMS['ATR']['timeperiod']

        return {
            'ATR': talib.ATR(self.high, self.low, self.close, timeperiod=atr_period),
            'NATR': talib.NATR(self.high, self.low, self.close, timeperiod=atr_period),
            'TRANGE': talib.TRANGE(self.high, self.low, self.close),
        }

    def calculate_trend(self) -> Dict:
        """计算趋势指标"""
        adx_period = INDICATOR_PARAMS['ADX']['timeperiod']

        # DMI/ADX
        adx = talib.ADX(self.high, self.low, self.close, timeperiod=adx_period)
        plus_di = talib.PLUS_DI(self.high, self.low, self.close, timeperiod=adx_period)
        minus_di = talib.MINUS_DI(self.high, self.low, self.close, timeperiod=adx_period)
        adxr = talib.ADXR(self.high, self.low, self.close, timeperiod=adx_period)

        # TRIX
        trix = talib.TRIX(self.close, timeperiod=12)

        # Aroon
        aroon_down, aroon_up = talib.AROON(self.high, self.low, timeperiod=25)

        # SAR
        sar = talib.SAR(self.high, self.low)

        return {
            'ADX': adx,
            '+DI': plus_di,
            '-DI': minus_di,
            'ADXR': adxr,
            'TRIX': trix,
            'Aroon_Up': aroon_up,
            'Aroon_Down': aroon_down,
            'SAR': sar,
        }

    def calculate_volume(self) -> Dict:
        """计算成交量指标"""
        # OBV
        obv = talib.OBV(self.close, self.volume)

        # AD
        ad = talib.AD(self.high, self.low, self.close, self.volume)

        # ADOSC
        adosc = talib.ADOSC(self.high, self.low, self.close, self.volume)

        return {
            'OBV': obv,
            'AD': ad,
            'ADOSC': adosc,
        }

    def calculate_oscillators(self) -> Dict:
        """计算其他振荡指标"""
        # Williams %R
        willr = talib.WILLR(self.high, self.low, self.close, timeperiod=14)

        # CCI
        cci = talib.CCI(self.high, self.low, self.close, timeperiod=14)

        # ROC
        roc = talib.ROC(self.close, timeperiod=10)

        # MOM
        mom = talib.MOM(self.close, timeperiod=10)

        # Stochastic RSI
        fastk, fastd = talib.STOCHRSI(self.close, timeperiod=14)

        # Ultimate Oscillator
        ultosc = talib.ULTOSC(self.high, self.low, self.close)

        return {
            'WILLR': willr,
            'CCI': cci,
            'ROC': roc,
            'MOM': mom,
            'StochRSI_K': fastk,
            'StochRSI_D': fastd,
            'ULTOSC': ultosc,
        }

    def get_latest_values(self, indicators: Dict) -> Dict:
        """获取所有指标的最新值"""
        latest = {}
        for name, values in indicators.items():
            if isinstance(values, np.ndarray):
                latest[name] = values[-1] if len(values) > 0 else np.nan
            else:
                latest[name] = values

        return latest


class PatternRecognizer:
    """K线形态识别器"""

    def __init__(self, data: pd.DataFrame):
        """
        初始化

        Args:
            data: OHLCV数据
        """
        self.open = data['open'].astype(float).values
        self.high = data['high'].astype(float).values
        self.low = data['low'].astype(float).values
        self.close = data['close'].astype(float).values

    def detect_all_patterns(self) -> Dict:
        """检测所有形态"""
        patterns = {}

        # 看涨形态
        bullish = self._detect_bullish_patterns()
        patterns.update(bullish)

        # 看跌形态
        bearish = self._detect_bearish_patterns()
        patterns.update(bearish)

        # 中性形态
        neutral = self._detect_neutral_patterns()
        patterns.update(neutral)

        return patterns

    def _detect_bullish_patterns(self) -> Dict:
        """检测看涨形态"""
        patterns = {}

        bullish_funcs = {
            'CDL3WHITESOLDIERS': '三白兵',
            'CDLMORNINGSTAR': '晨星',
            'CDLHAMMER': '锤子线',
            'CDLPIERCING': '刺穿形态',
            'CDLENGULFING': '吞没形态',
            'CDLHARAMI': '孕线',
            'CDL3INSIDE': '三内上升',
            'CDLINVERTEDHAMMER': '倒锤线',
            'CDLDRAGONFLYDOJI': '蜻蜓十字',
        }

        for func_name, chinese_name in bullish_funcs.items():
            func = getattr(talib, func_name)
            result = func(self.open, self.high, self.low, self.close)

            if result[-1] > 0:
                patterns[chinese_name] = {
                    'type': 'bullish',
                    'signal': int(result[-1]),
                    'strength': '强' if result[-1] == 100 else '弱'
                }

        return patterns

    def _detect_bearish_patterns(self) -> Dict:
        """检测看跌形态"""
        patterns = {}

        bearish_funcs = {
            'CDL3BLACKCROWS': '三黑鸦',
            'CDLEVENINGSTAR': '黄昏星',
            'CDLHANGINGMAN': '上吊线',
            'CDLDARKCLOUDCOVER': '乌云盖顶',
            'CDLSHOOTINGSTAR': '流星',
            'CDL3OUTSIDE': '三外下降',
            'CDLGRAVESTONEDOJI': '墓碑十字',
        }

        for func_name, chinese_name in bearish_funcs.items():
            func = getattr(talib, func_name)
            result = func(self.open, self.high, self.low, self.close)

            if result[-1] < 0:
                patterns[chinese_name] = {
                    'type': 'bearish',
                    'signal': int(result[-1]),
                    'strength': '强' if result[-1] == -100 else '弱'
                }

        return patterns

    def _detect_neutral_patterns(self) -> Dict:
        """检测中性形态"""
        patterns = {}

        neutral_funcs = {
            'CDLDOJI': '十字星',
            'CDLSPINNINGTOP': '纺锤线',
            'CDLHIGHWAVE': '高浪线',
        }

        for func_name, chinese_name in neutral_funcs.items():
            func = getattr(talib, func_name)
            result = func(self.open, self.high, self.low, self.close)

            if result[-1] != 0:
                patterns[chinese_name] = {
                    'type': 'neutral',
                    'signal': int(result[-1]),
                    'strength': '中性'
                }

        return patterns


if __name__ == "__main__":
    # 测试指标计算
    from data_fetcher import DataFetcher

    fetcher = DataFetcher(use_proxy=True)
    data = fetcher.get_stock_data("000001", days=100)

    if data is not None:
        # 测试指标计算
        calc = TechnicalIndicators(data)
        indicators = calc.calculate_all()
        latest = calc.get_latest_values(indicators)

        print("\n最新指标值:")
        for name, value in list(latest.items())[:10]:
            print(f"{name}: {value:.2f}" if not np.isnan(value) else f"{name}: N/A")

        # 测试形态识别
        recognizer = PatternRecognizer(data)
        patterns = recognizer.detect_all_patterns()

        print(f"\n识别到的形态: {len(patterns)}")
        for name, info in patterns.items():
            print(f"  {name}: {info['type']} - {info['strength']}")
