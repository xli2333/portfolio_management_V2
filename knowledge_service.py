import os
import json
import logging
import uuid
import shutil
from datetime import datetime
from pypdf import PdfReader
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KnowledgeService:
    def __init__(self):
        self.supabase_url = os.environ.get("SUPABASE_URL")
        self.supabase_key = os.environ.get("SUPABASE_KEY")
        self.use_supabase = bool(self.supabase_url and self.supabase_key)
        
        self.base_path = "knowledge_base"
        self.local_meta_file = os.path.join(self.base_path, "documents.json")
        
        # Ensure directories
        os.makedirs(self.base_path, exist_ok=True)
        if not self.use_supabase:
            self._init_local_storage()

        if self.use_supabase:
            try:
                self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
                logger.info("KnowledgeService: Connected to Supabase")
            except Exception as e:
                logger.error(f"KnowledgeService: Supabase init failed: {e}")
                self.use_supabase = False
                self._init_local_storage()

    def _init_local_storage(self):
        """Initialize local metadata JSON."""
        if not os.path.exists(self.local_meta_file):
            with open(self.local_meta_file, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract all text from a PDF file."""
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text
        except Exception as e:
            logger.error(f"PDF extraction failed for {file_path}: {e}")
            return ""

    def save_document(self, symbol: str, file_obj, filename: str, doc_type: str = "user_upload") -> dict:
        """
        Save uploaded file or generated report.
        1. Save file to disk.
        2. Extract text (for content checking or preview).
        3. Save metadata to DB.
        """
        symbol = symbol.upper()
        doc_id = str(uuid.uuid4())
        
        # Create symbol directory
        symbol_dir = os.path.join(self.base_path, symbol)
        os.makedirs(symbol_dir, exist_ok=True)
        
        # Determine paths
        # Use safe filename
        safe_filename = "".join([c for c in filename if c.isalpha() or c.isdigit() or c in (' ', '.', '_', '-')]).strip()
        file_path = os.path.join(symbol_dir, f"{doc_id}_{safe_filename}")
        
        # Save file content
        try:
            file_obj.save(file_path)
        except AttributeError:
            # If file_obj is bytes or string (e.g. from report generator)
            with open(file_path, 'wb') as f:
                f.write(file_obj if isinstance(file_obj, bytes) else file_obj.encode('utf-8'))

        # Get file size
        file_size = os.path.getsize(file_path)

        # Metadata record
        record = {
            "id": doc_id,
            "symbol": symbol,
            "filename": safe_filename,
            "file_path": file_path,
            "type": doc_type,
            "file_size": file_size,
            "created_at": datetime.utcnow().isoformat()
        }

        # Save Metadata
        if self.use_supabase:
            try:
                self.supabase.table("documents").insert(record).execute()
            except Exception as e:
                logger.error(f"Supabase document insert failed: {e}")
                # Fallback to local? For now just log error.
                return {"error": str(e)}
        else:
            try:
                with open(self.local_meta_file, 'r', encoding='utf-8') as f:
                    docs = json.load(f)
                docs.append(record)
                with open(self.local_meta_file, 'w', encoding='utf-8') as f:
                    json.dump(docs, f, indent=2)
            except Exception as e:
                logger.error(f"Local document save failed: {e}")
                return {"error": str(e)}

        return record

    def list_documents(self, symbol: str) -> list:
        """List documents for a specific symbol."""
        symbol = symbol.upper()
        if self.use_supabase:
            try:
                res = self.supabase.table("documents").select("*").eq("symbol", symbol).order("created_at", desc=True).execute()
                return res.data
            except Exception as e:
                logger.error(f"Supabase list failed: {e}")
                return []
        else:
            try:
                with open(self.local_meta_file, 'r', encoding='utf-8') as f:
                    docs = json.load(f)
                return [d for d in docs if d["symbol"] == symbol]
            except Exception as e:
                return []

    def get_document_content(self, doc_id: str) -> str:
        """Retrieve full text content of a document by ID."""
        # 1. Find document metadata to get path
        doc = None
        if self.use_supabase:
            try:
                res = self.supabase.table("documents").select("*").eq("id", doc_id).single().execute()
                doc = res.data
            except Exception:
                pass
        
        if not doc:
            # Try local
            try:
                with open(self.local_meta_file, 'r', encoding='utf-8') as f:
                    docs = json.load(f)
                doc = next((d for d in docs if d["id"] == doc_id), None)
            except Exception:
                pass
        
        if not doc:
            return ""

        file_path = doc["file_path"]
        if not os.path.exists(file_path):
            return ""

        # Check extension
        if file_path.lower().endswith(".pdf"):
            return self.extract_text_from_pdf(file_path)
        else:
            # Text/Markdown files
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception:
                return ""

    def delete_document(self, doc_id: str) -> bool:
        """Delete document metadata and file."""
        # 1. Get info to find path
        doc = None
        if self.use_supabase:
            res = self.supabase.table("documents").select("*").eq("id", doc_id).execute()
            if res.data: doc = res.data[0]
        else:
            with open(self.local_meta_file, 'r', encoding='utf-8') as f:
                docs = json.load(f)
            doc = next((d for d in docs if d["id"] == doc_id), None)

        if not doc: return False

        # 2. Delete file
        if os.path.exists(doc["file_path"]):
            try:
                os.remove(doc["file_path"])
            except Exception as e:
                logger.error(f"Failed to delete file: {e}")

        # 3. Delete Metadata
        if self.use_supabase:
            self.supabase.table("documents").delete().eq("id", doc_id).execute()
        else:
            docs = [d for d in docs if d["id"] != doc_id]
            with open(self.local_meta_file, 'w', encoding='utf-8') as f:
                json.dump(docs, f, indent=2)
        
        return True

    def get_documents_content(self, file_ids: list) -> str:
        """Combine content of multiple documents."""
        if not file_ids:
            return ""
            
        combined_text = ""
        for doc_id in file_ids:
            # Get metadata first to get filename for separator
            filename = "Unknown File"
            if self.use_supabase:
                try:
                    res = self.supabase.table("documents").select("filename").eq("id", doc_id).single().execute()
                    if res.data: filename = res.data['filename']
                except: pass
            else:
                try:
                    with open(self.local_meta_file, 'r', encoding='utf-8') as f:
                        docs = json.load(f)
                    d = next((x for x in docs if x['id'] == doc_id), None)
                    if d: filename = d['filename']
                except: pass

            content = self.get_document_content(doc_id)
            if content:
                combined_text += f"\n\n--- Document: {filename} ---\n{content}\n"
        
        return combined_text
