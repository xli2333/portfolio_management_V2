"""Flask web UI for Stock Technical Analyzer (ASCII-safe)
- API: /analyze returns structured analysis with OHLCV & advanced indicators
- API: /export_pdf generates PDF with chart (SuperTrend/Ichimoku overlays)
"""

import sys
# Force UTF-8 for stdout (fixes Windows console issues)
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime
import os
import tempfile
import shutil
import numpy as np
from flask_cors import CORS
from portfolio_service import PortfolioService
from data_fetcher import DataFetcher
from knowledge_service import KnowledgeService
from report_generator import create_chat_pdf, create_markdown_pdf
from analyst_agent import AnalystAgent

# Initialize services
portfolio_service = PortfolioService()
knowledge_service = KnowledgeService()
analyst_agent = AnalystAgent()

# PDF reporting is disabled for local testing.
HAVE_REPORT = False

# Configure Chinese Fonts
CHINESE_FONT = 'Helvetica'  # Default fallback


app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)  # Enable CORS for all routes

# Ensure directories exist (for local dev mainly)
os.makedirs('output', exist_ok=True)
os.makedirs('static', exist_ok=True)


@app.errorhandler(500)
def internal_error(error):
    import traceback
    traceback.print_exc()
    return jsonify({'error': 'Internal Server Error', 'details': str(error)}), 500

@app.route('/')
def index():
    return send_file(os.path.join('static', 'index.html'))

# --- Portfolio APIs ---

