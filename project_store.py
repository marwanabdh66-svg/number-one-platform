"""Small, testable SQLite helpers for NUMBER ONE saved projects."""
from datetime import datetime


def initialize_projects_table(connection):
    """Create the saved-projects table and its user lookup index if absent."""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            title TEXT NOT NULL,
            template_id TEXT,
            prompt TEXT NOT NULL,
            created TEXT NOT NULL
        )
        """
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_projects_username_id "
        "ON projects(username, id DESC)"
    )
    connection.commit()


def save_project(connection, username, title, prompt, template_id=None, created=None):
    """Save one advertising brief and return its database id."""
    safe_username = str(username or "").strip()
    safe_title = str(title or "").strip()
    safe_prompt = str(prompt or "").strip()

    if not safe_username:
        raise ValueError("A signed-in username is required.")
    if not safe_title or not safe_prompt:
        raise ValueError("Project title and prompt are required.")

    cursor = connection.execute(
        """
        INSERT INTO projects (username, title, template_id, prompt, created)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            safe_username,
            safe_title,
            str(template_id).strip() if template_id else None,
            safe_prompt,
            created or datetime.now().strftime("%Y-%m-%d %H:%M"),
        ),
    )
    connection.commit()
    return cursor.lastrowid


def list_projects(connection, username):
    """Return only the saved projects owned by the requested username."""
    safe_username = str(username or "").strip()
    if not safe_username:
        return []

    return connection.execute(
        """
        SELECT id, title, template_id, prompt, created
        FROM projects
        WHERE username = ?
        ORDER BY id DESC
        """,
        (safe_username,),
    ).fetchall()
