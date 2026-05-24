"""Static task definitions and seeding helper.

This module defines a hardcoded `TASKS` list (3 tasks per segment)
and provides `seed_tasks()` which inserts them into the `tasks` table
if that table is currently empty.
"""

from typing import List, Dict

TASKS: List[Dict] = [
    # student segment (3 tasks)
    {
        "segment": "student",
        "text": "Open Mira (https://t.me/mira) and create a study board for your current course.",
        "proof_type": "screenshot",
        "xp_reward": 40,
    },
    {
        "segment": "student",
        "text": "Open Mira (https://t.me/mira) and add three study notes about today's lesson.",
        "proof_type": "text",
        "xp_reward": 50,
    },
    {
        "segment": "student",
        "text": "Open Mira (https://t.me/mira) and invite a classmate to collaborate on a board.",
        "proof_type": "screenshot",
        "xp_reward": 60,
    },
    # marketer segment (3 tasks)
    {
        "segment": "marketer",
        "text": "Open Mira (https://t.me/mira) and sketch a marketing funnel for a product launch.",
        "proof_type": "text",
        "xp_reward": 40,
    },
    {
        "segment": "marketer",
        "text": "Open Mira (https://t.me/mira) and create three copy variations for an ad campaign.",
        "proof_type": "screenshot",
        "xp_reward": 50,
    },
    {
        "segment": "marketer",
        "text": "Open Mira (https://t.me/mira) and map a customer persona with key pain points.",
        "proof_type": "text",
        "xp_reward": 60,
    },
    # founder segment (3 tasks)
    {
        "segment": "founder",
        "text": "Open Mira (https://t.me/mira) and draft a one-page roadmap for the next quarter.",
        "proof_type": "screenshot",
        "xp_reward": 40,
    },
    {
        "segment": "founder",
        "text": "Open Mira (https://t.me/mira) and outline the top three risks for your startup.",
        "proof_type": "text",
        "xp_reward": 50,
    },
    {
        "segment": "founder",
        "text": "Open Mira (https://t.me/mira) and build a simple investor pitch storyboard.",
        "proof_type": "screenshot",
        "xp_reward": 60,
    },
]


def seed_tasks() -> None:
    """Insert TASKS into the database if the `tasks` table is empty.

    Uses `get_connection` from `backend.database` to perform the check and
    insertion. If the table already contains rows, this function does nothing.
    """
    try:
        from backend.database import get_connection
    except Exception:
        # defensive: if the import fails, do nothing
        return

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(1) FROM tasks")
        row = cur.fetchone()
        count = row[0] if row else 0
        if count == 0:
            insert_sql = "INSERT INTO tasks (segment, text, proof_type, xp_reward) VALUES (?, ?, ?, ?)"
            entries = [
                (t["segment"], t["text"], t["proof_type"], t["xp_reward"])
                for t in TASKS
            ]
            cur.executemany(insert_sql, entries)
            conn.commit()
    finally:
        conn.close()


__all__ = ["TASKS", "seed_tasks"]
