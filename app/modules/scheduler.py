import os
from datetime import datetime, timedelta
import platform

DB_NOW = "2024-04-16 10:00:00"

# Need to make sure these are the same as the positions in the database
POSITIONS_DICT = {"Python Developer": "Python Dev", "SQL Developer": "Sql Dev", "Data Analyst": "Analyst", "Machine Learning Engineer": "ML"}

# When running in streamlit online there is no sql database to pull data from so we use this.
def open_slots(earliest):
    slots = []
    cursor = earliest.replace(minute=0, second=0, microsecond=0)
    if cursor < earliest:
        cursor = cursor + timedelta(hours=1)
    while len(slots) < 3:
        if cursor.weekday() not in (0, 5) and 9 <= cursor.hour <= 17:
            slots.append(cursor.strftime("%Y-%m-%d %H:%M"))
        cursor = cursor + timedelta(hours=1)
    return slots

def get_earliest_time(when=None, now=None):
    if now == None or now == "":
        now = when
    if when == None or when == "":
        when = now
    if when == None or when == "":
        when = DB_NOW
        now = DB_NOW
    message_time = datetime.strptime(when, "%Y-%m-%d %H:%M:%S")
    now_time = datetime.strptime(now, "%Y-%m-%d %H:%M:%S")
    buffer = now_time + timedelta(hours=1)
    return message_time if message_time > buffer else buffer

def closest_dates(when=None, now=None, position=None):
    earliest = get_earliest_time(when, now)
    earliest_text = earliest.strftime("%Y-%m-%d %H:%M:%S")
    is_mac = platform.system() == "Darwin"
    if is_mac:
        import pymssql
        from dotenv import load_dotenv
        load_dotenv()
        conn = pymssql.connect(
            server="127.0.0.1", port=1433, user="sa",
            password=os.getenv("MSSQL_SA_PASSWORD"), database="Tech", autocommit=True,
        )
        mark = "%s"
    elif platform.system() == "Windows":
        import pyodbc
        drivers = [d for d in pyodbc.drivers() if "SQL Server" in d]
        driver = drivers[-1] if drivers else "SQL Server"
        conn = pyodbc.connect(
            f"DRIVER={{{driver}}};SERVER=localhost\\SQLEXPRESS;"
            "DATABASE=Tech;Trusted_Connection=yes;TrustServerCertificate=yes;",
            autocommit=True,
        )
        mark = "?"
    else:
        return open_slots(earliest)
    sql = f"""
        SELECT TOP 3 [date], [time]
        FROM dbo.Schedule
        WHERE position = {mark}
          AND available = 1
          AND DATEADD(day, DATEDIFF(day, 0, [date]), CAST([time] AS datetime)) >= {mark}
        ORDER BY [date], [time]
    """
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, (POSITIONS_DICT[position], earliest_text))
            rows = cursor.fetchall()
    slots = []
    for row in rows:
        slots.append(str(row[0])[:10] + " " + str(row[1])[:5])
    return slots

def schedule_time(code, message_time):
    text = (code or "").strip()
    if text == "" or text == "NOW":
        return message_time
    try:
        parts = text.split(",")
        weeks = int(parts[0])
        day = int(parts[1])  # monday is 0
        hour = "09:00"
        if len(parts) == 3:
            hour = parts[2]
        # go back to monday of that week, then add the weeks and the day
        monday = message_time - timedelta(days=message_time.weekday())
        target = monday + timedelta(weeks=weeks, days=day)
        clock = datetime.strptime(hour, "%H:%M")
        target = target.replace(hour=clock.hour, minute=clock.minute, second=0)
        if weeks == 0 and target <= message_time:
            target = target + timedelta(days=7)
        return target
    except (ValueError, IndexError):
        # bad code, use the message time
        return message_time
