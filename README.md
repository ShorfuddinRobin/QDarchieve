# QDArchive Seeding – Part 1: Data Acquisition

**Student ID:** 23129103  
**GitHub Repository:** https://github.com/ShorfuddinRobin/QDarchieve  
**Project:** SQ26 – Seeding QDArchive  
**Supervisor:** Prof. Dr. Dirk Riehle, FAU Erlangen-Nürnberg

---

# Overview

This repository implements **Part 1 (Data Acquisition)** of the Seeding QDArchive project.

The objective of Part 1 is to:

- Discover qualitative research projects from the assigned repositories.
- Download all publicly accessible project files.
- Extract and preserve metadata without modification.
- Store all information in a structured SQLite database.
- Prepare the acquired data for Part 2 (Classification).

---

# Assigned Repositories

| ID | Repository | URL | Platform |
|----|------------|-----|----------|
| 5 | DANS SSH DataStations | https://ssh.datastations.nl | Dataverse |
| 16 | Open Data Uni Halle | https://opendata.uni-halle.de | DSpace 5/6 |

---

# Repository Structure

```text
QDarchieve/
│
├── 23129103-seeding.db
├── main.py
├── README.md
├── requirements.txt
├── .gitignore
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
├── export/
│   └── export_csv.py
│
├── scripts/
│   └── retry_failed.py
│
└── data/                     (uploaded separately)
    ├── dans/
    └── open-data-uni-halle/
```

---

# Database Schema

The acquisition database is stored as:

```text
23129103-seeding.db
```

The database contains six tables.

## REPOSITORIES

Stores repository information.

```text
id
name
url
```

---

## PROJECTS

Stores one record for every discovered project.

```text
id
query_string
repository_id
repository_url
project_url
version
title
description
language
doi
upload_date
download_date
download_repository_folder
download_project_folder
download_version_folder
download_method
```

---

## FILES

Stores one record for every downloaded (or attempted) file.

```text
id
project_id
file_name
file_type
status
```

Allowed status values:

- SUCCEEDED
- FAILED_LOGIN_REQUIRED
- FAILED_SERVER_UNRESPONSIVE
- FAILED_TOO_LARGE

---

## KEYWORDS

```text
id
project_id
keyword
```

---

## PERSON_ROLE

```text
id
project_id
name
role
```

Allowed roles:

- AUTHOR
- UPLOADER
- OWNER
- OTHER
- UNKNOWN

---

## LICENSES

```text
id
project_id
license
```

---

# How to Run

## Requirements

- Python 3.10+
- pip

---

## Installation

```bash
git clone https://github.com/ShorfuddinRobin/QDarchieve
cd QDarchieve

python3 -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt
```

---

## Run the Pipeline

Initialise database

```bash
python3 main.py --init-only
```

Run DANS only

```bash
python3 main.py --repo dans
```

Run Open Data Uni Halle only

```bash
python3 main.py --repo halle
```

Run both repositories

```bash
python3 main.py
```

Export CSV files

```bash
python3 main.py --export-csv
```

Retry failed downloads

```bash
python3 scripts/retry_failed.py
```

---

# Search Queries

The following search queries were used to maximise retrieval of qualitative research projects.

| Query | Purpose |
|--------|---------|
| qdpx | REFI-QDA exchange format |
| mqda | MAXQDA projects |
| nvp | NVivo projects |
| interview study | Interview-based studies |
| qualitative research | Broad search |
| qualitative data | Broad search |

---

# Download Method

| Repository | Method | Description |
|------------|--------|-------------|
| DANS SSH DataStations | API-CALL | Uses the Dataverse Search API and Access API. |
| Open Data Uni Halle | SCRAPING | Uses DSpace HTML pages together with REST metadata endpoints. |

---

# Data Folder

