# QDArchive Seeding – Part 1: Data Acquisition

**Student ID:** 23129103  
**GitHub Repository:** https://github.com/ShorfuddinRobin/QDarchieve  
**Project:** SQ26 – Seeding QDArchive  
**Supervisor:** Prof. Dr. Dirk Riehle, FAU Erlangen-Nürnberg  
**Semester:** Summer 2026  

---

## What This Project Does

This repository implements **Part 1 (Data Acquisition)** of the Seeding QDArchive project. The goal is to discover, download, and catalogue qualitative research data projects from assigned public repositories, storing all metadata in a structured SQLite database.

**Assigned repositories:**
| ID | Name | URL | Software |
|----|------|-----|----------|
| 5  | DANS SSH DataStations | https://ssh.datastations.nl | Dataverse |
| 16 | Open Data Uni Halle | https://opendata.uni-halle.de | DSpace 5/6 |

---

## Repository Structure

```
QDarchieve/
├── 23129103-seeding.db          ← SQLite database (submission artifact)
├── main.py                      ← Pipeline entry point
├── requirements.txt
├── README.md
├── .gitignore
│
├── db/
│   ├── schema.sql               ← All 6 table definitions
│   └── database.py              ← DB helpers (insert, init, seed)
│
├── pipeline/
│   └── downloader.py            ← Generic file downloader
│
├── scrapers/
│   ├── dans_scraper.py          ← Repo #5: DANS via Dataverse API
│   └── uni_halle_scraper.py     ← Repo #16: Uni Halle via DSpace REST + HTML
│
├── export/
│   └── export_csv.py            ← Export DB tables to CSV for inspection
│
├── scripts/
│   └── retry_failed.py          ← Retry transient download failures
│
└── data/                        ← Downloaded files (uploaded separately to FAUbox)
    ├── dans/
    │   └── {project_folder}/
    │       └── file.qdpx ...
    └── open-data-uni-halle/
        └── {project_folder}/
            └── file.pdf ...
```

---

## Database Schema

The SQLite database `23129103-seeding.db` contains six tables:

### REPOSITORIES
Seed table listing the two assigned repositories.
```
id | name | url
```

### PROJECTS
One row per discovered research project.
```
id | query_string | repository_id | repository_url | project_url |
version | title | description | language | doi |
upload_date | download_date |
download_repository_folder | download_project_folder | download_version_folder |
download_method (SCRAPING | API-CALL)
```

### FILES
One row per file belonging to a project.
```
id | project_id | file_name | file_type | status
```
`status` is one of:
- `SUCCEEDED`
- `FAILED_LOGIN_REQUIRED`
- `FAILED_SERVER_UNRESPONSIVE`
- `FAILED_TOO_LARGE`

### KEYWORDS
```
id | project_id | keyword
```

### PERSON_ROLE
```
id | project_id | name | role (AUTHOR | UPLOADER | OWNER | OTHER | UNKNOWN)
```

### LICENSES
```
id | project_id | license
```

---

## How to Run

### Prerequisites
- Python 3.10 or higher
- pip

### Setup

```bash
git clone https://github.com/ShorfuddinRobin/QDarchieve
cd QDarchieve

python3 -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### Run the Pipeline

```bash
# Initialise database only (creates 23129103-seeding.db)
python3 main.py --init-only

# Run DANS scraper only (repo #5)
python3 main.py --repo dans

# Run Uni Halle scraper only (repo #16)
python3 main.py --repo halle

# Run both scrapers
python3 main.py

# Run both and also export CSVs for review
python3 main.py --export-csv
```

### Retry Failed Downloads

```bash
python3 scripts/retry_failed.py
```

---

## Queries Used

The following search queries were used across both repositories. These were chosen to maximise recall of QDA-related projects:

| Query | Rationale |
|-------|-----------|
| `qdpx` | Standard REFI-QDA exchange format |
| `mqda` | MaxQDA project file extension |
| `nvp` | NVivo project file extension |
| `interview study` | Common description in qualitative research |
| `qualitative research` | Broad catch-all |
| `qualitative data` | Alternative broad catch-all |

---

## Download Method per Repository

| Repository | Method | Reason |
|---|---|---|
| DANS SSH DataStations | `API-CALL` | Dataverse exposes a complete Search API (`/api/search`) and file access API (`/api/access/datafile/<id>`). No scraping of HTML was necessary. |
| Open Data Uni Halle | `SCRAPING` | DSpace 5/6 does not expose a structured search API. Discovery required parsing HTML from `/simple-search`. File metadata was then retrieved from the `/rest/handle/...` endpoint. |

---

## Data Folder

The `data/` directory is **not committed to Git** (it is listed in `.gitignore`) because it can be several gigabytes.

It is uploaded separately to FAUbox / Google Drive and the link is submitted via the professor's form.

Structure of the data folder:
```
data/
├── dans/
│   └── doi_10.17026_SS_ABCDEF/
│       ├── interview_data.qdpx
│       └── codebook.pdf
└── open-data-uni-halle/
    └── 1981185920_12345/
        ├── study.mqda
        └── transcript1.docx
