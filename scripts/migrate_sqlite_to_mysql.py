"""
One-off migration: copy data from the legacy ai_recruitment_copilot.db
(SQLite) into the freshly-initialized MySQL hirepilot_db.

Only copies columns that exist in both the SQLite export and the
current MySQL schema; MySQL-only columns are left at their defaults.
Safe to run only once against empty MySQL tables (uses INSERT, not
UPSERT) -- run order matters for the FK-dependent tables.
"""
import sqlite3
import pymysql

SQLITE_PATH = "ai_recruitment_copilot.db"

MYSQL_CFG = dict(
    host="localhost",
    port=3306,
    user="hirepilot_user",
    password="HirePilot!2026",
    database="hirepilot_db",
)

# Order matters: parents before children (FK dependencies).
TABLES = [
    "skills",
    "jobs",
    "candidates",
    "job_skills",
    "candidate_skills",
    "resume_data",
    "applications",
    "interviews",
    "employees",
    "activities",
    "hr_users",
]


def main():
    sconn = sqlite3.connect(SQLITE_PATH)
    sconn.row_factory = sqlite3.Row
    scur = sconn.cursor()

    mconn = pymysql.connect(**MYSQL_CFG)
    mcur = mconn.cursor()

    # Get full MySQL column metadata so we only insert columns that exist there,
    # and can backfill NOT NULL columns with no default that SQLite doesn't have.
    mysql_column_info = {}
    for t in TABLES:
        mcur.execute(
            "SELECT COLUMN_NAME, IS_NULLABLE, COLUMN_DEFAULT, DATA_TYPE, EXTRA "
            "FROM information_schema.columns WHERE table_schema=%s AND table_name=%s",
            (MYSQL_CFG["database"], t),
        )
        mysql_column_info[t] = {
            row[0]: {"nullable": row[1] == "YES", "default": row[2], "type": row[3], "extra": row[4]}
            for row in mcur.fetchall()
        }

    def default_for(data_type: str):
        if data_type == "json":
            return "[]"
        if data_type in ("int", "bigint", "smallint", "tinyint"):
            return 0
        if data_type in ("datetime", "timestamp", "date"):
            return None
        return ""

    mcur.execute("SET FOREIGN_KEY_CHECKS=0")

    for t in TABLES:
        scur.execute(f'SELECT * FROM "{t}"')
        rows = [dict(r) for r in scur.fetchall()]
        if not rows:
            print(f"{t}: no rows to migrate")
            continue

        info = mysql_column_info[t]
        sqlite_cols = [c for c in rows[0].keys() if c in info]

        # Columns MySQL requires (NOT NULL, no default, not auto_increment) that
        # SQLite didn't have -- fill with a safe empty value.
        required_extra = [
            c for c, meta in info.items()
            if c not in sqlite_cols
            and not meta["nullable"]
            and meta["default"] is None
            and "auto_increment" not in meta["extra"]
        ]

        cols = sqlite_cols + required_extra
        placeholders = ", ".join(["%s"] * len(cols))
        col_list = ", ".join(f"`{c}`" for c in cols)
        sql = f"INSERT INTO `{t}` ({col_list}) VALUES ({placeholders})"

        values = [
            tuple(row[c] for c in sqlite_cols)
            + tuple(default_for(info[c]["type"]) for c in required_extra)
            for row in rows
        ]
        mcur.executemany(sql, values)
        mconn.commit()
        print(f"{t}: migrated {len(rows)} rows")

    mcur.execute("SET FOREIGN_KEY_CHECKS=1")
    mconn.commit()

    mcur.close()
    mconn.close()
    sconn.close()
    print("Migration complete.")


if __name__ == "__main__":
    main()
