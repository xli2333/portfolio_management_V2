"""
Signal Generator Module
生成交易信号和综合评分
"""

import numpy as np
from typing import Dict, List
from config import SIGNAL_THRESHOLDS


class SignalGenerator:
    """交易信号生成器"""

    def __init__(self, data, indicators: Dict, patterns: Dict):
        """
        初始化

        Args:
            data: 原始数据
            indicators: 技术指标字典
            patterns: 形态识别结果
        """
        self.data = data
        self.indicators = indicators
        self.patterns = patterns
        self.latest_close = data['close'].iloc[-1]

    def generate_all_signals(self) -> Dict:
        """生成所有交易信号"""
        signals = {}

        # 1. MACD信号
        signals['MACD'] = self._macd_signal()

        # 2. RSI信号
        signals['RSI'] = self._rsi_signal()

        # 3. KDJ信号
        signals['KDJ'] = self._kdj_signal()

        # 4. 布林带信号
        signals['Bollinger'] = self._bollinger_signal()

        # 5. 移动平均线信号
        signals['MA'] = self._ma_signal()

        # 6. 趋势信号
        signals['Trend'] = self._trend_signal()

        # 7. Williams %R信号
        signals['WilliamsR'] = self._willr_signal()

        # 8. CCI信号
        signals['CCI'] = self._cci_signal()

        # 9. 形态信号
        signals['Pattern'] = self._pattern_signal()

        # 10. 成交量信号
        signals['Volume'] = self._volume_signal()

        return signals

    def _macd_signal(self) -> Dict:
        """MACD信号"""
        macd = self.indicators['MACD'][-1]
        signal = self.indicators['MACD_Signal'][-1]
        hist = self.indicators['MACD_Hist'][-1]

        if np.isnan(macd) or np.isnan(signal):
            return {'signal': 'N/A', 'strength': 0, 'description': '数据不足'}

        # 金叉/死叉
        if macd > signal and hist > 0:
            strength = min(abs(hist) * 1000, 100)  # 归一化到0-100
            return {
                'signal': 'buy',
                'strength': int(strength),
                'description': f'金叉买入 (MACD={macd:.4f})'
            }
        elif macd < signal and hist < 0:
            strength = min(abs(hist) * 1000, 100)
            return {
                'signal': 'sell',
                'strength': int(strength),
                'description': f'死叉卖出 (MACD={macd:.4f})'
            }
        else:
            return {
                'signal': 'hold',
                'strength': 0,
                'description': '持有观望'
            }

    def _rsi_signal(self) -> Dict:
        """RSI信号"""
        rsi = self.indicators['RSI_14'][-1]

        if np.isnan(rsi):
            return {'signal': 'N/A', 'strength': 0, 'description': '数据不足'}

        oversold = SIGNAL_THRESHOLDS['RSI']['oversold']
        overbought = SIGNAL_THRESHOLDS['RSI']['overbought']

        if rsi < oversold:
            strength = int((oversold - rsi) / oversold * 100)
            return {
                'signal': 'buy',
                'strength': strength,
                'description': f'超卖买入 (RSI={rsi:.1f})'
            }
        elif rsi > overbought:
            strength = int((rsi - overbought) / (100 - overbought) * 100)
            return {
                'signal': 'sell',
                'strength': strength,
                'description': f'超买卖出 (RSI={rsi:.1f})'
            }
        else:
            return {
                'signal': 'neutral',
                'strength': 0,
                'description': f'中性 (RSI={rsi:.1f})'
            }

    def _kdj_signal(self) -> Dict:
        """KDJ信号"""
        k = self.indicators['K'][-1]
        d = self.indicators['D'][-1]
        j = self.indicators['J'][-1]

        if np.isnan(k) or np.isnan(d):
            return {'signal': 'N/A', 'strength': 0, 'description': '数据不足'}

        oversold = SIGNAL_THRESHOLDS['KDJ']['oversold']
        overbought = SIGNAL_THRESHOLDS['KDJ']['overbought']

        # 金叉且超卖
        if k > d and j < oversold:
            strength = int((oversold - j) / oversold * 100)
            return {
                'signal': 'buy',
                'strength': strength,
                'description': f'金叉且超卖 (K={k:.1f}, J={j:.1f})'
            }
        # 死叉且超买
        elif k < d and j > overbought:
            strength = int((j - overbought) / (100 - overbought) * 100)
            return {
                'signal': 'sell',
                'strength': strength,
                'description': f'死叉且超买 (K={k:.1f}, J={j:.1f})'
            }
        elif k > d:
            return {
                'signal': 'hold',
                'strength': 30,
                'description': f'金叉持有 (K={k:.1f})'
            }
        elif k < d:
            return {
                'signal': 'hold',
                'strength': -30,
                'description': f'死叉观望 (K={k:.1f})'
            }
        else:
            return {
                'signal': 'neutral',
                'strength': 0,
                'description': '中性'
            }

    def _bollinger_signal(self) -> Dict:
        """布林带信号"""
        upper = self.indicators['BB_Upper'][-1]
        lower = self.indicators['BB_Lower'][-1]
        pct_b = self.indicators['BB_PctB'][-1]

        if np.isnan(upper) or np.isnan(lower):
            return {'signal': 'N/A', 'strength': 0, 'description': '数据不足'}

        # 触及下轨
        if self.latest_close <= lower:
            return {
                'signal': 'buy',
                'strength': 80,
                'description': f'触及下轨买入 (%B={pct_b:.1f}%)'
            }
        # 触及上轨
        elif self.latest_close >= upper:
            return {
                'signal': 'sell',
                'strength': 80,
                'description': f'触及上轨卖出 (%B={pct_b:.1f}%)'
            }
        # 中轨附近
        else:
            return {
                'signal': 'neutral',
                'strength': 0,
                'description': f'正常范围 (%B={pct_b:.1f}%)'
            }

    def _ma_signal(self) -> Dict:
        """移动平均线信号"""
        sma5 = self.indicators['SMA_5'][-1]
        sma10 = self.indicators['SMA_10'][-1]
        sma20 = self.indicators['SMA_20'][-1]
        sma60 = self.indicators['SMA_60'][-1]

        if any(np.isnan(x) for x in [sma5, sma10, sma20, sma60]):
            return {'signal': 'N/A', 'strength': 0, 'description': '数据不足'}

        # 多头排列
        if sma5 > sma10 > sma20 > sma60:
            return {
                'signal': 'buy',
                'strength': 90,
                'description': '多头排列-强势上涨'
            }
        # 空头排列
        elif sma5 < sma10 < sma20 < sma60:
            return {
                'signal': 'sell',
                'strength': 90,
                'description': '空头排列-弱势下跌'
            }
        # 价格突破均线
        elif self.latest_close > sma20 and self.latest_close > sma60:
            return {
                'signal': 'buy',
                'strength': 60,
                'description': '价格站上中长期均线'
            }
        elif self.latest_close < sma20 and self.latest_close < sma60:
            return {
                'signal': 'sell',
                'strength': 60,
                'description': '价格跌破中长期均线'
            }
        else:
            return {
                'signal': 'neutral',
                'strength': 0,
                'description': '均线缠绕'
            }

    def _trend_signal(self) -> Dict:
        """趋势信号（ADX）"""
        adx = self.indicators['ADX'][-1]
        plus_di = self.indicators['+DI'][-1]
        minus_di = self.indicators['-DI'][-1]

        if np.isnan(adx):
            return {'signal': 'N/A', 'strength': 0, 'description': '数据不足'}

        strong_trend = SIGNAL_THRESHOLDS['ADX']['strong_trend']
        weak_trend = SIGNAL_THRESHOLDS['ADX']['weak_trend']

        # 强趋势
        if adx > strong_trend:
            if plus_di > minus_di:
                return {
                    'signal': 'buy',
                    'strength': int(adx),
                    'description': f'强势上涨趋势 (ADX={adx:.1f})'
                }
            else:
                return {
                    'signal': 'sell',
                    'strength': int(adx),
                    'description': f'强势下跌趋势 (ADX={adx:.1f})'
                }
        # 弱趋势
        elif adx < weak_trend:
            return {
                'signal': 'neutral',
                'strength': 0,
                'description': f'无明显趋势 (ADX={adx:.1f})'
            }
        # 中等趋势
        else:
            return {
                'signal': 'neutral',
                'strength': int(adx),
                'description': f'中等趋势 (ADX={adx:.1f})'
            }

    def _willr_signal(self) -> Dict:
        """Williams %R信号"""
        willr = self.indicators['WILLR'][-1]

        if np.isnan(willr):
            return {'signal': 'N/A', 'strength': 0, 'description': '数据不足'}

        oversold = SIGNAL_THRESHOLDS['WILLR']['oversold']
        overbought = SIGNAL_THRESHOLDS['WILLR']['overbought']

        if willr < oversold:
            strength = int((oversold - willr) / abs(oversold) * 100)
            return {
                'signal': 'buy',
                'strength': strength,
                'description': f'超卖 (WR={willr:.1f})'
            }
        elif willr > overbought:
            strength = int((willr - overbought) / abs(overbought) * 100)
            return {
                'signal': 'sell',
                'strength': strength,
                'description': f'超买 (WR={willr:.1f})'
            }
        else:
            return {
                'signal': 'neutral',
                'strength': 0,
                'description': f'中性 (WR={willr:.1f})'
            }

    def _cci_signal(self) -> Dict:
        """CCI信号"""
        cci = self.indicators['CCI'][-1]

        if np.isnan(cci):
            return {'signal': 'N/A', 'strength': 0, 'description': '数据不足'}

        if cci < -100:
            strength = min(int(abs(cci + 100) / 2), 100)
            return {
                'signal': 'buy',
                'strength': strength,
                'description': f'超卖 (CCI={cci:.1f})'
            }
        elif cci > 100:
            strength = min(int((cci - 100) / 2), 100)
            return {
                'signal': 'sell',
                'strength': strength,
                'description': f'超买 (CCI={cci:.1f})'
            }
        else:
            return {
                'signal': 'neutral',
                'strength': 0,
                'description': f'正常 (CCI={cci:.1f})'
            }

    def _pattern_signal(self) -> Dict:
        """形态信号"""
        if not self.patterns:
            return {
                'signal': 'neutral',
                'strength': 0,
                'description': '未识别到明显形态'
            }

        bullish_count = sum(1 for p in self.patterns.values() if p['type'] == 'bullish')
        bearish_count = sum(1 for p in self.patterns.values() if p['type'] == 'bearish')

        if bullish_count > bearish_count:
            strength = min(bullish_count * 30, 100)
            pattern_names = [name for name, p in self.patterns.items() if p['type'] == 'bullish']
            return {
                'signal': 'buy',
                'strength': strength,
                'description': f'看涨形态: {", ".join(pattern_names[:2])}'
            }
        elif bearish_count > bullish_count:
            strength = min(bearish_count * 30, 100)
            pattern_names = [name for name, p in self.patterns.items() if p['type'] == 'bearish']
            return {
                'signal': 'sell',
                'strength': strength,
                'description': f'看跌形态: {", ".join(pattern_names[:2])}'
            }
        else:
            return {
                'signal': 'neutral',
                'strength': 0,
                'description': '形态信号中性'
            }

    def _volume_signal(self) -> Dict:
        """成交量信号"""
        if len(self.data) < 6:
            return {'signal': 'N/A', 'strength': 0, 'description': '数据不足'}

        # 计算5日平均成交量
        recent_volume = self.data['volume'].iloc[-5:].mean()
        today_volume = self.data['volume'].iloc[-1]

        volume_ratio = today_volume / recent_volume

        # 放量上涨
        if volume_ratio >= 2 and self.data['change_pct'].iloc[-1] > 0:
            return {
                'signal': 'buy',
                'strength': min(int(volume_ratio * 30), 100),
                'description': f'放量上涨 (量比={volume_ratio:.1f})'
            }
        # 放量下跌
        elif volume_ratio >= 2 and self.data['change_pct'].iloc[-1] < 0:
            return {
                'signal': 'sell',
                'strength': min(int(volume_ratio * 30), 100),
                'description': f'放量下跌 (量比={volume_ratio:.1f})'
            }
        # 缩量
        elif volume_ratio < 0.5:
            return {
                'signal': 'neutral',
                'strength': 0,
                'description': f'缩量 (量比={volume_ratio:.1f})'
            }
        else:
            return {
                'signal': 'neutral',
                'strength': 0,
                'description': f'正常量能 (量比={volume_ratio:.1f})'
            }

    def calculate_综合评分(self, signals: Dict) -> Dict:
        """计算综合评分"""
        buy_strength = 0
        sell_strength = 0
        total_signals = 0

        for name, signal in signals.items():
            if signal['signal'] == 'N/A':
                continue

            total_signals += 1

            if signal['signal'] == 'buy':
                buy_strength += signal['strength']
            elif signal['signal'] == 'sell':
                sell_strength += signal['strength']

        # 计算综合得分（-100到+100）
        if total_signals == 0:
            score = 0
        else:
            score = (buy_strength - sell_strength) / total_signals

        # 确定操作建议
        if score > 50:
            recommendation = '强烈买入'
        elif score > 20:
            recommendation = '买入'
        elif score > -20:
            recommendation = '持有观望'
        elif score > -50:
            recommendation = '卖出'
        else:
            recommendation = '强烈卖出'

        return {
            'score': score,
            'recommendation': recommendation,
            'buy_signals': sum(1 for s in signals.values() if s['signal'] == 'buy'),
            'sell_signals': sum(1 for s in signals.values() if s['signal'] == 'sell'),
            'neutral_signals': sum(1 for s in signals.values() if s['signal'] in ['neutral', 'hold']),
        }
