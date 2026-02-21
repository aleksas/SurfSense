import os
import json
import re
from pathlib import Path
from elasticsearch import Elasticsearch, helpers

# --- CONFIGURATION ---
LITHUANIA_RC_DIR = Path("/ingest/docs/lithuania_rc_data")
RECORDS_DIR = LITHUANIA_RC_DIR / "final_processed_records"
ES_URL = "http://elasticsearch:9200"
INDEX_NAME = "lithuania_rc_companies"

def extract_json_from_md(md_path):
    content = md_path.read_text(encoding='utf-8')
    
    # Simple regex-based extraction for our known format
    name_match = re.search(r'^# (.*)', content)
    code_match = re.search(r'- \*\*Įmonės kodas\*\*: (\d+)', content)
    status_match = re.search(r'- \*\*Statusas\*\*: (.*)', content)
    reg_date_match = re.search(r'- \*\*JAR registracijos data\*\*: (.*)', content)
    
    # Extract projects from table
    projects = []
    # Match markdown table rows: | Title | Code | Amount | Status | Date |
    rows = re.findall(r'^\| (.*) \| (.*) \| (.*) \| (.*) \| (.*) \|$', content, re.MULTILINE)
    for row in rows:
        if row[0].strip() == "Projektas": continue # Skip header
        if row[0].strip().startswith(":---"): continue # Skip separator
        
        projects.append({
            "title": row[0].strip(),
            "project_code": row[1].strip(),
            "amount": row[2].strip(),
            "status": row[3].strip(),
            "date": row[4].strip()
        })

    return {
        "company_name": name_match.group(1).strip() if name_match else "Unknown",
        "company_code": code_match.group(1).strip() if code_match else md_path.stem,
        "status": status_match.group(1).strip() if status_match else "Unknown",
        "registration_date": reg_date_match.group(1).strip() if reg_date_match else "Unknown",
        "projects": projects,
        "raw_text": content # Keep raw text for full-text search fallback
    }

def index_all():
    es = Elasticsearch(ES_URL, request_timeout=60)
    
    try:
        # Check if index exists by trying to get its mapping
        es.indices.get(index=INDEX_NAME)
        print(f"Index {INDEX_NAME} exists.")
    except Exception:
        print(f"Creating index {INDEX_NAME}...")
        # Create with explicit mapping for better searching
        mapping = {
            "mappings": {
                "properties": {
                    "company_name": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                    "company_code": {"type": "keyword"},
                    "status": {"type": "keyword"},
                    "registration_date": {"type": "date", "format": "yyyy-MM-dd"},
                    "projects": {
                        "type": "nested",
                        "properties": {
                            "title": {"type": "text"},
                            "project_code": {"type": "keyword"},
                            "amount": {"type": "text"}, # Kept as text because it has ' EUR'
                            "status": {"type": "keyword"},
                            "date": {"type": "keyword"}
                        }
                    },
                    "raw_text": {"type": "text"}
                }
            }
        }
        es.indices.create(index=INDEX_NAME, body=mapping)

    print(f"Reading records from {RECORDS_DIR}...")
    files = list(RECORDS_DIR.glob("*.md"))
    print(f"Found {len(files)} records.")

    def generate_actions():
        for i, md_file in enumerate(files):
            try:
                doc = extract_json_from_md(md_file)
                yield {
                    "_index": INDEX_NAME,
                    "_id": doc["company_code"],
                    "_source": doc
                }
                if (i + 1) % 1000 == 0:
                    print(f"Prepared {i+1} records...")
            except Exception as e:
                pass # Silently skip errors

    print("Starting bulk indexing to Elasticsearch...")
    success, failed = helpers.bulk(es, generate_actions())
    print(f"Indexing complete. Success: {success}, Failed: {failed}")

if __name__ == "__main__":
    index_all()
