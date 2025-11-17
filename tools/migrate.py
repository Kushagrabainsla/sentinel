#!/usr/bin/env python3
import argparse
import hashlib
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import psycopg2
import psycopg2.extras


# ---------- Helpers ----------
def sha256_str(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def list_sql_files(dir_path: Path) -> List[Path]:
    files = [p for p in dir_path.glob("*.sql") if p.is_file()]
    return sorted(files, key=lambda p: p.name)  # V001__, V002__...


def connect_from_env(
    host: str = None,
    port: str = None,
    db: str = None,
    user: str = None,
    password: str = None,
    sslmode: str = None,
):
    dsn = {
        "host": host or os.environ.get("PGHOST"),
        "port": port or os.environ.get("PGPORT", "5432"),
        "dbname": db or os.environ.get("PGDATABASE") or os.environ.get("PG_DB"),
        "user": user or os.environ.get("PGUSER") or os.environ.get("PG_USER"),
        "password": password or os.environ.get("PGPASSWORD") or os.environ.get("PG_PASS"),
        "sslmode": sslmode or os.environ.get("PGSSLMODE", "require"),
    }
    missing = [k for k, v in dsn.items() if not v and k in ("host", "dbname", "user", "password")]
    if missing:
        raise RuntimeError(f"Missing required DB settings: {', '.join(missing)}")
    return psycopg2.connect(
        host=dsn["host"],
        port=dsn["port"],
        dbname=dsn["dbname"],
        user=dsn["user"],
        password=dsn["password"],
        sslmode=dsn["sslmode"],
    )


# ---------- Migration primitives ----------
def ensure_migrations_table(cur) -> None:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version     text PRIMARY KEY,
            applied_at  timestamptz NOT NULL DEFAULT now(),
            checksum    text NOT NULL
        );
        """
    )


def get_applied_versions(cur) -> Dict[str, str]:
    cur.execute("SELECT version, checksum FROM schema_migrations;")
    return {row[0]: row[1] for row in cur.fetchall()}


def apply_migration(conn, cur, version: str, sql_text: str, checksum: str) -> None:
    """
    Run one migration inside a transaction; record it in schema_migrations.
    """
    try:
        # psycopg2 starts a transaction automatically on first statement
        cur.execute(sql_text)
        cur.execute(
            "INSERT INTO schema_migrations (version, checksum) VALUES (%s, %s)",
            (version, checksum),
        )
        conn.commit()
        print(f"[OK] Applied {version}")
    except Exception as exc:
        conn.rollback()
        print(f"[ERR] Migration {version} failed: {exc}")
        raise


def run_dir(conn, cur, dir_path: Path) -> None:
    if not dir_path or not dir_path.exists():
        return
    files = list_sql_files(dir_path)
    if not files:
        return

    ensure_migrations_table(cur)
    applied = get_applied_versions(cur)

    for f in files:
        version = f.stem  # e.g., V001__init
        sql_text = f.read_text(encoding="utf-8")
        checksum = sha256_str(sql_text)

        if version in applied:
            if applied[version] != checksum:
                print(f"[WARN] {version} already applied but checksum differs. Skipping.")
            else:
                print(f"[SKIP] {version} already applied.")
            continue

        apply_migration(conn, cur, version, sql_text, checksum)


# ---------- CLI ----------
def main() -> int:
    ap = argparse.ArgumentParser(description="Apply DB migrations to Postgres (psycopg2).")
    ap.add_argument("--migrations", default="db/migrations", help="Path to migrations dir")
    ap.add_argument("--seeds", default="db/seed", help="Path to seeds dir (optional)")
    # Optional explicit connection args (otherwise read PG* env vars)
    ap.add_argument("--host")
    ap.add_argument("--port")
    ap.add_argument("--db")
    ap.add_argument("--user")
    ap.add_argument("--password")
    ap.add_argument("--sslmode")
    args = ap.parse_args()

    conn = connect_from_env(
        host=args.host,
        port=args.port,
        db=args.db,
        user=args.user,
        password=args.password,
        sslmode=args.sslmode,
    )
    try:
        with conn, conn.cursor() as cur:
            run_dir(conn, cur, Path(args.migrations))
            run_dir(conn, cur, Path(args.seeds))
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
