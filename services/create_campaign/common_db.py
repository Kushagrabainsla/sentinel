import os
import psycopg2
import psycopg2.extras

def get_conn():
    return psycopg2.connect(
        host=os.environ["PG_HOST"],
        port=os.environ.get("PG_PORT", "5432"),
        dbname=os.environ["PG_DB"],
        user=os.environ["PG_USER"],
        password=os.environ["PG_PASS"],
        sslmode=os.environ.get("PG_SSLMODE", "require"),
    )

def fetch_one(sql, params=None):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, params or [])
        return cur.fetchone()

def execute(sql, params=None):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, params or [])
        conn.commit()