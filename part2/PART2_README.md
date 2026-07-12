# QDArchive Seeding – Part 2: Classification

**Student ID:** 23129103
**Project:** SQ26 – Seeding QDArchive
**Builds on:** Part 1 database `23129103-seeding.db` (repos #5 DANS, #16 Open Data Uni Halle)

---

## What This Does

Implements Part 2 (Classification) on top of the Part 1 database:

1. **Schema migration** – adds `type`, `primary_class`, `secondary_class` to `PROJECTS`
   and `primary_class` to `FILES` (`01_migrate_schema.py`).
2. **Project-type classification** – assigns `PROJECT_TYPE`
   (`QDA_PROJECT` / `QD_PROJECT` / `OTHER_PROJECT` / `NOT_A_PROJECT`) to every
   project from its files' extensions (`02_classify_project_type.py`).
3. **ISIC Rev. 5 classification** – a TF-IDF content classifier matches each
   `QDA_PROJECT`/`QD_PROJECT` project's title+description+keywords against
   the ISIC Rev. 5 taxonomy at the **division** level (2 levels: section +
   division, e.g. `Q85`), assigning `primary_class` and (where a close
   second candidate exists) `secondary_class`. Each project's files inherit
   its `primary_class` (`03_classify_isic.py`).
4. **Report generation** – builds the required PDF (histogram + top-20
   table + comments, per repository) and the required XLSX extract
   (`04_generate_report.py`).

Run in order:
```bash
python3 01_migrate_schema.py 23129103-sq26-classification.db
python3 02_classify_project_type.py 23129103-sq26-classification.db
python3 03_classify_isic.py 23129103-sq26-classification.db
python3 04_generate_report.py
```

`isic_divisions.json` is a pre-extracted, cached version of
`ISIC5_Exp_Notes_11Mar2024.xlsx` (section + division titles/includes text,
with group/class text rolled up into their parent division) — built once and
reused so the classifier doesn't re-parse the 1000-row spreadsheet every run.

---

## Method Notes / Assumptions

- **PROJECT_TYPE rule** is extension-based only, per the slides:
  `QDA_PROJECT` (has a `.qdpx`/MaxQDA/NVivo/ATLAS.ti/etc. analysis file) →
  `QD_PROJECT` (has a primary-data-like file: pdf/doc/docx/txt/rtf/odt/
  image/audio/video) → `OTHER_PROJECT` (has some other recognisable data
  file: csv/xlsx/sav/shp/zip/json/...) → `NOT_A_PROJECT` otherwise.
  The three extension sets are documented at the top of
  `02_classify_project_type.py` and are cross-checked against both the
  vendor extension spreadsheet and the actual extensions present in this DB.
- **ISIC classification is metadata-only.** We only have the Part 1 SQLite
  database in this environment, not the actual downloaded data folder — so
  the classifier works from project title + description + keywords, not
  file *contents*. This is an honest, documented limitation (see Technical
  Challenges below), not a shortcut: a text-similarity match against the
  official ISIC division descriptions is a defensible proxy given what data
  is available, but it is not equivalent to reading the actual interview
  transcripts.
- **File-level classification is propagated from the project.** Since we
  don't have file contents to classify files individually, each file in a
  classified project simply inherits that project's `primary_class`. This
  is flagged rather than hidden.
- **`secondary_class`** is only populated when the second-best ISIC match
  scores at least 85% of the best match's similarity — otherwise there
  usually isn't a genuine second candidate, just noise.

---

## Results Summary (Step 4b form answers)

### Repository #5 — DANS SSH DataStations
- Projects: 4,874 total
  - `QDA_PROJECT`: 15
  - `QD_PROJECT`: 3,739
  - `OTHER_PROJECT`: 1,114
  - `NOT_A_PROJECT`: 6
- Classified (QDA+QD) with a primary class: 3,752
- **Dominant class: `Q85` – Education (431 projects, ~11.5% of classified)**

### Repository #16 — Open Data Uni Halle
- Projects: 2,637 total, **all** `NOT_A_PROJECT`
- Classified with a primary class: 0
- **Dominant class: none** — see Technical Challenges #1 below for why.

---

## Technical Challenges (data, not programming)

1. **Uni Halle has almost no file records.** The `FILES` table holds only
   25 rows for all 2,637 Uni Halle projects (all `file_type = 'none'`),
   versus 77,718 rows for DANS's 4,874 projects. Because `PROJECT_TYPE`
   depends entirely on file extensions, every Uni Halle project correctly
   falls to `NOT_A_PROJECT` and none reach the ISIC classifier. This traces
   back to Part 1's Uni Halle DSpace scraper not enumerating bitstreams per
   item — a data-acquisition gap worth revisiting (e.g. via the DSpace
   bitstream REST endpoint) before final submission, since it silently
   zeroes out an entire repository's classification results.
2. **Metadata-only classification produces some implausible top matches
   for DANS** (e.g. `H49` Land transport, `B09` Mining support ranking
   above what "should" intuitively be common for interview data). Many
   DANS records are single-interview deposits with a short, often
   Dutch-language title and little else — thin text gives the TF-IDF
   matcher little to work with, so a few generic words can tip the vote
   toward an unrelated division. This is a known ceiling of a text-only
   classifier and is disclosed rather than smoothed over.
3. **Keyword and license data are still unnormalised** (carried over from
   Part 1: comma-joined keyword strings, multiple licenses per project).
   These weren't touched here since Part 2's schema/classification tasks
   don't require it, but they would need cleaning before any keyword-based
   classification refinement or license-conflict resolution.
4. **Multiple ISIC candidates per project are common** but the assignment
   only asks for a two-level classification with an optional secondary
   class, so borderline cases (projects that genuinely span two domains,
   e.g. an education-sector oral history project about migration) are
   resolved to whichever division scores marginally higher, which is a
   simplification of genuinely multi-disciplinary qualitative research.

---

## Deliverables Checklist (per SQ26 slides, Part 2 Steps 4a–4d)

- [x] **4a** `23129103-sq26-classification.db` — commit to repo root, tag `classification-results`
- [x] **4b** Results-form answers — see "Results Summary" above (submit via the Google Form, once per repo)
- [x] **4c** `23129103-sq26-classification-results.xlsx` — columns: repository_id, project_type, project_title, primary_class, secondary_class, no_project_files
- [x] **4d** `23129103-sq26-classification-report.pdf` — per-repository histogram + top-20 table + comments