```

---

## Technical Challenges

> **Note to assessor:** Per the project requirements, this section documents **data quality and data access challenges** encountered during Part 1. Programming challenges are deliberately excluded.

### 1. Inconsistent Metadata Completeness

Both repositories store metadata in very different ways. DANS uses a nested JSON structure with typed metadata blocks (Dublin Core, custom Dataverse fields). Open Data Uni Halle uses a flat Dublin Core array in its REST API. In both cases, many fields are simply absent for older deposits: descriptions are missing, upload dates are stored inconsistently (sometimes only a year, sometimes a full ISO timestamp), and language codes are not normalised (e.g. "German", "de", "deu" all appear for the same language). Per the professor's instruction, raw values were stored without normalisation; this will be resolved in Part 2.

### 2. Keyword Formatting and Data Quality

Keywords in both repositories suffer from severe inconsistency. A single project may list `"interlanguage pragmatics, EFL learners, scoping review"` as one single keyword string rather than three separate entries. Others use semicolons or slashes as delimiters. Some keywords are comma-separated within a single field. Because the instruction is to not change data at this stage, all keyword values were stored exactly as found. Parsing and normalisation is a Part 2 concern.

### 3. Restricted and Login-Gated Files

A significant fraction of datasets — particularly on DANS SSH DataStations — mark individual files as restricted even when the dataset metadata is publicly visible. The Dataverse API signals this via a `"restricted": true` flag per file. These files were recorded in the FILES table with status `FAILED_LOGIN_REQUIRED` rather than skipped silently. This preserves the knowledge that the data exists but is inaccessible without credentials.

### 4. Ambiguity Between People's Roles

Both repositories use a single contributor field without distinguishing between the person who uploaded the dataset, the original author(s) of the research, and the data owner (often an institution). DANS stores a "depositor" field separately from "author", but the distinction between depositor and uploader is not always clear. Uni Halle uses `dc.contributor.author` and `dc.creator` interchangeably. Where the role could be inferred, `AUTHOR` or `UPLOADER` were assigned; where it could not, `UNKNOWN` was used.

### 5. Multiple Licenses on a Single Project

Several DANS datasets specify more than one license — for instance, a CC BY 4.0 license on the dataset itself and a separate custom institutional license on individual files. The current schema stores one license per LICENSES row, so multiple licenses result in multiple rows for the same project. This is correct behaviour for Part 1 but means Part 2 must handle the case where projects have conflicting or redundant license entries.

### 6. Version History and Duplicate Projects

Dataverse (DANS) maintains version history for datasets. The same intellectual project may appear as v1, v2, v3 with different file sets. The current scraper targets the `:latest` version only. If a project was updated between two pipeline runs, the older version's files may differ from what is on disk. This is a known limitation to be addressed in Part 2.

### 7. Lack of QDA-Specific Filtering

Neither repository has a dedicated filter for "QDA files". Searching for `qdpx` or `mqda` returns results only when the uploader happened to mention the file format in their metadata. Many qualitative datasets contain `.qdpx` files without mentioning the format by name in any metadata field — they can only be found by inspecting the actual file list. This means recall is inherently limited at the metadata-search stage; a full file-listing crawl would be needed for completeness.

---

## Submission Checklist

- [x] `23129103-seeding.db` in root of GitHub repository
- [x] Git tag `part-1-release` on final commit
- [ ] `data/` folder uploaded to FAUbox or Google Drive
- [ ] Professor's submission form filled in with GitHub link and data folder link

---

## License

This code is written for academic purposes as part of the SQ26 project at FAU Erlangen-Nürnberg. The downloaded research data retains its original licenses as recorded in the database.