The **data/** directory is excluded from Git because it contains several gigabytes of downloaded research data.

The folder is uploaded separately to **FAUbox / Google Drive**.

Example structure:

```text
data/
├── dans/
│   └── doi_10.xxxxx/
│       ├── interview_data.qdpx
│       └── codebook.pdf
│
└── open-data-uni-halle/
    └── project_folder/
        ├── transcript.docx
        └── report.pdf
```

---

# Technical Challenges

Programming issues are intentionally omitted. Only data-related challenges are reported.

## 1. Inconsistent Metadata

Metadata completeness differs greatly between repositories. Missing descriptions, inconsistent dates and multiple language formats are common.

---

## 2. Keyword Quality

Keywords often contain multiple concepts within one field or use inconsistent separators. Original values were preserved.

---

## 3. Restricted Files

Many datasets provide public metadata but restrict access to downloadable files. These files are stored with the status:

- FAILED_LOGIN_REQUIRED

---

## 4. Contributor Roles

Repositories do not always distinguish clearly between author, uploader and owner. Roles were assigned whenever they could be inferred.

---

## 5. Multiple Licenses

Some datasets contain more than one license. Each license is stored as a separate row in the LICENSES table.

---

## 6. Dataset Versions

DANS maintains multiple versions of datasets. Only the latest version is downloaded.

---

## 7. QDA File Discovery

Many repositories do not explicitly identify QDA software files. Discovery therefore depends on available metadata and downloadable file lists.

---

# QDArchive Seeding – Part 2: Classification

## Overview

Part 2 extends the Part 1 data acquisition pipeline by classifying the collected projects according to the SQ26 assignment requirements.

Using the database created in Part 1 (`23129103-seeding.db`), the classification pipeline:

- Migrates the database schema
- Determines the project type
- Assigns ISIC Revision 5 classifications
- Generates the required PDF report
- Generates the required Excel results

---

# Classification Database

Part 2 creates a new SQLite database:

```text
23129103-sq26-classification.db
```

The original acquisition database remains unchanged.

The following fields are added to the **PROJECTS** table.

| Column | Description |
|---------|-------------|
| type | Project type |
| primary_class | ISIC primary classification |
| secondary_class | ISIC secondary classification |

The **FILES** table is extended with:

| Column | Description |
|---------|-------------|
| primary_class | Inherited project classification |

---

# Classification Workflow

The pipeline consists of four stages.

## Stage 1 — Schema Migration

The Part 1 database is copied and extended with the required classification columns.

---

## Stage 2 — Project Type Classification

Projects are classified using the file extensions stored in the FILES table.

Possible project types are:

| Project Type | Description |
|--------------|-------------|
| **QDA_PROJECT** | Contains recognised qualitative analysis software files (QDPX, NVivo, MAXQDA, Atlas.ti, etc.) |
| **QD_PROJECT** | Contains qualitative research data files such as PDF, DOCX, TXT, images, audio or video. |
| **OTHER_PROJECT** | Contains files but does not satisfy the previous categories. |
| **NOT_A_PROJECT** | No qualifying project files detected. |

---

## Stage 3 — ISIC Revision 5 Classification

Projects classified as **QDA_PROJECT** or **QD_PROJECT** are compared against the official ISIC Revision 5 taxonomy.

The classifier analyses:

- Project title
- Project description
- Project keywords

A TF-IDF similarity model compares the project metadata with the official ISIC division descriptions.

The highest-scoring division becomes the **Primary Class**.

When another division receives a similar score, it is stored as the **Secondary Class**.

---

## Stage 4 — Report Generation

The pipeline automatically generates:

- Classification database
- Classification report (PDF)
- Classification results (XLSX)

The PDF report contains:

- Histogram of primary classes
- Top 20 ISIC classes
- Repository-specific comments

---

# Results Summary

## Repository #5 — DANS SSH DataStations

| Metric | Value |
|---------|------:|
| Total Projects | 4,874 |
| QDA_PROJECT | 15 |
| QD_PROJECT | 3,739 |
| OTHER_PROJECT | 1,114 |
| NOT_A_PROJECT | 6 |

Projects receiving a primary ISIC classification:

**3,752**

Most common class:

**Q85 – Education**

---

## Repository #16 — Open Data Uni Halle

| Metric | Value |
|---------|------:|
| Total Projects | 2,637 |
| Classified Projects | 0 |

The available metadata and file information did not satisfy the rules required to classify projects as **QDA_PROJECT** or **QD_PROJECT**. Consequently, no ISIC classifications were assigned for this repository.

---

# Classification Outputs

Part 2 generates the following deliverables.

```text
23129103-sq26-classification.db
23129103-sq26-classification-results.xlsx
23129103-sq26-classification-report.pdf
```

---

# Technical Challenges (Part 2)

## 1. Metadata Quality

Many projects contain only short titles or limited descriptions, reducing the amount of information available for metadata-based classification.

---

## 2. Keyword Consistency

Keywords are often stored as comma-separated strings or mixed-language values. Original metadata was preserved without modification.

---

## 3. Restricted Files

Many datasets contain restricted files requiring authentication. These files cannot be analysed directly during classification.

---

## 4. Metadata-Based Classification

Classification relies on project metadata rather than file contents. Projects with limited metadata may therefore receive less specific ISIC classifications.

---

## 5. Repository Differences

DANS contains substantially richer metadata and downloadable files, enabling successful classification for most projects.

Open Data Uni Halle contains comparatively limited classifiable metadata and file information, resulting in no ISIC assignments.

---

# Part 2 Submission Checklist

- [x] `23129103-sq26-classification.db`
- [x] Classification pipeline completed
- [x] Classification report (PDF)
- [x] Classification results (XLSX)
- [x] Updated README

---

# Overall Project

This repository now contains the complete implementation of:

- **Part 1 – Data Acquisition**
- **Part 2 – Classification**

The complete workflow includes:

- Multi-repository data acquisition
- Metadata extraction
- SQLite database generation
- Project type classification
- ISIC Revision 5 classification
- Automated PDF report generation
- Automated Excel report generation

while preserving the original repository metadata throughout the pipeline.

---

# Final Submission Checklist

## Part 1

- [x] Acquisition database
- [x] Data acquisition pipeline
- [x] Downloaded research data
- [x] GitHub repository
- [x] README documentation

## Part 2

- [x] Classification database
- [x] Classification report (PDF)
- [x] Classification results (XLSX)
- [x] Classification pipeline
- [x] Updated repository documentation

---

# License

This repository was developed for academic purposes as part of the **SQ26 – Seeding QDArchive** project at **Friedrich-Alexander-Universität Erlangen-Nürnberg** under the supervision of **Prof. Dr. Dirk Riehle**.

The downloaded research data remains subject to the original licenses specified by their respective repositories.
