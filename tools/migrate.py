import argparse
import base64
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import List

import boto3


def sha256_str(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def list_sql_files(dir_path: Path) -> List[Path]:
    files = [p for p in dir_path.glob("*.sql") if p.is_file()]
    return sorted(files, key=lambda p: p.name)  # V001__, V002__...


def exec_sql(rds, db_arn: str, secret_arn: str, sql: str, params=None):
    return rds.execute_statement(
        resourceArn=db_arn,
        secretArn=secret_arn,
        database="sentinel",
        sql=sql,
        parameters=params or [],
    )


def ensure_migrations_table(rds, db_arn: str, secret_arn: str) -> None:
    exec_sql(
        rds,
        db_arn,
        secret_arn,
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version     text PRIMARY KEY,
            applied_at  timestamptz NOT NULL DEFAULT now(),
            checksum    text NOT NULL
        );
        """,
    )


def get_applied_versions(rds, db_arn: str, secret_arn: str) -> dict:
    resp = exec_sql(rds, db_arn, secret_arn, "SELECT version, checksum FROM schema_migrations;")
    applied = {}
    for row in resp.get("records", []):
        ver = row[0]["stringValue"]
        chk = row[1]["stringValue"]
        applied[ver] = chk
    return applied


def apply_migration(rds, db_arn: str, secret_arn: str, version: str, sql_text: str, checksum: str) -> None:
    # Data API transaction
    tx = rds.begin_transaction(resourceArn=db_arn, secretArn=secret_arn, database="sentinel")
    tx_id = tx["transactionId"]
    try:
        rds.execute_statement(
            resourceArn=db_arn,
            secretArn=secret_arn,
            database="sentinel",
            transactionId=tx_id,
            sql=sql_text,
        )
        rds.execute_statement(
            resourceArn=db_arn,
            secretArn=secret_arn,
            database="sentinel",
            transactionId=tx_id,
            sql="INSERT INTO schema_migrations (version, checksum) VALUES (:v, :c)",
            parameters=[
                {"name": "v", "value": {"stringValue": version}},
                {"name": "c", "value": {"stringValue": checksum}},
            ],
        )
        rds.commit_transaction(resourceArn=db_arn, secretArn=secret_arn, transactionId=tx_id)
        print(f"[OK] Applied {version}")
    except Exception as exc:
        rds.rollback_transaction(resourceArn=db_arn, secretArn=secret_arn, transactionId=tx_id)
        print(f"[ERR] Migration {version} failed: {exc}")
        raise


def run_dir(rds, db_arn: str, secret_arn: str, dir_path: Path) -> None:
    if not dir_path.exists():
        return
    files = list_sql_files(dir_path)
    if not files:
        return

    ensure_migrations_table(rds, db_arn, secret_arn)
    applied = get_applied_versions(rds, db_arn, secret_arn)

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

        apply_migration(rds, db_arn, secret_arn, version, sql_text, checksum)


def main():
    parser = argparse.ArgumentParser(description="Apply DB migrations via RDS Data API.")
    parser.add_argument("--db-arn", required=True, help="RDS Cluster ARN (Data API enabled)")
    parser.add_argument("--secret-arn", required=True, help="Secrets Manager ARN for DB")
    parser.add_argument("--migrations", default="db/migrations", help="Path to migrations dir")
    parser.add_argument("--seeds", default="db/seed", help="Path to seeds dir (optional)")
    args = parser.parse_args()

    rds = boto3.client("rds-data")

    run_dir(rds, args.db_arn, args.secret_arn, Path(args.migrations))
    run_dir(rds, args.db_arn, args.secret_arn, Path(args.seeds))


if __name__ == "__main__":
    sys.exit(main())
