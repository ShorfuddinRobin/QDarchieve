# QDArchive – Part 1 Data Acquisition Pipeline

This repository contains my implementation of **Part 1 (Data Acquisition)** for the *Seeding QDArchive* project.

The goal of this pipeline is to **automatically discover, download, and archive qualitative research datasets**, while storing their metadata in a structured database.

---

## Project Overview

The pipeline performs the following tasks:

1. **Dataset Discovery**

   * Searches public research repositories using APIs.
   * Currently supported repositories:

     * Zenodo
     * Dataverse

2. **Automated Download**

   * Downloads all files belonging to a dataset.
   * Each dataset is stored in its own directory.

3. **Metadata Collection**

   * Metadata for each dataset is stored in a **SQLite database**.

4. **Archive Creation**

   * Creates a structured local archive of qualitative research datasets.

---

## Repository Structure

```
QDArchive/

├── downloads/
│   ├── zenodo/
│   └── dataverse/

├── metadata.db
├── Pipeline.py
└── README.md
```

**downloads/**
Contains all downloaded datasets organized by repository and dataset ID.

**metadata.db**
SQLite database containing metadata for each dataset.

**Pipeline.py**
Main pipeline script for searching, downloading, and recording datasets.

---

## Metadata Database Schema

The SQLite database contains the following fields:

| Field              | Description                    |
| ------------------ | ------------------------------ |
| dataset_url        | URL of the dataset             |
| repository         | Source repository              |
| title              | Dataset title                  |
| author             | Dataset author                 |
| license            | Dataset license                |
| doi                | Digital Object Identifier      |
| download_timestamp | Timestamp of download          |
| local_directory    | Path to local dataset folder   |
| qda_filename       | Detected QDA file (if present) |

---

## Example Dataset Structure

```
downloads/
   zenodo/
      3384296/
         research_paper.pdf
         transcript.txt
         analysis.qdpx
```

Each dataset folder may contain:

* QDA analysis files (`.qdpx`, `.nvpx`, `.atlproj`)
* transcripts
* PDFs
* additional research materials

---

## Running the Pipeline

Install dependencies:

```
pip install requests
```

Run the pipeline:

```
python Pipeline.py
```

The script will:

1. Search repositories for qualitative research datasets
2. Download dataset files
3. Store metadata in the SQLite database

---

## Notes

Due to GitHub storage limitations, large dataset files may not be uploaded to this repository. The pipeline can be used to recreate the archive locally.

---

## Author

  Syed Md Shorfuddin

