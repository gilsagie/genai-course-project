import os
import re
import platform
from dotenv import load_dotenv
import sys

APP_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)
from tools import docker_is_on


def _run(conn, batches):
        with conn:
            with conn.cursor() as cursor:
                for batch in batches:
                    cursor.execute(batch)


def create_schedule_database():
    load_dotenv()
    SA_PASSWORD = os.getenv("MSSQL_SA_PASSWORD")
    ROOT = os.path.realpath(__file__)
    for _ in range(3):
        ROOT = os.path.dirname(ROOT)
    SQL_PATH = os.path.join(ROOT, "docs", "db_Tech.sql")

    is_mac = platform.system() == "Darwin"
    
    with open(SQL_PATH, "r", encoding="utf-8-sig") as f:
        sql_script = f.read()

    # Split script into individual batches on standalone 'GO' lines
    batches = re.split(r"^\s*GO\s*$", sql_script, flags=re.MULTILINE | re.IGNORECASE)

    master_batches = []
    tech_batches = []
    on_tech = False
    for batch in batches:
        text = batch.strip()
        if text == "":
            continue
        if re.match(r"(?is)^use\s+\w+\s*;?$", text):
            continue
        if on_tech:
            tech_batches.append(text)
        else:
            master_batches.append(text)
            if re.search(r"(?i)create\s+database", text):
                on_tech = True

    if is_mac:
        if not docker_is_on():
            print("Docker is off or tech-sql is stopped. Run: docker start tech-sql")
            return
        import pymssql
        print("Mac detected: Building database inside Docker...")
        master = pymssql.connect(
            server="127.0.0.1", port=1433, user="sa",
            password=SA_PASSWORD, database="master", autocommit=True,
        )
        _run(master, master_batches)
        tech = pymssql.connect(
            server="127.0.0.1", port=1433, user="sa",
            password=SA_PASSWORD, database="Tech", autocommit=True,
        )
        _run(tech, tech_batches)
    else:
        import pyodbc
        print("Windows detected: Building database natively...")
        drivers = [d for d in pyodbc.drivers() if "SQL Server" in d]
        driver = drivers[-1] if drivers else "SQL Server"
        master = pyodbc.connect(
            f"DRIVER={{{driver}}};SERVER=localhost\\SQLEXPRESS;"
            "DATABASE=master;Trusted_Connection=yes;TrustServerCertificate=yes;",
            autocommit=True,
        )
        _run(master, master_batches)
        tech = pyodbc.connect(
            f"DRIVER={{{driver}}};SERVER=localhost\\SQLEXPRESS;"
            "DATABASE=Tech;Trusted_Connection=yes;TrustServerCertificate=yes;",
            autocommit=True,
        )
        _run(tech, tech_batches)

if __name__ == "__main__":
    create_schedule_database()
