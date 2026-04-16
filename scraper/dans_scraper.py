"""
scrapers/dans_scraper.py
Scraper for DANS SSH Data Stations (repo #5).
Uses the Dataverse Search API and Native API.
  Base URL : https://ssh.datastations.nl
  API docs : https://guides.dataverse.org/en/latest/api/search.html
"""
import time
import datetime
import requests
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from db import database as db
from pipeline.downloader import download_file, make_project_dir, safe_filename, SESSION

REPO_ID   = 5
REPO_NAME = "dans"
REPO_URL  = "https://ssh.datastations.nl"
API_BASE  = "https://ssh.datastations.nl"

# Queries to run (as instructed by professor)
QUERIES = [
    "qdpx",
    "mqda",
    "interview study",
    "qualitative research",
    "nvp",
]

PAGE_SIZE = 10   # items per API call


def normalize_license(raw: str) -> str:
    """Map verbose license strings to short canonical forms where possible."""
    if not raw:
        return "UNKNOWN"
    r = raw.strip()
    mapping = {
        "Creative Commons Zero v1.0 Universal": "CC0",
        "CC0 1.0": "CC0",
        "Creative Commons Attribution 4.0": "CC BY 4.0",
        "CC BY 4.0": "CC BY 4.0",
        "Creative Commons Attribution Share Alike 4.0": "CC BY-SA 4.0",
        "Creative Commons Attribution Non Commercial 4.0": "CC BY-NC 4.0",
        "Creative Commons Attribution No Derivatives 4.0": "CC BY-ND 4.0",
        "Creative Commons Attribution Non Commercial No Derivatives 4.0": "CC BY-NC-ND 4.0",
        "Open Data Commons Open Database License v1.0": "ODbL-1.0",
    }
    return mapping.get(r, r)


