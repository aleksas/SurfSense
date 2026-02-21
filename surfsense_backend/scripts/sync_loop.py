import time
import subprocess
import os
from orchestrate_rc_ingestion import sync

# Config
SYNC_INTERVAL_HOURS = int(os.getenv("SYNC_INTERVAL_HOURS", "24"))
SEARCH_SPACE_ID = os.getenv("SEARCH_SPACE_ID", "5")
USER_EMAIL = os.getenv("USER_EMAIL", "ant.kampo@gmail.com")

def trigger_ingestion():
    print(f"Triggering SurfSense re-index for Search Space {SEARCH_SPACE_ID}...")
    cmd = [
        "python", "/app/scripts/ingest_docs_tree.py",
        "--email", USER_EMAIL,
        "--search-space-id", SEARCH_SPACE_ID,
        "--folder", "/ingest/docs/lithuania_rc_data/final_processed_records",
        "--glob", "*.md",
        "--reindex-existing"
    ]
    subprocess.run(cmd)

def main_loop():
    print(f"Starting RC Sync Loop (Interval: {SYNC_INTERVAL_HOURS}h)...")
    while True:
        changed = sync()
        if changed:
            trigger_ingestion()
        
        print(f"Sleeping for {SYNC_INTERVAL_HOURS} hours...")
        time.sleep(SYNC_INTERVAL_HOURS * 3600)

if __name__ == "__main__":
    main_loop()
