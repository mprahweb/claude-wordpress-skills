import sqlite3
import os
from datetime import datetime
from typing import List, Optional
from models import Customer, Project, Task, TimeEntry

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zeiterfassung.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            number TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            is_global INTEGER DEFAULT 1,
            project_id INTEGER,
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS time_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            project_id INTEGER NOT NULL,
            task_id INTEGER,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            duration_minutes INTEGER NOT NULL,
            note TEXT DEFAULT '',
            invoiced INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (project_id) REFERENCES projects(id),
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        )
    """)

    conn.commit()
    conn.close()


# ── Customers ──────────────────────────────────────────────────────────────

def get_all_customers() -> List[Customer]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM customers ORDER BY number").fetchall()
    conn.close()
    return [Customer(id=r["id"], number=r["number"], name=r["name"], created_at=r["created_at"]) for r in rows]


def save_customer(customer: Customer) -> int:
    conn = get_connection()
    c = conn.cursor()
    if customer.id is None:
        c.execute("INSERT INTO customers (number, name) VALUES (?, ?)", (customer.number, customer.name))
        new_id = c.lastrowid
    else:
        c.execute("UPDATE customers SET number=?, name=? WHERE id=?", (customer.number, customer.name, customer.id))
        new_id = customer.id
    conn.commit()
    conn.close()
    return new_id


def delete_customer(customer_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM customers WHERE id=?", (customer_id,))
    conn.commit()
    conn.close()


# ── Projects ───────────────────────────────────────────────────────────────

def get_projects(customer_id: Optional[int] = None) -> List[Project]:
    conn = get_connection()
    if customer_id is not None:
        rows = conn.execute(
            "SELECT p.*, c.name as customer_name FROM projects p "
            "JOIN customers c ON p.customer_id = c.id "
            "WHERE p.customer_id=? ORDER BY p.name",
            (customer_id,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT p.*, c.name as customer_name FROM projects p "
            "JOIN customers c ON p.customer_id = c.id ORDER BY c.number, p.name"
        ).fetchall()
    conn.close()
    return [Project(
        id=r["id"], customer_id=r["customer_id"], name=r["name"],
        description=r["description"] or "", created_at=r["created_at"],
        customer_name=r["customer_name"]
    ) for r in rows]


def save_project(project: Project) -> int:
    conn = get_connection()
    c = conn.cursor()
    if project.id is None:
        c.execute(
            "INSERT INTO projects (customer_id, name, description) VALUES (?, ?, ?)",
            (project.customer_id, project.name, project.description)
        )
        new_id = c.lastrowid
    else:
        c.execute(
            "UPDATE projects SET customer_id=?, name=?, description=? WHERE id=?",
            (project.customer_id, project.name, project.description, project.id)
        )
        new_id = project.id
    conn.commit()
    conn.close()
    return new_id


def delete_project(project_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM projects WHERE id=?", (project_id,))
    conn.commit()
    conn.close()


# ── Tasks ──────────────────────────────────────────────────────────────────

def get_tasks(project_id: Optional[int] = None) -> List[Task]:
    """Returns global tasks + optionally tasks for a specific project."""
    conn = get_connection()
    if project_id is not None:
        rows = conn.execute(
            "SELECT * FROM tasks WHERE is_global=1 OR project_id=? ORDER BY name",
            (project_id,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM tasks ORDER BY is_global DESC, name").fetchall()
    conn.close()
    return [Task(
        id=r["id"], name=r["name"], is_global=bool(r["is_global"]),
        project_id=r["project_id"], created_at=r["created_at"]
    ) for r in rows]


def save_task(task: Task) -> int:
    conn = get_connection()
    c = conn.cursor()
    if task.id is None:
        c.execute(
            "INSERT INTO tasks (name, is_global, project_id) VALUES (?, ?, ?)",
            (task.name, int(task.is_global), task.project_id)
        )
        new_id = c.lastrowid
    else:
        c.execute(
            "UPDATE tasks SET name=?, is_global=?, project_id=? WHERE id=?",
            (task.name, int(task.is_global), task.project_id, task.id)
        )
        new_id = task.id
    conn.commit()
    conn.close()
    return new_id


def delete_task(task_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()


# ── Time Entries ───────────────────────────────────────────────────────────

def _row_to_entry(r) -> TimeEntry:
    return TimeEntry(
        id=r["id"],
        customer_id=r["customer_id"],
        project_id=r["project_id"],
        task_id=r["task_id"],
        start_time=r["start_time"],
        end_time=r["end_time"],
        duration_minutes=r["duration_minutes"],
        note=r["note"] or "",
        invoiced=bool(r["invoiced"]),
        created_at=r["created_at"],
        customer_name=r["customer_name"],
        project_name=r["project_name"],
        task_name=r["task_name"],
        customer_number=r["customer_number"],
    )


def get_time_entries(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    customer_id: Optional[int] = None,
    project_id: Optional[int] = None,
) -> List[TimeEntry]:
    conn = get_connection()
    query = """
        SELECT te.*,
               c.name  AS customer_name,
               c.number AS customer_number,
               p.name  AS project_name,
               t.name  AS task_name
        FROM time_entries te
        LEFT JOIN customers c ON te.customer_id = c.id
        LEFT JOIN projects  p ON te.project_id  = p.id
        LEFT JOIN tasks     t ON te.task_id     = t.id
        WHERE 1=1
    """
    params = []
    if date_from:
        query += " AND te.start_time >= ?"
        params.append(date_from)
    if date_to:
        query += " AND te.start_time <= ?"
        params.append(date_to + " 23:59:59")
    if customer_id:
        query += " AND te.customer_id = ?"
        params.append(customer_id)
    if project_id:
        query += " AND te.project_id = ?"
        params.append(project_id)
    query += " ORDER BY te.start_time DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [_row_to_entry(r) for r in rows]


def save_time_entry(entry: TimeEntry) -> int:
    conn = get_connection()
    c = conn.cursor()
    if entry.id is None:
        c.execute(
            "INSERT INTO time_entries (customer_id, project_id, task_id, start_time, end_time, duration_minutes, note, invoiced) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (entry.customer_id, entry.project_id, entry.task_id,
             entry.start_time, entry.end_time, entry.duration_minutes,
             entry.note, int(entry.invoiced))
        )
        new_id = c.lastrowid
    else:
        c.execute(
            "UPDATE time_entries SET customer_id=?, project_id=?, task_id=?, start_time=?, end_time=?, "
            "duration_minutes=?, note=?, invoiced=? WHERE id=?",
            (entry.customer_id, entry.project_id, entry.task_id,
             entry.start_time, entry.end_time, entry.duration_minutes,
             entry.note, int(entry.invoiced), entry.id)
        )
        new_id = entry.id
    conn.commit()
    conn.close()
    return new_id


def delete_time_entry(entry_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM time_entries WHERE id=?", (entry_id,))
    conn.commit()
    conn.close()


def set_invoiced(entry_ids: List[int], invoiced: bool):
    conn = get_connection()
    placeholders = ",".join("?" * len(entry_ids))
    conn.execute(
        f"UPDATE time_entries SET invoiced=? WHERE id IN ({placeholders})",
        [int(invoiced)] + entry_ids
    )
    conn.commit()
    conn.close()