def search_datasets(query: str):
    """
    Use the Dataverse Search API to find datasets.
    Yields individual dataset persistent_ids.
    """
    start = 0
    while True:
        url = (
            f"{API_BASE}/api/search"
            f"?q={requests.utils.quote(query)}"
            f"&type=dataset"
            f"&start={start}"
            f"&per_page={PAGE_SIZE}"
            f"&sort=date"
            f"&order=desc"
        )
        try:
            resp = SESSION.get(url, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            print(f"  [dans] Search API error for query='{query}' start={start}: {exc}")
            break

        items = data.get("data", {}).get("items", [])
        total = data.get("data", {}).get("total_count", 0)
        print(f"  [dans] query='{query}' start={start} total={total} got={len(items)}")

        if not items:
            break

        for item in items:
            yield item, query

        start += PAGE_SIZE
        if start >= total:
            break
        time.sleep(0.5)


def get_dataset_metadata(persistent_id: str) -> dict:
    """Fetch full metadata for a dataset via the Native API."""
    url = f"{API_BASE}/api/datasets/:persistentId/?persistentId={persistent_id}"
    try:
        resp = SESSION.get(url, timeout=30)
        resp.raise_for_status()
        return resp.json().get("data", {})
    except Exception as exc:
        print(f"  [dans] metadata error for {persistent_id}: {exc}")
        return {}


def get_dataset_files(persistent_id: str) -> list:
    """Return the list of files for a dataset."""
    url = (
        f"{API_BASE}/api/datasets/:persistentId/versions/:latest/files"
        f"?persistentId={persistent_id}"
    )
    try:
        resp = SESSION.get(url, timeout=30)
        resp.raise_for_status()
        return resp.json().get("data", [])
    except Exception as exc:
        print(f"  [dans] files error for {persistent_id}: {exc}")
        return []


def extract_metadata_fields(meta: dict) -> dict:
    """Parse the nested Dataverse metadata structure into a flat dict."""
    fields_out = {}
    for block in meta.get("metadataBlocks", {}).values():
        for field in block.get("fields", []):
            typeName = field.get("typeName", "")
            multiple = field.get("multiple", False)
            value = field.get("value")

            if typeName == "title":
                fields_out["title"] = value or ""

            elif typeName == "dsDescription":
                if multiple and isinstance(value, list):
                    texts = []
                    for item in value:
                        if isinstance(item, dict):
                            texts.append(item.get("dsDescriptionValue", {}).get("value", ""))
                    fields_out["description"] = " ".join(texts)
                else:
                    fields_out["description"] = str(value or "")

            elif typeName == "author":
                authors = []
                if multiple and isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            name = item.get("authorName", {}).get("value", "")
                            if name:
                                authors.append(name)
                fields_out["authors"] = authors

            elif typeName == "keyword":
                keywords = []
                if multiple and isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            kw = item.get("keywordValue", {}).get("value", "")
                            if kw:
                                keywords.append(kw)
                fields_out["keywords"] = keywords

            elif typeName == "language":
                if multiple and isinstance(value, list):
                    fields_out["language"] = value[0] if value else None
                else:
                    fields_out["language"] = value

            elif typeName == "depositor":
                fields_out["depositor"] = value or ""

            elif typeName == "dateOfDeposit":
                fields_out["upload_date"] = value or ""

    return fields_out


def run():
    print(f"\n{'='*60}")
    print(f"[dans] Starting scrape of DANS SSH DataStations")
    print(f"{'='*60}")

    seen_pids = set()
    projects_inserted = 0

    for query in QUERIES:
        print(f"\n[dans] ---- Query: '{query}' ----")
        for item, q_string in search_datasets(query):
            pid = item.get("global_id") or item.get("identifier_of_dataverse", "")
            if not pid or pid in seen_pids:
                continue
            seen_pids.add(pid)

            project_url = item.get("url") or f"{API_BASE}/dataset.xhtml?persistentId={pid}"

            # Skip if already in DB
            if db.project_url_exists(project_url):
                print(f"  [dans] skip (already in DB): {pid}")
                continue

            print(f"  [dans] processing: {pid}")

            # Full metadata
            meta = get_dataset_metadata(pid)
            if not meta:
                continue

            fields = extract_metadata_fields(meta)
            title = fields.get("title") or item.get("name", "Untitled")
            description = fields.get("description") or item.get("description", "")
            upload_date = fields.get("upload_date") or item.get("published_at", "")
            doi = pid if pid.startswith("doi:") else item.get("identifier_of_dataverse", "")
            doi_url = f"https://doi.org/{doi.replace('doi:', '')}" if doi.startswith("doi:") else ""
            language = fields.get("language", "")

            # Project folder = last segment of pid (e.g. "FK2/ABCDEF")
            project_folder = pid.replace("/", "_").replace(":", "_")

            # Local dir
            dest_dir = make_project_dir(REPO_NAME, project_folder)

            now = datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"

            project_data = {
                "query_string":                q_string,
                "repository_id":               REPO_ID,
                "repository_url":              REPO_URL,
                "project_url":                 project_url,
                "version":                     str(meta.get("latestVersion", {}).get("versionNumber", "") or ""),
                "title":                       title,
                "description":                 description[:4000],
                "language":                    language,
                "doi":                         doi_url,
                "upload_date":                 upload_date,
                "download_date":               now,
                "download_repository_folder":  REPO_NAME,
                "download_project_folder":     project_folder,
                "download_version_folder":     None,
                "download_method":             "API-CALL",
            }

            project_id = db.insert_project(project_data)
            projects_inserted += 1

            # Keywords
            for kw in fields.get("keywords", []):
                db.insert_keyword(project_id, kw)

            # People
            for author in fields.get("authors", []):
                db.insert_person_role(project_id, author, "AUTHOR")
            depositor = fields.get("depositor", "")
            if depositor:
                db.insert_person_role(project_id, depositor, "UPLOADER")

            # License
            license_raw = meta.get("latestVersion", {}).get("license", {})
            if isinstance(license_raw, dict):
                license_str = license_raw.get("name", "") or license_raw.get("uri", "")
            else:
                license_str = str(license_raw) if license_raw else ""
            if license_str:
                db.insert_license(project_id, normalize_license(license_str))

            # Files
            files = get_dataset_files(pid)
            print(f"    [dans] {len(files)} files found")
            for f in files:
                df = f.get("dataFile", {})
                file_id   = df.get("id")
                file_name = df.get("filename", f"file_{file_id}")
                file_ext  = Path(file_name).suffix.lstrip(".").lower() or "bin"

                # Check restricted
                restricted = f.get("restricted", False)
                if restricted:
                    status = "FAILED_LOGIN_REQUIRED"
                    db.insert_file(project_id, file_name, file_ext, status)
                    print(f"      skip restricted: {file_name}")
                    continue

                dl_url = f"{API_BASE}/api/access/datafile/{file_id}"
                status = download_file(dl_url, dest_dir, safe_filename(file_name) or file_name)
                db.insert_file(project_id, file_name, file_ext, status)
                print(f"      [{status}] {file_name}")
                time.sleep(0.3)

            time.sleep(0.5)

    print(f"\n[dans] Done. {projects_inserted} new projects inserted.")


if __name__ == "__main__":
    db.init_db()
    db.seed_repositories()
    run()
