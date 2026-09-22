"""
TimeTrack's persistence layer -- SQLite, shared by every tool in this
project. Same tested file from the Persistence video, unchanged.
"""

from pathlib import Path
from dotenv import load_dotenv
import mysql.connector
import os
from mysql.connector import Error
load_dotenv()

DB_PATH = Path(__file__).parent / "timetrack.db"

connection = None
cursor = None

try:
    connection = mysql.connector.connect( host=os.getenv("DB_HOST"), database=os.getenv("DB_NAME"), user=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD"), port=int(os.getenv("DB_PORT", 3306)), ) 
    if connection.is_connected():
         db_info = connection.get_server_info() 
         print("Connected to MySQL Server version:", db_info) 
         cursor = connection.cursor() 
         cursor.execute("SELECT DATABASE();") 
         record = cursor.fetchone() 
         print("Connected to database:", record)
except Error as e:
    print("Error while connecting to MySQL", e)
finally:
    if connection.is_connected():
        cursor.close()
        connection.close()
        print("MySQL connection is closed")

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=int(os.getenv("DB_PORT", 3306)),
    )

def init_db(): 
    conn = get_connection() 
    cursor = conn.cursor() 
    cursor.execute(""" CREATE TABLE IF NOT EXISTS time_entries ( id INT AUTO_INCREMENT PRIMARY KEY, employee_name VARCHAR(255) NOT NULL, project VARCHAR(255) NOT NULL, entry_date DATE NOT NULL, hours DECIMAL(5,2) NOT NULL, description TEXT NOT NULL ) """) 
    cursor.execute("SELECT COUNT(*) FROM time_entries") 
    count = cursor.fetchone()[0] 
    if count == 0: 
        seed = [ 
            ( "Asha Patel", "Website Redesign", "2026-09-08", 6.5, "Homepage layout", ),
            ( "Asha Patel", "Website Redesign", "2026-09-09", 7.0, "Mobile responsive fixes", ),
            ( "Asha Patel", "Client Onboarding", "2026-09-10", 3.0, "Kickoff call + notes", ), 
            ( "Rahul Mehta", "Website Redesign", "2026-09-08", 5.5, "API integration", ),
            ( "Rahul Mehta", "Internal Tools", "2026-09-09", 8.0, "Dashboard bug fixes", ), ] cursor.executemany( """ INSERT INTO time_entries (employee_name, project, entry_date, hours, description) VALUES (%s, %s, %s, %s, %s) """, seed, ) 
        conn.commit()
    cursor.close() 
    conn.close()

def _row_to_dict(row) -> dict:
    return {
        "id": row["id"],
        "employee_name": row["employee_name"],
        "project": row["project"],
        "entry_date": row["entry_date"],
        "hours": row["hours"],
        "description": row["description"],
    }


def list_all_entries() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM time_entries ORDER BY entry_date DESC, id DESC").fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def log_time(employee_name: str, project: str, entry_date: str, hours: float, description: str = "") -> dict:
    if hours <= 0:
        raise ValueError("hours must be a positive number")
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO time_entries (employee_name, project, entry_date, hours, description) "
        "VALUES (?, ?, ?, ?, ?)",
        (employee_name, project, entry_date, hours, description),
    )
    conn.commit()
    new_id = cursor.lastrowid
    row = conn.execute("SELECT * FROM time_entries WHERE id = ?", (new_id,)).fetchone()
    conn.close()
    return _row_to_dict(row)


def get_timesheet(employee_name: str, start_date: str | None = None, end_date: str | None = None) -> list[dict]:
    conn = get_connection()
    query = "SELECT * FROM time_entries WHERE employee_name = ?"
    params: list = [employee_name]
    if start_date:
        query += " AND entry_date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND entry_date <= ?"
        params.append(end_date)
    query += " ORDER BY entry_date"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def list_projects() -> list[str]:
    conn = get_connection()
    rows = conn.execute("SELECT DISTINCT project FROM time_entries ORDER BY project").fetchall()
    conn.close()
    return [r["project"] for r in rows]


def get_project_summary(project: str) -> dict:
    conn = get_connection()
    rows = conn.execute(
        "SELECT employee_name, SUM(hours) as total_hours FROM time_entries "
        "WHERE project = ? GROUP BY employee_name ORDER BY employee_name",
        (project,),
    ).fetchall()
    conn.close()
    if not rows:
        raise ValueError(f"No time logged against project '{project}'")
    by_employee = {r["employee_name"]: r["total_hours"] for r in rows}
    return {
        "project": project,
        "total_hours": sum(by_employee.values()),
        "by_employee": by_employee,
    }