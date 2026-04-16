# 📊 QDArchive Seeding — Part 1: Data Acquisition

| Field      | Value                                             |
| ---------- | ------------------------------------------------- |
| Student ID | 23129103                                          |
| Course     | Seeding QDArchive – Applied Software Engineering  |
| Professor  | Dirk Riehle                                       |
| University | Friedrich-Alexander-Universität Erlangen-Nürnberg |
| Semester   | Winter 2025/26 + Summer 2026                      |
| Deadline   | April 17, 2026                                    |

---

# 🧭 Overview

This repository implements the **Part 1 (Data Acquisition)** pipeline for the QDArchive project.

The objective is to collect qualitative research datasets, extract structured metadata, download available files, and store everything in a SQLite database following the required schema.

---

# 🏛️ Repositories Used

| Repository            | Method         | URL                           |
| --------------------- | -------------- | ----------------------------- |
| DANS SSH DataStations | REST API       | https://ssh.datastations.nl   |
| Open Data Uni Halle   | OAI-PMH + HTML | https://opendata.uni-halle.de |

---

# 📁 Project Structure

```
qdarchive/
│
├── main.py
├── requirements.txt
├── README.md
│
├── db/
│   ├── database.py
│   └── schema.sql
│
├── pipeline/
│   └── downloader.py
│
├── scrapers/
│   ├── dans_scraper.py
│   └── uni_halle_scraper.py
│
├── data/                (excluded from GitHub)
└── *.db                 SQLite database
```

---

# 🧱 Database Schema

The database follows the required structure with six tables:

* repositories
* projects
* files
* keywords
* person_role
* licenses

### Constraints

* FILES.status ∈ {SUCCEEDED, FAILED_SERVER_UNRESPONSIVE, FAILED_LOGIN_REQUIRED, FAILED_TOO_LARGE}
* PERSON_ROLE.role ∈ {AUTHOR, UPLOADER, OWNER, OTHER, UNKNOWN}

---

# ⚙️ Data Acquisition Methods

## 🔹 DANS — REST API (Dataverse)

Endpoints used:

```
/api/search
/api/datasets/:persistentId
/api/access/datafile/{id}
```

Pipeline:

1. Search datasets using broad queries
2. Filter using qualitative keywords
3. Extract metadata
4. Download all accessible files

---

## 🔹 Uni Halle — OAI-PMH + HTML Scraping

Endpoints used:

```
ListRecords (oai_dc)
resumptionToken pagination
```

Pipeline:

1. Harvest metadata using OAI-PMH
2. Extract title and description
3. Visit project pages
4. Scrape `/bitstream/` links
5. Download files

---

# 📊 Results

| Metric                | Value                   |
| --------------------- | ----------------------- |
| Total data downloaded | ~3.5 GB                 |
| Projects collected    | Hundreds                |
| File types            | PDF, XML, TXT, datasets |
| Database              | Fully populated         |

---

# 📥 File Download Logic

| Status                     | Meaning                      |
| -------------------------- | ---------------------------- |
| SUCCEEDED                  | File downloaded successfully |
| FAILED_LOGIN_REQUIRED      | Requires authentication      |
| FAILED_TOO_LARGE           | Skipped due to size          |
| FAILED_SERVER_UNRESPONSIVE | Network/server issue         |

---

# ⚠️ Technical Challenges

1. Many Halle records contain metadata but no downloadable files
2. Most DANS datasets require login
3. Metadata is inconsistent and incomplete
4. Some files are very large
5. Pagination differs between APIs

---

# 🧠 Design Decisions

* Apply keyword filtering for qualitative datasets
* Preserve raw metadata without modification
* Use modular architecture (scrapers, pipeline, database)
* Ensure robustness with retries and duplicate checks

---

# 🚀 Usage

Install dependencies:

```
pip install -r requirements.txt
```

Run scrapers:

```
python main.py --repo dans
python main.py --repo halle
```

---

# 📂 Data Availability

The `data/` folder (~3.5 GB) is not included in this repository.
It is uploaded separately via FAUbox / Google Drive.

---

# ✅ Submission Checklist

* Database created and populated
* Metadata stored correctly
* Files downloaded and classified
* Schema constraints respected
* README completed
* Data uploaded separately

---

# 📌 Conclusion

This pipeline demonstrates multi-source data acquisition using REST APIs and OAI-PMH, automated metadata extraction, and robust file downloading. A substantial dataset (~3.5 GB) was successfully collected and structured.

---

# 👨‍💻 Author

Syed Md Shorfuddin
M.Sc. Data Science
Friedrich-Alexander-Universität Erlangen-Nürnberg
