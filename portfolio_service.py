import os
import json
import logging
# import requests # No longer needed
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv
import google.generativeai as genai # New import

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PortfolioService:
    def __init__(self):
        self.supabase_url = os.environ.get("SUPABASE_URL")
        self.supabase_key = os.environ.get("SUPABASE_KEY")
        self.local_file = "portfolio.json"
        self.summary_file = "company_summaries.json"
        self.use_supabase = bool(self.supabase_url and self.supabase_key)
        self.gemini_key = os.environ.get("GEMINI_API_KEY")
        
        if self.gemini_key:
            genai.configure(api_key=self.gemini_key)
            self.gemini_client = genai.GenerativeModel("gemini-2.5-pro") # Initialize model here
        else:
            self.gemini_client = None
            
        if self.use_supabase:
            logger.info("Initializing PortfolioService with Supabase")
            try:
                self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
                self.use_supabase = False
        
        if not self.use_supabase:
            logger.info("Initializing PortfolioService with Local File Storage")
            self._init_local_storage()
            self._init_summary_storage()

    def _init_local_storage(self):
        """Initialize local JSON file if it doesn't exist."""
        if not os.path.exists(self.local_file):
            with open(self.local_file, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def _init_summary_storage(self):
        """Initialize local summary cache."""
        if not os.path.exists(self.summary_file):
            with open(self.summary_file, 'w', encoding='utf-8') as f:
                json.dump({}, f)

    def get_portfolio(self, user_id):
        """Retrieve all holdings for a specific user."""
        if self.use_supabase:
            try:
                response = self.supabase.table("holdings").select("*").eq("user_id", user_id).execute()
                return response.data
            except Exception as e:
                logger.error(f"Supabase read error: {e}")
                return []
        else:
            try:
                with open(self.local_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Local file read error: {e}")
                return []

    def add_stock(self, user_id, symbol, quantity, cost_basis):
        """Add a stock to the portfolio for a specific user."""
        symbol = symbol.upper()
        # Support fractional shares by using float()
        try:
            # Supabase shares column is bigint (int8), so we must send int, not float (e.g. 100.0 fails)
            safe_shares = int(float(quantity))
        except ValueError:
            safe_shares = 0
            
        record = {
            "user_id": user_id,
            "symbol": symbol,
            "shares": safe_shares,
            "cost_basis": float(cost_basis),
            "updated_at": datetime.utcnow().isoformat()
        }

        if self.use_supabase:
            try:
                # Insert the record directly. Supabase doesn't support "upsert" easily without a primary key constraint
                # that includes user_id+symbol. For now, we append.
                self.supabase.table("holdings").insert(record).execute()
                return {"status": "success", "msg": "Added to Supabase"}
            except Exception as e:
                logger.error(f"Supabase write error: {e}")
                return {"status": "error", "msg": str(e)}
        else:
            try:
                data = self.get_portfolio(user_id) # Local mode ignores user_id effectively
                # Check if symbol exists, if so, maybe update?
                existing = next((item for item in data if item["symbol"] == symbol), None)
                if existing:
                    existing["shares"] = float(quantity)
                    existing["cost_basis"] = float(cost_basis)
                    existing["updated_at"] = datetime.utcnow().isoformat()
                else:
                    data.append(record)
                
                with open(self.local_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                return {"status": "success", "msg": "Saved locally"}
            except Exception as e:
                logger.error(f"Local file write error: {e}")
                return {"status": "error", "msg": str(e)}

    def remove_stock(self, user_id, symbol):
        """Remove a stock from the portfolio."""
        symbol = symbol.upper()
        if self.use_supabase:
            try:
                self.supabase.table("holdings").delete().eq("user_id", user_id).eq("symbol", symbol).execute()
                return {"status": "success"}
            except Exception as e:
                return {"status": "error", "msg": str(e)}
        else:
            try:
                data = self.get_portfolio(user_id)
                data = [d for d in data if d["symbol"] != symbol]
                with open(self.local_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                return {"status": "success"}
            except Exception as e:
                return {"status": "error", "msg": str(e)}

    def get_company_summary(self, symbol):
        """Get one-sentence company summary, using cache or Gemini AI."""
        if not symbol: return ""
        
        # 1. Try Cache
        cache = {}
        try:
            if os.path.exists(self.summary_file):
                with open(self.summary_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
        except Exception as e:
            logger.error(f"Summary cache read error: {e}")

        if symbol in cache:
            return cache[symbol]

        # 2. Fetch from Gemini
        summary = self._fetch_gemini_summary(symbol)
        
        # 3. Save to Cache
        if summary and not summary.startswith("API Error") and summary != "Network Error" and summary != "AI Generation Error":
            cache[symbol] = summary
            try:
                with open(self.summary_file, 'w', encoding='utf-8') as f:
                    json.dump(cache, f, indent=2, ensure_ascii=False)
            except Exception as e:
                logger.error(f"Summary cache write error: {e}")
        
        return summary

    def _fetch_gemini_summary(self, symbol):
        """Call Gemini API for summary."""
        if not self.gemini_client:
            return "API Key Missing or Client Not Initialized"

        try:
            # For A-Shares, fetch company name for better AI context
            prompt_symbol = symbol
            if symbol.isdigit():
                try:
                    from data_fetcher import DataFetcher
                    fetcher = DataFetcher()
                    info = fetcher.get_stock_info(symbol)
                    if info and info.get('name') and info['name'] != symbol:
                        prompt_symbol = f"{symbol} (公司名: {info['name']})"
                except Exception as e:
                    logger.warning(f"Failed to fetch company name for {symbol}: {e}")

            # Use the configured Gemini client
            response = self.gemini_client.generate_content(
                f"请用一句话简明扼要地总结股票代码为 {prompt_symbol} 的公司的主要业务和行业地位（不要废话，直接说重点）。",
                safety_settings=[
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                ]
            )
            
            if response and response.text:
                return response.text.strip()
            else:
                return "AI Generation Error: No text in response"
                
        except Exception as e:
            logger.error(f"Gemini Fetch Exception: {e}")
            return f"Network Error: {str(e)}"
