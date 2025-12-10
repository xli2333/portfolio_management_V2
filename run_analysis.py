
import sys
import os
import json
import argparse
from datetime import datetime
from analyzer import StockAnalyzer

def save_text_report(analyzer, filepath):
    """Generate a readable text report."""
    with open(filepath, 'w', encoding='utf-8') as f:
        # Header
        info = analyzer.stock_info
        price = analyzer.get_price_info()
        score = analyzer.综合评分
        
        f.write("="*50 + "\n")
        f.write(f"  STOCK ANALYSIS REPORT: {info.get('name')} ({info.get('code')})\n")
        f.write(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write("="*50 + "\n\n")
        
        # Price Section
        f.write(f"1. MARKET DATA\n")
        f.write(f"   Price:  {price.get('close')}\n")
        f.write(f"   Change: {price.get('change_pct'):.2f}%\n")
        f.write(f"   Volume: {price.get('volume'):,.0f}\n")
        f.write(f"   Trend:  {score.get('regime', 'N/A').upper()}\n\n")
        
        # Score Section
        f.write(f"2. TECHNICAL SCORE\n")
        f.write(f"   Total Score:    {score.get('score'):.1f} / 100\n")
        f.write(f"   Recommendation: {score.get('recommendation')}\n")
        f.write(f"   Buy Signals:    {score.get('buy_signals')}\n")
        f.write(f"   Sell Signals:   {score.get('sell_signals')}\n\n")
        
        # Key Indicators
        f.write(f"3. KEY INDICATORS\n")
        inds = analyzer.get_key_indicators()
        f.write(f"   RSI (14):    {inds.get('RSI_14'):.2f}\n")
        f.write(f"   MACD:        {inds.get('MACD'):.3f}\n")
        f.write(f"   KDJ (K/D/J): {inds.get('K'):.1f} / {inds.get('D'):.1f} / {inds.get('J'):.1f}\n")
        
        # Advanced Indicators
        extra = analyzer.extra_indicators
        if extra:
             f.write(f"   SuperTrend:  {extra.get('SuperTrend')[-1]:.2f} (Dir: {extra.get('ST_Direction')[-1]})\n")
             f.write(f"   VWMA:        {extra.get('VWMA')[-1]:.2f}\n")
        
        # Active Signals
        f.write(f"\n4. ACTIVE SIGNALS\n")
        for name, sig in analyzer.signals.items():
            if sig.get('signal') != 'neutral' and sig.get('signal') != 'N/A':
                arrow = "↑ BUY" if sig['signal'] == 'buy' else "↓ SELL"
                f.write(f"   [{arrow}] {name:<15} | Strength: {sig.get('strength')} | {sig.get('description')}\n")
        
        f.write("\n" + "="*50 + "\n")

def main():
    parser = argparse.ArgumentParser(description='Run Stock Technical Analysis (Backend)')
    parser.add_argument('symbol', type=str, help='Stock Code (e.g. 600000)')
    parser.add_argument('--period', type=str, default='daily', choices=['daily', 'weekly', 'monthly'], help='Timeframe')
    parser.add_argument('--days', type=int, default=150, help='Days of history to fetch')
    parser.add_argument('--proxy', action='store_true', help='Enable default proxy if configured')
    
    args = parser.parse_args()
    
    print(f"\nAnalyzing {args.symbol} ({args.period})...")
    
    # Initialize Analyzer
    # Note: use_proxy=False is default in our clean architecture, but kept for compatibility
    analyzer = StockAnalyzer(use_proxy=args.proxy)
    
    if not analyzer.analyze(args.symbol, days=args.days, period=args.period):
        print("[!] Analysis Failed. Check network connection or stock code.")
        return

    # Create Output Directory
    os.makedirs('output', exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_path = os.path.join('output', f"{args.symbol}_{args.period}_{timestamp}")
    
    # 1. Save JSON (Raw Data)
    analyzer.export_to_json(f"{base_path}.json")
    
    # 2. Save Text Report (Readable)
    save_text_report(analyzer, f"{base_path}.txt")
    
    # 3. Print Summary to Console
    info = analyzer.stock_info
    score = analyzer.综合评分
    price = analyzer.get_price_info()
    
    print("\n" + "="*40)
    print(f"  RESULT: {info['name']} ({args.symbol})")
    print("="*40)
    print(f"  Price:  {price['close']} ({price['change_pct']:.2f}%)")
    print(f"  Score:  {score['score']:.1f} -> {score['recommendation']}")
    print(f"  Regime: {score['regime']}")
    print("-"*40)
    print(f"[OK] Reports saved to:")
    print(f"   - {base_path}.txt")
    print(f"   - {base_path}.json")
    print("="*40 + "\n")

if __name__ == '__main__':
    main()