@app.route('/api/portfolio', methods=['GET'])
def get_portfolio():
    try:
        user_id = request.headers.get('User-ID', 'anonymous')
        
        # 1. Get holdings from DB/File
        holdings = portfolio_service.get_portfolio(user_id)
        if not holdings:
            return jsonify({'overview': {'total_market_value': 0, 'total_pl': 0, 'total_cost': 0, 'day_pl': 0, 'total_pl_pct': 0, 'currency': 'CNY'}, 'holdings': []})

        # 2. Extract symbols to fetch realtime price
        symbols = [h['symbol'] for h in holdings]
        
        # 3. Fetch Realtime Prices (Batch)
        fetcher = DataFetcher()
        realtime_data = fetcher.get_realtime_batch(symbols)
        
        # 4. Compute Portfolio Metrics
        enriched_holdings = []
        
        # Currency Subtotals
        total_mv_cny = 0.0
        total_cost_cny = 0.0
        total_day_pl_cny = 0.0
        
        total_mv_usd = 0.0
        total_cost_usd = 0.0
        total_day_pl_usd = 0.0
        
        has_us_stock = False

        for h in holdings:
            symbol = h['symbol']
            shares = h.get('shares', 0)
            cost_basis = h.get('cost_basis', 0.0)
            
            rt = realtime_data.get(symbol, {'price': 0, 'change_pct': 0, 'name': symbol})
            current_price = rt['price']
            day_change_pct = rt['change_pct']
            name = rt['name']
            
            # Determine Currency
            is_us = not symbol.isdigit()
            currency = 'USD' if is_us else 'CNY'
            if is_us: has_us_stock = True
            
            market_value = current_price * shares
            cost_value = cost_basis * shares
            unrealized_pl = market_value - cost_value
            unrealized_pl_pct = (unrealized_pl / cost_value * 100) if cost_value else 0
            
            prev_close = current_price / (1 + day_change_pct/100) if (1 + day_change_pct/100) != 0 else current_price
            day_pl = (current_price - prev_close) * shares

            # Accumulate Subtotals
            if currency == 'USD':
                total_mv_usd += market_value
                total_cost_usd += cost_value
                total_day_pl_usd += day_pl
            else:
                total_mv_cny += market_value
                total_cost_cny += cost_value
                total_day_pl_cny += day_pl

            enriched_holdings.append({
                'symbol': symbol,
                'name': name,
                'shares': shares,
                'cost_basis': cost_basis,
                'current_price': current_price,
                'market_value': market_value,
                'unrealized_pl': unrealized_pl,
                'unrealized_pl_pct': unrealized_pl_pct,
                'day_change_pct': day_change_pct,
                'day_pl': day_pl,
                'currency': currency
            })
            
        # 5. Determine Reporting Currency and Consolidate
        # Rule: STRICTLY FORCE USD for everything as requested.
        # "Abandon real-time exchange rate, use 7.1 directly. USD Priority!!"
        report_currency = 'USD'
        
        final_mv = 0.0
        final_cost = 0.0
        final_day_pl = 0.0
        
        # Fixed Rate
        rate = 7.1
        
        # Convert CNY parts to USD
        final_mv = total_mv_usd + (total_mv_cny / rate)
        final_cost = total_cost_usd + (total_cost_cny / rate)
        final_day_pl = total_day_pl_usd + (total_day_pl_cny / rate)
            
        total_pl = final_mv - final_cost
        total_pl_pct = (total_pl / final_cost * 100) if final_cost else 0

        overview = {
            'total_market_value': final_mv,
            'total_cost': final_cost,
            'total_pl': total_pl,
            'total_pl_pct': total_pl_pct,
            'day_pl': final_day_pl,
            'currency': report_currency,
            'exchange_rate': rate
        }

        return jsonify({
            'overview': overview,
            'holdings': enriched_holdings
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/portfolio/add', methods=['POST'])
def add_portfolio_item():
    try:
        user_id = request.headers.get('User-ID', 'anonymous')
        data = request.get_json(force=True)
        symbol = data.get('symbol')
        quantity = data.get('quantity')
        cost = data.get('cost')
        
        if not symbol or quantity is None or cost is None:
            return jsonify({'error': 'Missing fields'}), 400
            
        result = portfolio_service.add_stock(user_id, symbol, quantity, cost)
        if result.get('status') == 'error':
             return jsonify({'error': result.get('msg')}), 500
             
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/portfolio/update', methods=['POST'])
def update_portfolio_item():
    """Update an existing stock holding."""
    try:
        user_id = request.headers.get('User-ID', 'anonymous')
        data = request.get_json(force=True)
        symbol = data.get('symbol')
        quantity = data.get('quantity')
        cost = data.get('cost')
        
        if not symbol or quantity is None or cost is None:
            return jsonify({'error': 'Missing fields'}), 400
            
        # Reusing update_stock logic (which wraps add_stock with upsert)
        result = portfolio_service.update_stock(user_id, symbol, quantity, cost)
        if result.get('status') == 'error':
             return jsonify({'error': result.get('msg')}), 500
             
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/portfolio/analysis', methods=['GET'])
def get_portfolio_analysis():
    """
    Advanced Portfolio Analysis:
    - Fetches ~1 year history for all holdings.
    - Computes simulated historical portfolio value (assuming current shares held constant).
    - Metrics: Sharpe, Volatility, MaxDrawdown, Correlation Matrix.
    """
    try:
        import pandas as pd
        import numpy as np

        user_id = request.headers.get('User-ID', 'anonymous')

        # 1. Get Holdings
        holdings = portfolio_service.get_portfolio(user_id)
        if not holdings:
             return jsonify({'error': 'Portfolio is empty'}), 400

        # 2. Fetch History (Batch-like)
        fetcher = DataFetcher()
        # We need a common date index.
        # Strategy: Fetch all, put into a dict of Series, then concat.
        
        price_series = {}
        shares_map = {}
        
        for h in holdings:
            symbol = h['symbol']
            shares = h.get('shares', 0)
            if shares <= 0: continue
            
            # Fetch ~1 year (252 trading days -> ~365 days)
            # Using 400 days to be safe for holidays/weekends
            df = fetcher.get_stock_data(symbol, days=400, period='daily')
            
            if df is not None and not df.empty:
                # Ensure date is datetime
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                
                # Keep only close price
                price_series[symbol] = df['close']
                shares_map[symbol] = shares
        
        if not price_series:
            return jsonify({'error': 'Could not fetch historical data'}), 500

        # 3. Align Data (Inner Join to ensure valid data for all)
        # If inner join is too strict (e.g. one stock is new), outer join + ffill might be better.
        # Let's use Outer Join + Forward Fill + Dropna(any) for the start
        prices_df = pd.DataFrame(price_series)
        prices_df.sort_index(inplace=True)
        prices_df.fillna(method='ffill', inplace=True)
        prices_df.dropna(inplace=True) # Drop start period where some stocks didn't exist/have data
        
        if prices_df.empty:
             return jsonify({'error': 'Insufficient overlapping data for analysis'}), 400
             
        # 4. Calculate Portfolio Value Curve
        # Value_t = Sum(Price_i_t * Shares_i)
        portfolio_value = pd.Series(0.0, index=prices_df.index)
        for symbol in prices_df.columns:
            portfolio_value += prices_df[symbol] * shares_map.get(symbol, 0)
            
        # 5. Calculate Metrics
        # Daily Returns
        returns = portfolio_value.pct_change().dropna()
        
        if len(returns) < 10:
             return jsonify({'error': 'Not enough data points for metrics'}), 400

        # Annualization Factor (A-shares ~242, US ~252, let's use 252)
        TRADING_DAYS = 252
        
        # Cumulative Return
        total_return = (portfolio_value.iloc[-1] / portfolio_value.iloc[0]) - 1
        
        # Annualized Return (CAGR approximation)
        years = len(returns) / TRADING_DAYS
        annual_return = ((1 + total_return) ** (1 / years)) - 1 if years > 0 else 0
        
        # Volatility (Annualized Std Dev)
        volatility = returns.std() * np.sqrt(TRADING_DAYS)
        
        # Sharpe Ratio (Risk Free = 3%)
        rf = 0.03
        sharpe = (annual_return - rf) / volatility if volatility != 0 else 0
        
        # Max Drawdown
        rolling_max = portfolio_value.cummax()
        drawdown = (portfolio_value - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        
        # 6. Correlation Matrix
        # Calculate correlation of returns between individual assets
        asset_returns = prices_df.pct_change().dropna()
        corr_matrix = asset_returns.corr()
        
        # Format Correlation for Frontend (Heatmap friendly)
        # { nodes: [symbols], links: [{source, target, value}] } or just a 2D grid
        # Let's return a simple grid: { symbols: [], matrix: [[1, 0.5], [0.5, 1]] }
        corr_symbols = list(corr_matrix.columns)
        corr_values = corr_matrix.where(pd.notnull(corr_matrix), None).values.tolist()
        
        # 7. Prepare Response
        
        # Chart Data (for Lightweight Charts)
        # Format: { time: 'yyyy-mm-dd', value: 123.45 }
        chart_data = []
        for dt, val in portfolio_value.items():
            chart_data.append({
                'time': dt.strftime('%Y-%m-%d'),
                'value': val
            })

        analysis_result = {
            'metrics': {
                'total_return_pct': float(total_return * 100),
                'annual_return_pct': float(annual_return * 100),
                'volatility_pct': float(volatility * 100),
                'sharpe_ratio': float(sharpe),
                'max_drawdown_pct': float(max_drawdown * 100)
            },
            'chart_data': chart_data,
            'correlation': {
                'symbols': corr_symbols,
                'matrix': corr_values
            },
            'period_days': len(returns)
        }
        
        return jsonify(_clean_nan_values(analysis_result))

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/portfolio/remove', methods=['DELETE']) # Or POST if preferred
def remove_portfolio_item():
    try:
        user_id = request.headers.get('User-ID', 'anonymous')
        symbol = request.args.get('symbol')
        if not symbol:
             # Try JSON body
             data = request.get_json(silent=True) or {}
             symbol = data.get('symbol')
        
        if not symbol:
             return jsonify({'error': 'Missing symbol'}), 400

        result = portfolio_service.remove_stock(user_id, symbol)
        if result.get('status') == 'error':
             return jsonify({'error': result.get('msg')}), 500
             
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- Knowledge Base APIs ---

@app.route('/api/knowledge/upload', methods=['POST'])
def upload_document():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        file = request.files['file']
        symbol = request.form.get('symbol')
        
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        if not symbol:
            return jsonify({'error': 'Missing symbol'}), 400
            
        # Validate PDF
        if not file.filename.lower().endswith('.pdf'):
             return jsonify({'error': 'Only PDF files are allowed'}), 400

        result = knowledge_service.save_document(symbol, file, file.filename)
        if "error" in result:
             return jsonify(result), 500
             
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/knowledge/list', methods=['GET'])
def list_documents():
    symbol = request.args.get('symbol')
    if not symbol:
        return jsonify({'error': 'Missing symbol'}), 400
    try:
        docs = knowledge_service.list_documents(symbol)
        return jsonify(docs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/knowledge/delete', methods=['DELETE'])
def delete_document():
    doc_id = request.args.get('doc_id')
    if not doc_id:
        return jsonify({'error': 'Missing doc_id'}), 400
    try:
        success = knowledge_service.delete_document(doc_id)
        if success:
            return jsonify({'status': 'success'})
        else:
            return jsonify({'error': 'Document not found or delete failed'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/knowledge/save_chat', methods=['POST'])
def save_chat_to_knowledge():
    try:
        data = request.get_json(force=True)
        symbol = data.get('symbol')
        messages = data.get('messages') # List of strings
        
        if not symbol or not messages:
            return jsonify({'error': 'Missing symbol or messages'}), 400
            
        # Generate PDF
        pdf_bytes = create_chat_pdf(symbol, messages)
        
        # Save
        filename = f"chat_export_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        result = knowledge_service.save_document(symbol, pdf_bytes, filename, doc_type='chat_history')
        
        if "error" in result:
             return jsonify(result), 500
             
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/agent/generate_report', methods=['POST'])
def generate_agent_report():
    try:
        data = request.get_json(force=True)
        symbol = data.get('symbol')
        model = data.get('model') or 'gemini-2.5-pro'
        selected_file_ids = data.get('selected_file_ids') or []
        
        if not symbol:
            return jsonify({'error': 'Missing symbol'}), 400
            
        # 1. Get Context
        docs_text = knowledge_service.get_documents_content(selected_file_ids)
        
        # 2. Run Agent
        report_text = analyst_agent.generate_deep_research_report(symbol, docs_text, model)
        if report_text.startswith("Error") or report_text.startswith("Agent Error"):
             return jsonify({'error': report_text}), 500
             
        # 3. Generate PDF
        pdf_bytes = create_markdown_pdf(symbol, report_text)
        
        # 4. Save to Knowledge Base
        filename = f"DeepReport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        save_result = knowledge_service.save_document(symbol, pdf_bytes, filename, doc_type='ai_report')
        
        return jsonify({
            'status': 'success',
            'report_text': report_text,
            'file_record': save_result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- End Portfolio APIs ---

@app.route('/analyze', methods=['GET', 'POST'])

def analyze():
    try:
        if request.method == 'POST':
             data = request.get_json(force=True)
             symbol = (data.get('symbol') or '').strip().upper()
             period = (data.get('period') or 'daily').strip()
        else:
             symbol = (request.args.get('symbol') or '').strip().upper()
             period = (request.args.get('period') or 'daily').strip()

        if not symbol:
            return jsonify({'error': 'Please enter a stock symbol'}), 400

        try:
            from analyzer import StockAnalyzer
        except Exception as e:
            return jsonify({'error': f'Missing backend dependency (maybe TA-Lib/akshare): {e}'}), 500

        analyzer = StockAnalyzer(use_proxy=True)
        # Use longer history for weekly/monthly
        days = 400
        if period == 'weekly': days = 500
        if period == 'monthly': days = 2000
        
        if not analyzer.analyze(symbol, days=days, period=period):
            error_msg = analyzer.last_error or 'Analysis failed, check symbol or network'
            print(f"[Error] /analyze failed for {symbol}: {error_msg}")
            return jsonify({'error': error_msg}), 400

        # OHLCV for charting
        try:
            ohlcv = []
            if analyzer.data is not None and len(analyzer.data) > 0:
                for _, row in analyzer.data.iterrows():
                    d = str(row['date'])
                    if len(d) == 8 and d.isdigit():
                        d = f"{d[0:4]}-{d[4:6]}-{d[6:8]}"
                    ohlcv.append({
                        'date': d,
                        'open': float(row['open']),
                        'high': float(row['high']),
                        'low': float(row['low']),
                        'close': float(row['close']),
                        'volume': float(row['volume']) if 'volume' in row else None,
                    })

            # Convert advanced indicators to JSON-safe
            def _to_safe_list(arr):
                safe = []
                for x in arr:
                    if isinstance(x, float) and (x != x):  # NaN -> None
                        safe.append(None)
                    else:
                        safe.append(x)
                return safe

            adv_raw = getattr(analyzer, 'extra_indicators', {}) or {}
            adv_safe = {}
            for k, v in adv_raw.items():
                if isinstance(v, np.ndarray):
                    adv_safe[k] = _to_safe_list(v.tolist())
                elif isinstance(v, (list, tuple)):
                    adv_safe[k] = _to_safe_list(v)
                else:
                    adv_safe[k] = v

            result = {
                'stock_info': analyzer.stock_info,
                'price_info': analyzer.get_price_info(),
                'key_indicators': analyzer.get_key_indicators(),
                'ma_levels': analyzer.get_ma_levels(),
                'patterns': analyzer.patterns,
                'signals': analyzer.signals,
                'comprehensive_score': analyzer.综合评分,
                'advanced_indicators': adv_safe,
                'ohlcv': ohlcv,
            }
            
            # Clean all NaN/Infinity values before JSON serialization
            result = _clean_nan_values(result)
            return jsonify(result)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'error': 'Serialization Error', 'details': str(e)}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/stock_list')
def stock_list():
    try:
        from data_fetcher import DataFetcher
        fetcher = DataFetcher(use_proxy=True)
        stocks = fetcher.get_stock_list()
        return jsonify(stocks.to_dict('records')[:100])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stock_summary')
def stock_summary():
    symbol = request.args.get('symbol', '').strip().upper()
    if not symbol:
        return jsonify({'error': 'Missing symbol'}), 400
        
    try:
        # Delegate to portfolio_service to handle caching and AI call
        summary = portfolio_service.get_company_summary(symbol)
        return jsonify({'summary': summary})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json(force=True)
        symbol = (data.get('symbol') or '').strip().upper()
        message = (data.get('message') or '').strip()
        history = data.get('history') or []
        selected_file_ids = data.get('selected_file_ids') or []
        model = data.get('model') or 'gemini-2.5-flash'
        
        if not symbol or not message:
            return jsonify({'error': 'Missing symbol or message'}), 400
            
        reply = portfolio_service.chat_with_gemini(symbol, message, history, selected_file_ids, model)
        return jsonify({'reply': reply})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})


def _to_datetime_index(df):
    import pandas as pd
    import numpy as np
    data = df.copy()
    if not np.issubdtype(data['date'].dtype, np.datetime64):
        data['date'] = data['date'].astype(str).apply(
            lambda d: datetime.strptime(d, '%Y%m%d') if d.isdigit() and len(d) == 8 else pd.to_datetime(d)
        )
    data = data.set_index('date')
    data.index.name = 'Date'
    return data


def _clean_nan_values(obj):
    """Recursively replace NaN/Infinity with None and convert numpy types for JSON."""
    import math
    import numpy as np
    
    if isinstance(obj, dict):
        return {k: _clean_nan_values(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_clean_nan_values(item) for item in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return float(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
         return _clean_nan_values(obj.tolist())
    else:
        return obj


def _generate_chart_png(analyzer, png_path: str):
    if not HAVE_REPORT:
        raise RuntimeError('reportlab/mplfinance not installed, cannot export PDF')

    import pandas as pd

    df = analyzer.data.copy()
    df = _to_datetime_index(df)
    cols_map = {'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}
    for k, v in cols_map.items():
        if k in df.columns:
            df[v] = df[k].astype(float)
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()

    add_plots = []
    # MA20 & MA60
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA60'] = df['Close'].rolling(window=60).mean()
    add_plots.append(mpf.make_addplot(df['MA20'], color='#2f7df6', width=1.2))
    add_plots.append(mpf.make_addplot(df['MA60'], color='#ffb703', width=1.2))

    # SuperTrend
    extra = getattr(analyzer, 'extra_indicators', {}) or {}
    st = extra.get('SuperTrend')
    if st is not None and len(st) == len(df):
        df['SuperTrend'] = pd.Series(st, index=df.index)
        add_plots.append(mpf.make_addplot(df['SuperTrend'], color='#26a69a', width=1.0))

    # Ichimoku cloud edges
    sa = extra.get('Ichimoku_SenkouA')
    sb = extra.get('Ichimoku_SenkouB')
    if sa is not None and sb is not None and len(sa) == len(df):
        df['SenkouA'] = pd.Series(sa, index=df.index)
        df['SenkouB'] = pd.Series(sb, index=df.index)
        add_plots.append(mpf.make_addplot(df['SenkouA'], color='#8bc34a', width=0.8, linestyle='--'))
        add_plots.append(mpf.make_addplot(df['SenkouB'], color='#e57373', width=0.8, linestyle='--'))

    # Configure Chinese font style
    # Use a style that supports Chinese (SimHei)
    my_style = mpf.make_mpf_style(base_mpf_style='yahoo', rc={'font.family': CHINESE_FONT, 'axes.unicode_minus': False})

    mpf.plot(
        df,
        type='candle',
        style=my_style,
        addplot=add_plots,
        volume=True,
        mav=(),
        savefig=dict(fname=png_path, dpi=160, bbox_inches='tight')
    )


def _generate_pdf_report(analyzer, pdf_path: str, chart_png_path: str):
    if not HAVE_REPORT:
        raise RuntimeError('reportlab not installed, cannot export PDF')

    c = canvas.Canvas(pdf_path, pagesize=A4)
    w, h = A4
    margin = 2 * cm
    y = h - margin

    # Cover
    c.setFillColorRGB(0.11, 0.19, 0.29)
    c.rect(0, 0, w, h, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    
    # Use the registered Chinese font (default size 24 for title)
    c.setFont(CHINESE_FONT, 24)
    c.drawString(margin, y - 1 * cm, 'Stock Technical Analysis Report')
    
    c.setFont(CHINESE_FONT, 14)
    stock_name = analyzer.stock_info.get('name') if analyzer.stock_info else ''
    stock_code = analyzer.stock_info.get('code') if analyzer.stock_info else ''
    c.drawString(margin, y - 2.2 * cm, f'{stock_name} ({stock_code})')
    
    c.setFont(CHINESE_FONT, 10)
    c.drawString(margin, y - 3.2 * cm, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    c.showPage()

    # Summary
    c.setFillColorRGB(1, 1, 1); c.rect(0, 0, w, h, fill=1, stroke=0)
    c.setFillColorRGB(0, 0, 0)
    c.setFont(CHINESE_FONT, 16); c.drawString(margin, h - margin, 'Summary')
    c.setFont(CHINESE_FONT, 11)
    price = analyzer.get_price_info()
    score = analyzer.综合评分 or {}
    lines = [
        f"Close: {price.get('close', 'NA')}",
        f"Change %: {price.get('change_pct', 0):+.2f}%",
        f"Volume: {price.get('volume', 0)}",
        f"Score: {score.get('score', 0):+.1f} / 100",
        f"Recommendation: {score.get('recommendation', 'NA')}",
        f"Regime: {score.get('regime', 'mixed')}",
    ]
    yy = h - margin - 1.2 * cm
    for line in lines:
        c.drawString(margin, yy, line); yy -= 0.8 * cm

    if os.path.exists(chart_png_path):
        img_w = w - 2 * margin
        img_h = img_w * 0.55
        c.drawImage(chart_png_path, margin, margin + 3 * cm, width=img_w, height=img_h, preserveAspectRatio=True)
    c.showPage()

    # Signals
    c.setFillColorRGB(1, 1, 1); c.rect(0, 0, w, h, fill=1, stroke=0)
    c.setFillColorRGB(0, 0, 0)
    c.setFont(CHINESE_FONT, 16); c.drawString(margin, h - margin, 'Signals (Top 15)')
    c.setFont(CHINESE_FONT, 10)
    sigs = analyzer.signals or {}
    ordered = sorted(
        [(k, v) for k, v in sigs.items() if v.get('signal') != 'N/A'],
        key=lambda kv: kv[1].get('strength', 0), reverse=True
    )[:15]
    yy = h - margin - 1.2 * cm
    for name, s in ordered:
        line = f"{name:15s} | {s.get('signal','-'):6s} | {s.get('strength',0):3d} | {s.get('description','')}"
        c.drawString(margin, yy, line)
        yy -= 0.7 * cm
        if yy < margin:
            c.showPage(); yy = h - margin

    c.showPage(); c.save()


# @app.route('/export_pdf')
# def export_pdf():
#     symbol = (request.args.get('symbol') or '').strip().upper()
#     if not symbol:
#         return jsonify({'error': 'missing symbol'}), 400

#     if not HAVE_REPORT:
#         return jsonify({'error': 'reportlab/mplfinance not available on server'}), 500

#     try:
#         from analyzer import StockAnalyzer
#     except Exception as e:
#         return jsonify({'error': f'Missing backend dependency: {e}'}), 500

#     analyzer = StockAnalyzer(use_proxy=True)
#     if not analyzer.analyze(symbol, days=120):
#         return jsonify({'error': 'analysis failed, check symbol or network'}), 400

#     # Use temporary directory for Vercel/Cloud compatibility
#     with tempfile.TemporaryDirectory() as tmpdirname:
#         ts = datetime.now().strftime('%Y%m%d_%H%M%S')
#         base = f"{symbol}_{ts}"
#         chart_path = os.path.join(tmpdirname, f"{base}_chart.png")
#         pdf_path = os.path.join(tmpdirname, f"{base}_report.pdf")

#         try:
#             _generate_chart_png(analyzer, chart_path)
#             _generate_pdf_report(analyzer, pdf_path, chart_path)

#             # Read file into memory to serve it
#             return send_file(pdf_path, as_attachment=True, download_name=f"{base}_report.pdf")
#         except Exception as e:
#             import traceback
#             traceback.print_exc()
#             return jsonify({'error': f'PDF Generation Error: {str(e)}'}), 500


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("  Stock Technical Analyzer - Web UI")
    print("  Visit: http://localhost:5000")
    print("=" * 60 + "\n")
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, use_reloader=False, threaded=False, host='0.0.0.0', port=port)