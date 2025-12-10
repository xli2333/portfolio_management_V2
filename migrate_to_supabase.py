import json
import os
import sys
from supabase import create_client
from dotenv import load_dotenv

def migrate():
    load_dotenv()
    
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_KEY must be set in .env")
        sys.exit(1)
        
    try:
        supabase = create_client(supabase_url, supabase_key)
        print("Connected to Supabase.")
    except Exception as e:
        print(f"Failed to connect to Supabase: {e}")
        sys.exit(1)
        
    local_file = "portfolio.json"
    if not os.path.exists(local_file):
        print(f"No {local_file} found. Nothing to migrate.")
        return

    try:
        with open(local_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if not data:
            print("portfolio.json is empty.")
            return
            
        print(f"Found {len(data)} records in {local_file}. Migrating...")
        
        # Prepare data for Supabase
        # Ensure keys match Supabase table columns: symbol, shares, cost_basis, updated_at
        records = []
        for item in data:
            try:
                shares_val = float(item.get("shares", 0))
            except ValueError:
                shares_val = 0.0
                
            record = {
                "symbol": item.get("symbol"),
                "shares": shares_val,
                "cost_basis": float(item.get("cost_basis", 0.0)),
                "updated_at": item.get("updated_at")
            }
            records.append(record)
            
        # Supabase upsert
        # We assume 'symbol' is the primary key (unique constraint)
        response = supabase.table("holdings").upsert(records).execute()
        
        print("Migration complete!")
        print(response)
        
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate()
