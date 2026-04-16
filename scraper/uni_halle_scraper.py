import sys, re, time, datetime, requests
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlencode
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent))

from db import database as db
from pipeline.downloader import make_project_dir

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
REPO_ID   = 16
REPO_NAME = "open-data-uni-halle"
REPO_URL  = "https://opendata.uni-halle.de"
OAI_URL   = "https://opendata.uni-halle.de/oai/request"

NS_OAI = "http://www.openarchives.org/OAI/2.0/"

LIMIT = 500   # 🔥 increased safely

# limits to control size
MAX_FILES_PER_PROJECT = 2
MAX_FILE_MB = 20

# ─────────────────────────────────────────────
# SESSION
# ─────────────────────────────────────────────
SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0"
})

# ─────────────────────────────────────────────
# SAFE REQUEST
# ─────────────────────────────────────────────
def safe_get(url, tries=3):
    for _ in range(tries):
        try:
            print(f"[GET] {url}")
            r = SESSION.get(url, timeout=60)
            if r.status_code == 200:
                return r
        except:
            time.sleep(2)
    return None

# ─────────────────────────────────────────────
# EXTRACT DC METADATA
# ─────────────────────────────────────────────
def dc_values(record_el, field):
    values = []
    md = record_el.find(f".//{{{NS_OAI}}}metadata")
    if md is None:
        return values

    for el in md.iter():
        if el.tag.endswith(field) and el.text:
            values.append(el.text.strip())

    return values

# ─────────────────────────────────────────────
# EXTRACT FILE LINKS
# ─────────────────────────────────────────────
def extract_files(project_url):
    r = safe_get(project_url)
    if not r:
        return []

    soup = BeautifulSoup(r.text, "html.parser")

    files = []
    for a in soup.find_all("a", href=True):
        href = a["href"]

        if "/bitstream/" in href:
            if not href.startswith("http"):
                href = REPO_URL + href
            files.append(href)

    return list(set(files))

# ─────────────────────────────────────────────
# SAFE DOWNLOAD (SIZE LIMITED)
# ─────────────────────────────────────────────
def download_file(url, folder):
    try:
        r = SESSION.get(url, stream=True, timeout=120)

        size_mb = int(r.headers.get("content-length", 0)) / (1024 * 1024)

        if size_mb > MAX_FILE_MB:
            print(f"[skip large] {round(size_mb,2)} MB")
            return None

        filename = url.split("/")[-1]
        path = Path(folder) / filename

        with open(path, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)

        return filename

    except:
        return None

# ─────────────────────────────────────────────
# SAFE DB INSERT
# ─────────────────────────────────────────────
def safe_insert(data, tries=5):
    for _ in range(tries):
        try:
            return db.insert_project(data)
        except:
            time.sleep(1)
    return None

# ─────────────────────────────────────────────
# MAIN HARVEST
# ─────────────────────────────────────────────
def harvest():
    print("\n[halle] QUALITATIVE OAI HARVEST STARTED\n")

    token = None
    inserted = 0

    while True:

        # request build
        if token:
            params = {"verb": "ListRecords", "resumptionToken": token}
        else:
            params = {"verb": "ListRecords", "metadataPrefix": "oai_dc"}

        url = OAI_URL + "?" + urlencode(params)

        r = safe_get(url)
        if not r:
            break

        root = ET.fromstring(r.content)
        records = root.findall(f".//{{{NS_OAI}}}record")

        print(f"[batch] {len(records)}")

        for rec in records:

            if inserted >= LIMIT:
                print("\n[halle] STOPPED AFTER LIMIT\n")
                return

            # skip deleted
            header = rec.find(f"{{{NS_OAI}}}header")
            if header is not None and header.get("status") == "deleted":
                continue

            # identifier
            id_el = rec.find(f".//{{{NS_OAI}}}identifier")
            if id_el is None:
                continue

            oai_id = id_el.text.strip()

            m = re.search(r":(\d+/\d+)$", oai_id)
            if not m:
                continue

            handle = m.group(1)
            project_url = f"{REPO_URL}/handle/{handle}"

            if db.project_url_exists(project_url):
                continue

            # metadata
            title_list = dc_values(rec, "title")
            desc_list  = dc_values(rec, "description")

            title = title_list[0] if title_list else "Untitled"
            desc  = " ".join(desc_list)

            # folder
            project_folder = handle.replace("/", "_")
            folder_path = make_project_dir(REPO_NAME, project_folder)

            # insert project
            project_id = safe_insert({
                "query_string": "qualitative",
                "repository_id": REPO_ID,
                "repository_url": REPO_URL,
                "project_url": project_url,
                "version": "1",
                "title": title[:500],
                "description": desc,
                "language": "",
                "doi": "",
                "upload_date": "",
                "download_date": datetime.datetime.utcnow().isoformat(),
                "download_repository_folder": REPO_NAME,
                "download_project_folder": project_folder,
                "download_version_folder": "v1",
                "download_method": "API-CALL",
            })

            if not project_id:
                continue

            print(f"[{inserted+1}] {title[:60]}")

            # files
            files = extract_files(project_url)

            # 🔥 LIMIT FILE COUNT
            files = files[:MAX_FILES_PER_PROJECT]

            for f in files:
                fname = download_file(f, folder_path)

                if fname:
                    try:
                        db.insert_file(project_id, fname, "UNKNOWN", "DOWNLOADED")
                    except:
                        pass

            inserted += 1

        # pagination
        tok_el = root.find(f".//{{{NS_OAI}}}resumptionToken")
        if tok_el is None or not tok_el.text:
            break

        token = tok_el.text.strip()
        time.sleep(1)

# ─────────────────────────────────────────────
# ENTRY
# ─────────────────────────────────────────────
def run():
    print("\n" + "="*60)
    print("[halle] FINAL ASSIGNMENT SCRAPER")
    print("="*60)

    harvest()


if __name__ == "__main__":
    db.init_db()
    db.seed_repositories()
    run()
