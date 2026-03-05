import requests
import sqlite3
import os
import time
from pathlib import Path
from datetime import datetime

# -----------------------------
# CONFIG
# -----------------------------

QUERIES = [
    "qualitative research",
    "interview transcripts",
    "focus group",
    "ethnography",
    "qualitative dataset"
]

RESULTS_PER_QUERY = 50

DOWNLOAD_ROOT = Path("downloads")
ZENODO_ROOT = DOWNLOAD_ROOT / "zenodo"
DATAVERSE_ROOT = DOWNLOAD_ROOT / "dataverse"

DB_PATH = Path("metadata.db")

QDA_EXTENSIONS = (
    ".qdpx",
    ".nvpx",
    ".atlproj",
    ".mx"
)

# -----------------------------
# DATABASE
# -----------------------------

def init_db():

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS datasets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dataset_url TEXT,
        repository TEXT,
        title TEXT,
        author TEXT,
        license TEXT,
        doi TEXT,
        download_timestamp TEXT,
        local_directory TEXT,
        qda_filename TEXT
    )
    """)

    conn.commit()
    conn.close()


def insert_dataset(row):

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO datasets(
        dataset_url,
        repository,
        title,
        author,
        license,
        doi,
        download_timestamp,
        local_directory,
        qda_filename
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, row)

    conn.commit()
    conn.close()


# -----------------------------
# FILE DOWNLOAD
# -----------------------------

def download_file(url, path):

    try:

        r = requests.get(url, stream=True)

        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

    except Exception as e:
        print("Download failed:", url)
        print(e)


# -----------------------------
# ZENODO SEARCH
# -----------------------------

def search_zenodo(query):

    print("Searching Zenodo:", query)

    url = "https://zenodo.org/api/records"

    params = {
        "q": query,
        "size": RESULTS_PER_QUERY
    }

    r = requests.get(url, params=params)

    data = r.json()

    records = data.get("hits", {}).get("hits", [])

    return records


# -----------------------------
# PROCESS ZENODO DATASET
# -----------------------------

def process_zenodo_dataset(rec):

    metadata = rec.get("metadata", {})

    dataset_id = rec.get("id")

    folder = ZENODO_ROOT / str(dataset_id)

    folder.mkdir(parents=True, exist_ok=True)

    files = rec.get("files", [])

    if not files:
        return

    qda_file = None

    for f in files:

        filename = f.get("key")

        file_url = f.get("links", {}).get("self")

        if not filename or not file_url:
            continue

        path = folder / filename

        print("Downloading:", filename)

        download_file(file_url, path)

        if filename.lower().endswith(QDA_EXTENSIONS):
            qda_file = filename

    row = (

        rec.get("links", {}).get("html") or rec.get("links", {}).get("self"),
        "Zenodo",
        metadata.get("title"),
        metadata.get("creators", [{}])[0].get("name") if metadata.get("creators") else None,
        metadata.get("license", {}).get("id") if metadata.get("license") else None,
        metadata.get("doi"),
        datetime.utcnow().isoformat(),
        str(folder),
        qda_file

    )

    insert_dataset(row)


# -----------------------------
# DATAVERSE SEARCH
# -----------------------------

def search_dataverse(query):

    print("Searching Dataverse:", query)

    url = "https://dataverse.harvard.edu/api/search"

    params = {
        "q": query,
        "type": "dataset",
        "per_page": RESULTS_PER_QUERY
    }

    r = requests.get(url, params=params)

    data = r.json()

    return data.get("data", {}).get("items", [])


# -----------------------------
# PIPELINE
# -----------------------------

def run_pipeline():

    init_db()

    os.makedirs(ZENODO_ROOT, exist_ok=True)
    os.makedirs(DATAVERSE_ROOT, exist_ok=True)

    for query in QUERIES:

        # Zenodo
        records = search_zenodo(query)

        for rec in records:

            print("\nProcessing Zenodo dataset")

            process_zenodo_dataset(rec)

            time.sleep(1)

        # Dataverse search only (no download for now)
        dv_records = search_dataverse(query)

        for item in dv_records:

            row = (

                item.get("url"),
                "Dataverse",
                item.get("name"),
                None,
                None,
                None,
                datetime.utcnow().isoformat(),
                None,
                None
            )

            insert_dataset(row)


# -----------------------------
# RUN
# -----------------------------

if __name__ == "__main__":

    run_pipeline()

    print("\nPipeline finished successfully")