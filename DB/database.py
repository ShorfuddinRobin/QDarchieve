"""
db/database.py – SQLite access helpers for QDArchive seeding pipeline.
"""
import sqlite3
from pathlib import Path

DB_NAME = "23129103-seeding.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_db_path() -> Path:
    return Path(__file__).parent.parent / DB_NAME


# 🔥 SINGLE GLOBAL CONNECTION (fix DB locked issue)
_conn = None


def get_connection():
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(get_db_path(), check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=WAL;")
        _conn.execute("PRAGMA foreign_keys=ON;")
    return _conn


def init_db():
    conn = get_connection()
    with open(SCHEMA_PATH, "r", encoding="utf-8") as fh:
        conn.executescript(fh.read())
    conn.commit()
    print(f"[db] Initialised database at {get_db_path()}")


# ------------------------------------------------------------------
# SEED
# ------------------------------------------------------------------

KNOWN_REPOSITORIES = [
    (5,  "dans", "https://ssh.datastations.nl"),
    (16, "open-data-uni-halle", "https://opendata.uni-halle.de"),
]


def seed_repositories():
    conn = get_connection()
    cur = conn.cursor()

    for repo_id, name, url in KNOWN_REPOSITORIES:
        cur.execute(
            "INSERT OR IGNORE INTO REPOSITORIES(id, name, url) VALUES (?,?,?)",
            (repo_id, name, url),
        )

    conn.commit()
    print("[db] Repositories seeded.")


# ------------------------------------------------------------------
# INSERTS
# ------------------------------------------------------------------

def insert_project(data: dict) -> int:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO PROJECTS (
            query_string, repository_id, repository_url, project_url,
            version, title, description, language, doi,
            upload_date, download_date,
            download_repository_folder, download_project_folder,
            download_version_folder, download_method
        ) VALUES (
            :query_string, :repository_id, :repository_url, :project_url,
            :version, :title, :description, :language, :doi,
            :upload_date, :download_date,
            :download_repository_folder, :download_project_folder,
            :download_version_folder, :download_method
        )
        """,
        data,
    )

    conn.commit()
    return cur.lastrowid


def project_url_exists(project_url: str) -> bool:
    conn = get_connection()
    row = conn.execute(
        "SELECT id FROM PROJECTS WHERE project_url=?", (project_url,)
    ).fetchone()
    return row is not None
