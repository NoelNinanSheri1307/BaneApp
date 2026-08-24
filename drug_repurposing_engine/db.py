"""
SQLite Database Layer for BioConnect Research Engine
Manages users, authentication sessions, search history, saved research, projects, notes, and hypotheses.
"""

import sqlite3
import os
import hashlib
import secrets
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "research_database.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they do not exist."""
    conn = get_db()
    cursor = conn.cursor()

    # Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        name TEXT,
        created_at TEXT NOT NULL
    )
    """)

    # User Sessions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_sessions (
        token TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # Search History Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS search_history (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        query TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # Saved Research Items Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS saved_items (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        entity_type TEXT NOT NULL,
        entity_id TEXT NOT NULL,
        title TEXT,
        subtitle TEXT,
        metadata_json TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # Projects Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        status TEXT NOT NULL DEFAULT 'active',
        drug_id TEXT,
        disease_id TEXT,
        query TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # Project Notes Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS project_notes (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # Project Hypotheses Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS project_hypotheses (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        title TEXT NOT NULL,
        statement TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'draft',
        created_at TEXT NOT NULL,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    conn.commit()
    conn.close()


def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()


# ─── Auth Operations ───────────────────────────────────────────────────────────

def register_user(email: str, password: str, name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    email_clean = email.strip().lower()
    password_clean = password.strip()

    cursor.execute("SELECT id FROM users WHERE email = ?", (email_clean,))
    if cursor.fetchone():
        conn.close()
        return None  # Already exists

    user_id = f"usr_{secrets.token_hex(8)}"
    salt = secrets.token_hex(16)
    pw_hash = _hash_password(password_clean, salt)
    now = datetime.utcnow().isoformat()
    disp_name = (name or "").strip() or email_clean.split('@')[0].capitalize()

    cursor.execute(
        "INSERT INTO users (id, email, password_hash, salt, name, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, email_clean, pw_hash, salt, disp_name, now)
    )

    token = create_session(cursor, user_id)
    conn.commit()
    conn.close()

    return {
        "id": user_id,
        "email": email_clean,
        "name": disp_name,
        "token": token,
        "createdAt": now
    }


def login_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    email_clean = email.strip().lower()
    password_clean = password.strip()

    cursor.execute("SELECT id, email, password_hash, salt, name, created_at FROM users WHERE email = ?", (email_clean,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    salt = row["salt"]
    expected_hash = row["password_hash"]
    if _hash_password(password_clean, salt) != expected_hash:
        conn.close()
        return None

    user_id = row["id"]
    token = create_session(cursor, user_id)
    conn.commit()
    conn.close()

    return {
        "id": user_id,
        "email": row["email"],
        "name": row["name"],
        "token": token,
        "createdAt": row["created_at"]
    }


def create_session(cursor, user_id: str) -> str:
    token = secrets.token_hex(32)
    expires_at = (datetime.utcnow() + timedelta(days=30)).isoformat()
    cursor.execute(
        "INSERT INTO user_sessions (token, user_id, expires_at) VALUES (?, ?, ?)",
        (token, user_id, expires_at)
    )
    return token


def get_user_by_token(token: str) -> Optional[Dict[str, Any]]:
    if not token:
        return None
    conn = get_db()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    cursor.execute("""
        SELECT u.id, u.email, u.name, u.created_at
        FROM users u
        JOIN user_sessions s ON u.id = s.user_id
        WHERE s.token = ? AND s.expires_at > ?
    """, (token, now))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"id": row["id"], "email": row["email"], "name": row["name"], "createdAt": row["created_at"]}
    return None


def delete_session(token: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_sessions WHERE token = ?", (token,))
    conn.commit()
    conn.close()


# ─── Search History Operations ─────────────────────────────────────────────────

def record_search(user_id: str, query: str):
    conn = get_db()
    cursor = conn.cursor()
    query_clean = query.strip()
    # Delete existing duplicate to avoid clutter
    cursor.execute("DELETE FROM search_history WHERE user_id = ? AND LOWER(query) = LOWER(?)", (user_id, query_clean))
    sh_id = f"sh_{secrets.token_hex(8)}"
    now = datetime.utcnow().isoformat()
    cursor.execute(
        "INSERT INTO search_history (id, user_id, query, created_at) VALUES (?, ?, ?, ?)",
        (sh_id, user_id, query_clean, now)
    )
    conn.commit()
    conn.close()


def get_search_history(user_id: str, limit: int = 10) -> List[str]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT query FROM search_history WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit)
    )
    rows = cursor.fetchall()
    conn.close()
    return [r["query"] for r in rows]


def delete_search_history_item(user_id: str, query: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM search_history WHERE user_id = ? AND LOWER(query) = LOWER(?)",
        (user_id, query.strip())
    )
    conn.commit()
    conn.close()


def clear_user_search_history(user_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM search_history WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


# ─── Saved Items Operations ────────────────────────────────────────────────────

def get_saved_items(user_id: str) -> List[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, entity_type, entity_id, title, subtitle, metadata_json, created_at FROM saved_items WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    items = []
    for r in rows:
        meta = json.loads(r["metadata_json"]) if r["metadata_json"] else {}
        items.append({
            "id": r["id"],
            "entityType": r["entity_type"],
            "entityId": r["entity_id"],
            "title": r["title"] or r["entity_id"],
            "subtitle": r["subtitle"],
            "metadata": meta,
            "createdAt": r["created_at"]
        })
    return items


def add_saved_item(user_id: str, entity_type: str, entity_id: str, title: Optional[str] = None, subtitle: Optional[str] = None, metadata: Optional[Dict] = None) -> Dict[str, Any]:
    conn = get_db()
    cursor = conn.cursor()
    # Avoid duplicate
    cursor.execute(
        "SELECT id FROM saved_items WHERE user_id = ? AND entity_type = ? AND entity_id = ?",
        (user_id, entity_type, entity_id)
    )
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return {"id": existing["id"], "entityType": entity_type, "entityId": entity_id, "title": title, "subtitle": subtitle, "createdAt": datetime.utcnow().isoformat()}

    item_id = f"sav_{secrets.token_hex(8)}"
    now = datetime.utcnow().isoformat()
    meta_str = json.dumps(metadata) if metadata else None

    cursor.execute(
        "INSERT INTO saved_items (id, user_id, entity_type, entity_id, title, subtitle, metadata_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (item_id, user_id, entity_type, entity_id, title or entity_id, subtitle, meta_str, now)
    )
    conn.commit()
    conn.close()

    return {
        "id": item_id,
        "entityType": entity_type,
        "entityId": entity_id,
        "title": title or entity_id,
        "subtitle": subtitle,
        "metadata": metadata or {},
        "createdAt": now
    }


def remove_saved_item(user_id: str, item_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM saved_items WHERE user_id = ? AND (id = ? OR entity_id = ?)", (user_id, item_id, item_id))
    conn.commit()
    conn.close()


# ─── Projects Operations ───────────────────────────────────────────────────────

def get_user_projects(user_id: str) -> List[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, title, description, status, drug_id, disease_id, query, created_at, updated_at FROM projects WHERE user_id = ? ORDER BY updated_at DESC",
        (user_id,)
    )
    rows = cursor.fetchall()
    projects = []
    for r in rows:
        p_id = r["id"]
        # Fetch note IDs and hypothesis IDs
        cursor.execute("SELECT id FROM project_notes WHERE project_id = ? ORDER BY created_at ASC", (p_id,))
        note_ids = [n["id"] for n in cursor.fetchall()]

        cursor.execute("SELECT id FROM project_hypotheses WHERE project_id = ? ORDER BY created_at ASC", (p_id,))
        hyp_ids = [h["id"] for h in cursor.fetchall()]

        projects.append({
            "id": p_id,
            "title": r["title"],
            "description": r["description"],
            "status": r["status"],
            "drugId": r["drug_id"],
            "diseaseId": r["disease_id"],
            "query": r["query"],
            "signalIds": [f"{r['drug_id']}_{r['disease_id']}".lower()] if r["drug_id"] and r["disease_id"] else [],
            "noteIds": note_ids,
            "hypothesisIds": hyp_ids,
            "createdAt": r["created_at"],
            "updatedAt": r["updated_at"]
        })
    conn.close()
    return projects


def create_user_project(user_id: str, title: str, description: Optional[str] = None, drug_id: Optional[str] = None, disease_id: Optional[str] = None, query: Optional[str] = None) -> Dict[str, Any]:
    conn = get_db()
    cursor = conn.cursor()
    p_id = f"proj_{secrets.token_hex(6)}"
    now = datetime.utcnow().isoformat()
    cursor.execute(
        "INSERT INTO projects (id, user_id, title, description, status, drug_id, disease_id, query, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (p_id, user_id, title.strip(), description, "active", drug_id, disease_id, query, now, now)
    )
    conn.commit()
    conn.close()
    return {
        "id": p_id,
        "title": title.strip(),
        "description": description,
        "status": "active",
        "drugId": drug_id,
        "diseaseId": disease_id,
        "query": query,
        "signalIds": [f"{drug_id}_{disease_id}".lower()] if drug_id and disease_id else [],
        "noteIds": [],
        "hypothesisIds": [],
        "createdAt": now,
        "updatedAt": now
    }


def delete_user_project(user_id: str, project_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM project_hypotheses WHERE project_id = ?", (project_id,))
    cursor.execute("DELETE FROM project_notes WHERE project_id = ?", (project_id,))
    cursor.execute("DELETE FROM projects WHERE user_id = ? AND id = ?", (user_id, project_id))
    conn.commit()
    conn.close()


def add_project_note(user_id: str, project_id: str, content: str) -> Dict[str, Any]:
    conn = get_db()
    cursor = conn.cursor()
    note_id = f"note_{secrets.token_hex(6)}"
    now = datetime.utcnow().isoformat()
    cursor.execute(
        "INSERT INTO project_notes (id, project_id, user_id, content, created_at) VALUES (?, ?, ?, ?, ?)",
        (note_id, project_id, user_id, content.strip(), now)
    )
    cursor.execute("UPDATE projects SET updated_at = ? WHERE id = ?", (now, project_id))
    conn.commit()
    conn.close()
    return {
        "id": note_id,
        "projectId": project_id,
        "content": content.strip(),
        "createdAt": now,
        "updatedAt": now
    }


def add_project_hypothesis(user_id: str, project_id: str, title: str, statement: str) -> Dict[str, Any]:
    conn = get_db()
    cursor = conn.cursor()
    hyp_id = f"hyp_{secrets.token_hex(6)}"
    now = datetime.utcnow().isoformat()
    cursor.execute(
        "INSERT INTO project_hypotheses (id, project_id, user_id, title, statement, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (hyp_id, project_id, user_id, title.strip(), statement.strip(), "draft", now)
    )
    cursor.execute("UPDATE projects SET updated_at = ? WHERE id = ?", (now, project_id))
    conn.commit()
    conn.close()
    return {
        "id": hyp_id,
        "projectId": project_id,
        "title": title.strip(),
        "statement": statement.strip(),
        "status": "draft",
        "createdAt": now,
        "updatedAt": now
    }


# Initialize DB on module import
init_db()
