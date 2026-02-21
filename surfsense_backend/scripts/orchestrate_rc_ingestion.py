import os
import time
import datetime
import re
import csv
import xml.etree.ElementTree as ET
import zipfile
import httpx
from pathlib import Path
from collections import defaultdict

# --- CONFIGURATION (Environment-aware) ---
DOCS_ROOT = Path(os.getenv("DOCS_ROOT", "/ingest/docs"))
LITHUANIA_RC_DIR = DOCS_ROOT / "lithuania_rc_data"
JAR_FILE = LITHUANIA_RC_DIR / "JuridinisAsmuo.csv"
OUTPUT_DIR = LITHUANIA_RC_DIR / "final_processed_records"
TEMP_DIR = Path("/tmp/es_sync")
STATE_FILE = LITHUANIA_RC_DIR / ".sync_state"

# Ensure directories exist
TEMP_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def get_last_sync_date():
    if STATE_FILE.exists():
        try:
            return STATE_FILE.read_text().strip()
        except: pass
    # Default to 30 days ago if no state
    return (datetime.date.today() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")

def save_sync_date(date_str):
    STATE_FILE.write_text(date_str)

def normalize_name(name):
    if not name: return ""
    name = name.upper()
    name = name.replace('"', '').replace('&QUOT;', '').replace('„', '').replace('“', '')
    name = re.sub(r'UAB|MB|VŠĮ|AB|VŠI|IĮ|BĮ|TŪB|KŪB|UŽDAROJI AKCINĖ BENDROVĖ|VIEŠOJI ĮSTAIGA', '', name)
    name = re.sub(r'[^A-Z0-9ĄČĘĖĮŠŲŪŽ]', '', name)
    return name.strip()

def download_data(from_date, to_date):
    xls_path = TEMP_DIR / "export.xls"
    print(f"[{datetime.datetime.now()}] Downloading projects from {from_date} to {to_date}...")
    
    url = f"https://2014.esinvesticijos.lt/en//priorities-and-finances/paraiskos_ir_projektai/xlsexport?application_receipt_date%5Bfrom%5D={from_date}&application_receipt_date%5Bto%5D={to_date}&elig_result=0&benefit_result=0&ff=1"
    
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "content-type": "application/x-www-form-urlencoded",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    with httpx.Client(timeout=120.0) as client:
        response = client.post(url, headers=headers)
        response.raise_for_status()
        xls_path.write_bytes(response.content)
        
    return xls_path

def parse_xlsx_to_csv(xlsx_path, csv_path):
    print(f"[{datetime.datetime.now()}] Converting XLS to CSV...")
    with zipfile.ZipFile(xlsx_path, 'r') as z:
        with z.open('xl/worksheets/sheet1.xml') as f:
            context = ET.iterparse(f, events=('end',))
            with open(csv_path, 'w', encoding='utf-8', newline='') as csvfile:
                writer = csv.writer(csvfile)
                row_data = {}
                for event, elem in context:
                    if elem.tag.endswith('}c'):
                        r = elem.get('r')
                        col = ''.join(filter(str.isalpha, r))
                        v_elem = elem.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                        t_elem = elem.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}is/{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t')
                        val = t_elem.text if t_elem is not None else (v_elem.text if v_elem is not None else "")
                        row_data[col] = val
                        elem.clear()
                    elif elem.tag.endswith('}row'):
                        if row_data:
                            cols = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M']
                            writer.writerow([row_data.get(c, "") for c in cols])
                            row_data = {}
                        elem.clear()

def sync():
    from_date = get_last_sync_date()
    to_date = datetime.date.today().strftime("%Y-%m-%d")
    
    if from_date == to_date:
        print(f"[{datetime.datetime.now()}] Already synced for today.")
        return False

    try:
        xls_file = download_data(from_date, to_date)
        csv_file = TEMP_DIR / "projects.csv"
        parse_xlsx_to_csv(xls_file, csv_file)
    except Exception as e:
        print(f"[{datetime.datetime.now()}] Download/Parse failed: {e}")
        return False
    
    print(f"[{datetime.datetime.now()}] Loading company registry data...")
    name_to_entities = defaultdict(list)
    if not JAR_FILE.exists():
        print(f"Error: Registry file {JAR_FILE} not found!")
        return False

    with open(JAR_FILE, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name_to_entities[normalize_name(row['ja_pavadinimas'])].append(row)
            
    print(f"[{datetime.datetime.now()}] Matching projects and updating records...")
    updated_count = 0
    with open(csv_file, mode='r', encoding='utf-8') as f:
        next(f, None) # Skip header
        reader = csv.reader(f)
        for row in reader:
            if not row or len(row) < 3: continue
            proj_name, proj_code, exec_name = row[0], row[1], row[2]
            
            norm = normalize_name(exec_name)
            matches = name_to_entities.get(norm, [])
            
            if len(matches) == 1:
                ja = matches[0]
                code = ja['ja_kodas']
                md_path = OUTPUT_DIR / f"{code}.md"
                
                if not md_path.exists():
                    content = f"# {ja['ja_pavadinimas']}\n- **Įmonės kodas**: {code}\n- **JAR registracijos data**: {ja['reg_data']}\n\n## ES Investicijų projektai\n"
                else:
                    content = md_path.read_text()
                
                if proj_code not in content:
                    proj_line = f"| {proj_name} | {proj_code} | {row[7]} EUR | {row[3]} | {row[9]} |\n"
                    if "| Projektas |" not in content:
                        content += "\n| Projektas | Kodas | Suma | Statusas | Data |\n| :--- | :--- | :--- | :--- | :--- |\n"
                    content += proj_line
                    md_path.write_text(content)
                    updated_count += 1

    print(f"[{datetime.datetime.now()}] Sync complete. Updated {updated_count} records.")
    save_sync_date(to_date)
    return True

if __name__ == "__main__":
    sync()
