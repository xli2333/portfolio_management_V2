"""
Advanced signals with regime-aware weighting and improved scoring.
"""

from typing import Dict, Tuple
import numpy as np
import pandas as pd
from config import SIGNAL_THRESHOLDS, REGIME_THRESHOLDS


def _nan_to_num(x: float, default: float = 0.0) -> float:
    return default if (x is None or (isinstance(x, float) and (np.isnan(x) or np.isinf(x)))) else x


class AdvancedSignalGenerator:
    def __init__(self, data: pd.DataFrame, base_ind: Dict[str, np.ndarray], extra_ind: Dict[str, np.ndarray]):
        self.data = data
        self.base = base_ind
        self.extra = extra_ind
        self.close = data['close'].astype(float).values

        # Compute regime weights once
        self.regime, self.weights = self._detect_regime()

    def _detect_regime(self) -> Tuple[str, Dict[str, float]]:
        adx = float(self.base.get('ADX', np.array([np.nan]))[-1]) if 'ADX' in self.base else np.nan
        bb_w = float(self.base.get('BB_Width', self.extra.get('BB_Width', np.array([np.nan])))[-1]) if ('BB_Width' in self.base or 'BB_Width' in self.extra) else np.nan
        atr_pct = float(self.extra.get('ATR_Pct', np.array([np.nan]))[-1]) if 'ATR_Pct' in self.extra else np.nan

        adx_thr = REGIME_THRESHOLDS.get('ADX_trend', 25)
        bb_low = REGIME_THRESHOLDS.get('BB_width_low', 5.0)
        atr_thr = REGIME_THRESHOLDS.get('ATR_pct_trend', 2.0)

        # Rules: strong trend if ADX high and ATR% elevated; range if BB width very low
        if not np.isnan(adx) and adx >= adx_thr and (np.isnan(atr_pct) or atr_pct >= atr_thr):
            regime = 'trend'
        elif not np.isnan(bb_w) and bb_w <= bb_low:
            regime = 'range'
        else:
            regime = 'mixed'

        weights = {
            'trend': 2.0 if regime == 'trend' else (1.2 if regime == 'mixed' else 0.8),
            'range': 2.0 if regime == 'range' else (1.2 if regime == 'mixed' else 0.8),
            'volume': 1.0,
            'pattern': 1.0,
            'baseline': 1.0,
        }
        return regime, weights

    def generate(self) -> Dict[str, Dict]:
        s: Dict[str, Dict] = {}
        s['SuperTrend'] = self._supertrend_signal()
        s['Ichimoku'] = self._ichimoku_signal()
        s['Donchian'] = self._donchian_signal()
        s['KeltnerSqueeze'] = self._keltner_squeeze_signal()
        s['MoneyFlow'] = self._moneyflow_signal()
        s['PPO_TSI'] = self._ppo_tsi_signal()
        s['KAMA'] = self._kama_signal()
        s['ForceIndex'] = self._force_index_signal()
        s['Divergence'] = self._divergence_signal()
        return s

    def _divergence_signal(self) -> Dict:
        """
        Detect Regular Divergence (Bullish/Bearish) on RSI and MACD.
        Lookback window: 10-20 bars.
        """
        rsi = self.base.get('RSI')
        macd = self.base.get('MACD')
        
        if rsi is None or macd is None:
             return {'signal': 'N/A', 'strength': 0, 'description': '数据不足', 'category': 'pattern'}
             
        # Focus on last 20 bars for divergence
        lb = 20
        if len(self.close) < lb + 2:
             return {'signal': 'N/A', 'strength': 0, 'description': '数据不足', 'category': 'pattern'}
             
        price_win = self.close[-lb:]
        rsi_win = rsi[-lb:]
        macd_win = macd[-lb:]
        
        # Simple Peak/Valley detection (extremas)
        # This is a simplified heuristic. Real implementations use pivot points.
        
        price_low_idx = np.argmin(price_win)
        price_high_idx = np.argmax(price_win)
        
        rsi_low_idx = np.argmin(rsi_win)
        rsi_high_idx = np.argmax(rsi_win)
        
        # Bullish Divergence: Price Low is lower than previous, but RSI Low is higher?
        # Simplified Check: Price Min is at end, RSI Min is earlier? Or Price trend down, RSI trend up?
        
        # Use slope over the window for a robust check
        def get_slope(arr):
            if len(arr) < 2: return 0
            x = np.arange(len(arr))
            # Remove NaNs
            mask = ~np.isnan(arr)
            if np.sum(mask) < 2: return 0
            slope, _ = np.polyfit(x[mask], arr[mask], 1)
            return slope

        p_slope = get_slope(price_win)
        rsi_slope = get_slope(rsi_win)
        macd_slope = get_slope(macd_win)
        
        signal = 'neutral'
        desc = []
        strength = 0
        
        # Bullish Divergence: Price going down, RSI/MACD going up
        if p_slope < 0:
            if rsi_slope > 0.5: # Thresholds need tuning
                desc.append("RSI 底背离")
                strength += 40
            if macd_slope > 0.1:
                desc.append("MACD 底背离")
                strength += 40
            if strength > 0:
                signal = 'buy'
                
        # Bearish Divergence: Price going up, RSI/MACD going down
        elif p_slope > 0:
            if rsi_slope < -0.5:
                desc.append("RSI 顶背离")
                strength += 40
            if macd_slope < -0.1:
                desc.append("MACD 顶背离")
                strength += 40
            if strength > 0:
                signal = 'sell'
        
        if signal == 'neutral':
             return {'signal': 'neutral', 'strength': 0, 'description': '无背离', 'category': 'pattern'}
             
        return {
            'signal': signal, 
            'strength': min(strength, 90), 
            'description': ' & '.join(desc), 
            'category': 'pattern'
        }

    def _supertrend_signal(self) -> Dict:
        st_dir = self.extra.get('ST_Direction')
        st = self.extra.get('SuperTrend')
        if st_dir is None or st is None:
            return {'signal': 'N/A', 'strength': 0, 'description': '数据不足', 'category': 'trend'}
        direction = st_dir[-1]
        price = self.close[-1]
        dist = abs(_nan_to_num(price - st[-1]))
        rel = 0.0 if price == 0 else min(dist / price * 1000, 1.0)  # cap
        strength = int(50 + 50 * rel)
        if direction > 0 and price >= st[-1]:
            return {'signal': 'buy', 'strength': strength, 'description': 'SuperTrend 上行', 'category': 'trend'}
        elif direction < 0 and price <= st[-1]:
            return {'signal': 'sell', 'strength': strength, 'description': 'SuperTrend 下行', 'category': 'trend'}
        else:
            return {'signal': 'neutral', 'strength': 0, 'description': 'SuperTrend 中性', 'category': 'trend'}

    def _ichimoku_signal(self) -> Dict:
        tenkan = self.extra.get('Ichimoku_Tenkan')
        kijun = self.extra.get('Ichimoku_Kijun')
        sa = self.extra.get('Ichimoku_SenkouA')
        sb = self.extra.get('Ichimoku_SenkouB')
        chikou = self.extra.get('Ichimoku_Chikou')
        if any(x is None for x in [tenkan, kijun, sa, sb]):
            return {'signal': 'N/A', 'strength': 0, 'description': '数据不足', 'category': 'trend'}
        
        # Check for NaNs at the current index before computation to avoid RuntimeWarnings
        if np.isnan(sa[-1]) or np.isnan(sb[-1]):
            return {'signal': 'N/A', 'strength': 0, 'description': '一目云数据不足 (NaN)', 'category': 'trend'}
            
        price = self.close[-1]
        cloud_top = np.nanmax([sa[-1], sb[-1]])
        cloud_bottom = np.nanmin([sa[-1], sb[-1]])

        # Handle NaN values in cloud result (double check)
        if np.isnan(cloud_top) or np.isnan(cloud_bottom):
            return {'signal': 'N/A', 'strength': 0, 'description': '一目云数据不足', 'category': 'trend'}

        bullish = (price > cloud_top) and (tenkan[-1] > kijun[-1])
        bearish = (price < cloud_bottom) and (tenkan[-1] < kijun[-1])
        # optional chikou filter
        if chikou is not None and not np.isnan(chikou[-1]):
            bullish = bullish and chikou[-1] > price
            bearish = bearish and chikou[-1] < price
        span = cloud_top - cloud_bottom
        rel = 0.0 if span == 0 else min(abs(price - (cloud_top if bullish else cloud_bottom)) / span, 1.0)
        rel = _nan_to_num(rel, 0.0)  # Handle any remaining NaN
        strength = int(50 + 50 * rel)
        if bullish:
            return {'signal': 'buy', 'strength': strength, 'description': '一目多头云上方', 'category': 'trend'}
        elif bearish:
            return {'signal': 'sell', 'strength': strength, 'description': '一目空头云下方', 'category': 'trend'}
        return {'signal': 'neutral', 'strength': 0, 'description': '一目中性', 'category': 'trend'}

    def _donchian_signal(self) -> Dict:
        up = self.extra.get('Donchian_Upper')
        lo = self.extra.get('Donchian_Lower')
        if up is None or lo is None:
            return {'signal': 'N/A', 'strength': 0, 'description': '数据不足', 'category': 'trend'}
        price = self.close[-1]
        rng = up[-1] - lo[-1]
        if rng <= 0 or np.isnan(rng):
            return {'signal': 'neutral', 'strength': 0, 'description': '通道无效', 'category': 'trend'}
        if price >= up[-1]:
            return {'signal': 'buy', 'strength': 70, 'description': '唐奇安上沿突破', 'category': 'trend'}
        elif price <= lo[-1]:
            return {'signal': 'sell', 'strength': 70, 'description': '唐奇安下沿跌破', 'category': 'trend'}
        else:
            return {'signal': 'neutral', 'strength': 0, 'description': '通道内震荡', 'category': 'range'}

    def _keltner_squeeze_signal(self) -> Dict:
        ku = self.extra.get('Keltner_Upper')
        kl = self.extra.get('Keltner_Lower')
        bu = self.base.get('BB_Upper')
        bl = self.base.get('BB_Lower')
        if any(x is None for x in [ku, kl, bu, bl]):
            return {'signal': 'N/A', 'strength': 0, 'description': '数据不足', 'category': 'range'}
        price = self.close[-1]
        squeeze_on = (bu[-1] < ku[-1]) and (bl[-1] > kl[-1])
        if squeeze_on and price > ku[-1]:
            return {'signal': 'buy', 'strength': 80, 'description': 'Squeeze 向上释放', 'category': 'trend'}
        elif squeeze_on and price < kl[-1]:
            return {'signal': 'sell', 'strength': 80, 'description': 'Squeeze 向下释放', 'category': 'trend'}
        elif squeeze_on:
            return {'signal': 'neutral', 'strength': 0, 'description': 'Squeeze 盘整', 'category': 'range'}
        else:
            return {'signal': 'neutral', 'strength': 0, 'description': '非Squeeze', 'category': 'range'}

    def _moneyflow_signal(self) -> Dict:
        mfi = self.extra.get('MFI')
        cmf = self.extra.get('CMF')
        if mfi is None or cmf is None:
            return {'signal': 'N/A', 'strength': 0, 'description': '数据不足', 'category': 'volume'}
        mfi_v = mfi[-1]
        cmf_v = cmf[-1]
        if np.isnan(mfi_v) or np.isnan(cmf_v):
            return {'signal': 'N/A', 'strength': 0, 'description': '数据不足', 'category': 'volume'}
        if mfi_v < 20 and cmf_v > 0:
            return {'signal': 'buy', 'strength': 70, 'description': f'MFI<20 & CMF>0 ({mfi_v:.1f},{cmf_v:.2f})', 'category': 'volume'}
        elif mfi_v > 80 and cmf_v < 0:
            return {'signal': 'sell', 'strength': 70, 'description': f'MFI>80 & CMF<0 ({mfi_v:.1f},{cmf_v:.2f})', 'category': 'volume'}
        else:
            return {'signal': 'neutral', 'strength': 0, 'description': f'MFI/CMF 中性 ({mfi_v:.1f},{cmf_v:.2f})', 'category': 'volume'}

    def _ppo_tsi_signal(self) -> Dict:
        ppo = self.extra.get('PPO')
        ppo_sig = self.extra.get('PPO_Signal')
        tsi = self.extra.get('TSI')
        tsi_sig = self.extra.get('TSI_Signal')
        if any(x is None for x in [ppo, ppo_sig, tsi, tsi_sig]):
            return {'signal': 'N/A', 'strength': 0, 'description': '数据不足', 'category': 'trend'}
        ppo_bull = ppo[-1] > ppo_sig[-1]
        tsi_bull = tsi[-1] > tsi_sig[-1]
        if ppo_bull and tsi_bull:
            return {'signal': 'buy', 'strength': 75, 'description': 'PPO & TSI 同步看多', 'category': 'trend'}
        elif (not ppo_bull) and (not tsi_bull):
            return {'signal': 'sell', 'strength': 75, 'description': 'PPO & TSI 同步看空', 'category': 'trend'}
        else:
            return {'signal': 'neutral', 'strength': 0, 'description': 'PPO/TSI 分歧', 'category': 'trend'}

    def _kama_signal(self) -> Dict:
        kama = self.extra.get('KAMA')
        kama_slope = self.extra.get('KAMA_Slope')
        if kama is None or kama_slope is None:
            return {'signal': 'N/A', 'strength': 0, 'description': '数据不足', 'category': 'trend'}
        price = self.close[-1]
        slope = kama_slope[-1]
        if price > kama[-1] and slope > 0:
            return {'signal': 'buy', 'strength': 60, 'description': 'KAMA 上行', 'category': 'trend'}
        elif price < kama[-1] and slope < 0:
            return {'signal': 'sell', 'strength': 60, 'description': 'KAMA 下行', 'category': 'trend'}
        else:
            return {'signal': 'neutral', 'strength': 0, 'description': 'KAMA 中性', 'category': 'trend'}

    def _force_index_signal(self) -> Dict:
        fi = self.extra.get('ForceIndex')
        if fi is None:
            return {'signal': 'N/A', 'strength': 0, 'description': '数据不足', 'category': 'volume'}
        v = fi[-1]
        if np.isnan(v):
            return {'signal': 'N/A', 'strength': 0, 'description': '数据不足', 'category': 'volume'}
        if v > 0:
            return {'signal': 'buy', 'strength': min(int(abs(v) / (abs(v) + 1) * 100), 80), 'description': '正向资金推动', 'category': 'volume'}
        elif v < 0:
            return {'signal': 'sell', 'strength': min(int(abs(v) / (abs(v) + 1) * 100), 80), 'description': '负向资金施压', 'category': 'volume'}
        else:
            return {'signal': 'neutral', 'strength': 0, 'description': '资金中性', 'category': 'volume'}

    def score(self, signals: Dict[str, Dict]) -> Dict:
        # Merge base and advanced signals externally; here assume input already merged
        # Only directional signals contribute; category-weighted, strength 0-100 normalized
        total_weight = 0.0
        agg = 0.0
        buy_count = 0
        sell_count = 0
        neutral_count = 0

        for name, s in signals.items():
            sig = s.get('signal', 'neutral')
            if sig == 'N/A':
                continue
            category = s.get('category', 'baseline')
            weight = self.weights.get(category, 1.0)
            strength = float(_nan_to_num(s.get('strength', 0), 0.0)) / 100.0

            if sig == 'buy':
                agg += weight * strength
                total_weight += weight
                buy_count += 1
            elif sig == 'sell':
                agg -= weight * strength
                total_weight += weight
                sell_count += 1
            else:
                neutral_count += 1

        score = 0.0 if total_weight == 0 else 100.0 * agg / total_weight

        # Recommendation
        if score > 50:
            rec = '强烈买入'
        elif score > 20:
            rec = '买入'
        elif score > -20:
            rec = '持有观望'
        elif score > -50:
            rec = '卖出'
        else:
            rec = '强烈卖出'

        return {
            'score': score,
            'recommendation': rec,
            'buy_signals': buy_count,
            'sell_signals': sell_count,
            'neutral_signals': neutral_count,
            'regime': self.regime,
        }
