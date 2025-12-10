import os
import logging
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class AnalystAgent:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
        else:
            logger.error("GEMINI_API_KEY not found for AnalystAgent")

    def generate_deep_research_report(self, symbol: str, context_text: str = "", model_name: str = "gemini-2.5-pro") -> str:
        """
        Conducts deep research using internal context + Google Search, and writes a report.
        """
        if not self.api_key:
            return "Error: API Key missing."

        # 1. Initialize Model with Search Tool
        # Note: 'gemini-2.5-pro' supports Google Search Grounding natively via 'tools'
        tools = [
            # Enable Google Search retrieval
            {"google_search": {}} 
        ]
        
        # Use a high-intelligence model for reasoning
        model = genai.GenerativeModel(model_name, tools=tools)

        # 2. Construct Prompt
        # Handle Symbol Context (A-Share vs US)
        market_context = "China A-Share" if symbol.isdigit() else "US Stock"
        
        prompt = f"""
You are a Top Wall Street Investment Analyst (e.g., Goldman Sachs, Morgan Stanley level).
Your task is to write a comprehensive, professional investment research report for the {market_context} stock: {symbol}.

### Inputs
1. **Internal Knowledge Base**: I have attached some internal documents below. You MUST read and incorporate data/insights from them.
2. **External Search**: You MUST use your Google Search tool to find the *latest* news, financial data (current price, PE ratio, recent earnings), and industry trends as of today ({os.environ.get('CURRENT_DATE', 'Now')}).

### Report Structure (Markdown)
Please structure the report exactly as follows:

# {symbol} Investment Research Report
**Date:** [Today's Date]
**Analyst:** AI Advisor (Gemini 2.5 Pro)

## 1. Executive Summary (核心观点)
- Bullish/Bearish/Neutral rating.
- Key thesis in 3-5 bullet points.

## 2. Company & Business Overview (基本面分析)
- What they do.
- Recent financial performance (Revenue, Net Profit trends).
- *Merge insights from Internal Docs here if available.*

## 3. Industry Analysis (行业格局)
- Competitors and market share.
- Industry growth drivers (e.g., AI, EVs, etc.).
- *Use Google Search to get the latest industry news.*

## 4. Valuation & Risks (估值与风险)
- Current valuation metrics (PE, PS vs peers).
- Key risks (Policy, Tech, Market).

## 5. Conclusion (结论)
- Final verdict.

---
### Internal Knowledge Base Context:
{context_text[:100000]} 
(Note: Context truncated if too long, prioritize the most relevant parts)
"""
        # Note: Gemini 1.5/2.5 Pro has huge context (1M+ tokens), so simple truncation is just a safety measure for extreme edge cases, 
        # but usually passing full text is fine. The simplified slicing above is just a placeholder.

        try:
            logger.info(f"Agent starting research for {symbol}...")
            
            response = model.generate_content(
                prompt,
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            
            if response.text:
                return response.text
            else:
                return "Error: Agent produced no text (Blocked or Empty)."

        except Exception as e:
            logger.error(f"Agent Research Failed: {e}")
            return f"Agent Error: {str(e)}"
