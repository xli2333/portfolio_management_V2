import os
import sys
import logging
from analyst_agent import AnalystAgent
from report_generator import create_markdown_pdf

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_generate_report(symbol="AAPL"):
    print(f"\n=== Testing Agent Report Generation for {symbol} ===\n")

    # 1. Initialize Agent
    print("[1] Initializing AnalystAgent...")
    try:
        agent = AnalystAgent()
        print("    -> Success.")
    except Exception as e:
        print(f"    -> Failed: {e}")
        return

    # 2. Run Agent (Generate Text)
    print("[2] Running Agent to generate text (this may take a while)...")
    try:
        # Mocking context for test
        mock_context = "This company makes iPhones and Macs. Revenue is growing."
        report_text = agent.generate_deep_research_report(symbol, context_text=mock_context, model_name="gemini-2.5-flash") # Use flash for faster test
        
        print("\n--- Agent Response Preview ---")
        print(report_text[:500] + "...")
        print("------------------------------\n")
        
        if report_text.startswith("Error") or report_text.startswith("Agent Error"):
            print("    -> Agent returned an error message. Stopping.")
            return

    except Exception as e:
        print(f"    -> Agent Execution Failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # 3. Generate PDF
    print("[3] Generating PDF from text...")
    try:
        pdf_bytes = create_markdown_pdf(symbol, report_text)
        print(f"    -> PDF generated. Size: {len(pdf_bytes)} bytes")
        
        # Save to file for inspection
        output_filename = f"test_report_{symbol}.pdf"
        with open(output_filename, "wb") as f:
            f.write(pdf_bytes)
        print(f"    -> Saved to {output_filename}")
        
    except Exception as e:
        print(f"    -> PDF Generation Failed: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n=== Test Completed Successfully ===")

if __name__ == "__main__":
    # You can pass a symbol as argument
    sym = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    test_generate_report(sym)
