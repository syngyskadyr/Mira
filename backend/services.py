"""Business logic and services using sqlite3 (no ORM).

All functions use `get_connection()` from `backend.database`.
"""

from __future__ import annotations

import os
import random
import string
from typing import Optional, Dict, List

from backend.database import get_connection


def _generate_referral_code(conn) -> str:
    """Generate a unique 6-char alphanumeric referral code."""
    for _ in range(100):
        code = "".join(random.choices(string.ascii_letters + string.digits, k=6))
        cur = conn.execute("SELECT 1 FROM users WHERE referral_code = ?", (code,))
        if cur.fetchone() is None:
            return code
    raise RuntimeError("Could not generate unique referral code")


def register_user(
    telegram_id: int, username: str, segment: str, referral_code: Optional[str] = None
) -> Dict:
    """Register a user or return existing user.

    If `referral_code` is provided and matches an existing user, record the
    referral and give the new user +30 XP.
    Returns a dict with keys: user_id, telegram_id, username, segment, xp, referral_code
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, telegram_id, username, segment, xp, referral_code FROM users WHERE telegram_id = ?",
            (telegram_id,),
        )
        row = cur.fetchone()
        if row:
            return {
                "user_id": row[0],
                "telegram_id": row[1],
                "username": row[2],
                "segment": row[3],
                "xp": row[4],
                "referral_code": row[5],
            }

        # New user
        code = _generate_referral_code(conn)
        xp = 0
        cur.execute(
            "INSERT INTO users (telegram_id, username, segment, xp, referral_code) VALUES (?, ?, ?, ?, ?)",
            (telegram_id, username, segment, xp, code),
        )
        user_id = cur.lastrowid

        # handle referral if provided
        if referral_code:
            cur.execute(
                "SELECT id FROM users WHERE referral_code = ?", (referral_code,)
            )
            ref = cur.fetchone()
            if ref:
                referrer_id = ref[0]
                # insert referral record
                cur.execute(
                    "INSERT INTO referrals (referrer_id, referred_id, xp_awarded) VALUES (?, ?, 0)",
                    (referrer_id, user_id),
                )
                # award 30 XP to new user
                cur.execute("UPDATE users SET xp = xp + 30 WHERE id = ?", (user_id,))
                cur.execute("SELECT xp FROM users WHERE id = ?", (user_id,))
                xp = cur.fetchone()[0]
        conn.commit()

        # fetch and return created user
        cur.execute(
            "SELECT id, telegram_id, username, segment, xp, referral_code FROM users WHERE id = ?",
            (user_id,),
        )
        row = cur.fetchone()
        return {
            "user_id": row[0],
            "telegram_id": row[1],
            "username": row[2],
            "segment": row[3],
            "xp": row[4],
            "referral_code": row[5],
        }
    finally:
        conn.close()


def get_next_task(user_id: int) -> Optional[Dict]:
    """Return the next task for the user's segment.

    Loops back to the first task when all tasks have been submitted.
    Returns dict: task_id, text, proof_type, xp_reward
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT segment FROM users WHERE id = ?", (user_id,))
        row = cur.fetchone()
        if not row:
            return None
        segment = row[0]

        cur.execute(
            "SELECT id, text, proof_type, xp_reward FROM tasks WHERE segment = ? ORDER BY id ASC",
            (segment,),
        )
        tasks = cur.fetchall()
        if not tasks:
            return None

        cur.execute("SELECT task_id FROM submissions WHERE user_id = ?", (user_id,))
        submitted = {r[0] for r in cur.fetchall()}

        for t in tasks:
            if t[0] not in submitted:
                return {
                    "task_id": t[0],
                    "text": t[1],
                    "proof_type": t[2],
                    "xp_reward": t[3],
                }

        # all done: return first task (loop)
        t = tasks[0]
        return {"task_id": t[0], "text": t[1], "proof_type": t[2], "xp_reward": t[3]}
    finally:
        conn.close()


def submit_proof(
    user_id: int, task_id: int, proof_type: str, proof_content: str
) -> Dict:
    """Validate proof, insert submission, award XP, handle referrals.

    Returns dict: approved(bool), reason(if not), xp_earned, total_xp, rank, referrer_telegram_id (or None)
    """
    # validate
    if proof_type == "screenshot":
        if not proof_content:
            return {"approved": False, "reason": "screenshot required"}
    elif proof_type == "text":
        if not proof_content or len(proof_content.strip()) <= 50:
            return {"approved": False, "reason": "text proof must be > 50 characters"}
    else:
        return {"approved": False, "reason": "unknown proof_type"}

    conn = get_connection()
    referrer_telegram_id = None
    xp_earned = 0
    try:
        cur = conn.cursor()
        # ensure task exists and get xp_reward
        cur.execute("SELECT xp_reward FROM tasks WHERE id = ?", (task_id,))
        t = cur.fetchone()
        if not t:
            return {"approved": False, "reason": "task not found"}
        xp_reward = t[0]

        # insert submission
        cur.execute(
            "INSERT INTO submissions (user_id, task_id, proof_type) VALUES (?, ?, ?)",
            (user_id, task_id, proof_type),
        )

        # add xp to user
        cur.execute("UPDATE users SET xp = xp + ? WHERE id = ?", (xp_reward, user_id))
        xp_earned = xp_reward

        # handle referrals: if user was referred and xp_awarded == 0 -> award referrer +50 and mark xp_awarded=1
        cur.execute(
            "SELECT id, referrer_id, xp_awarded FROM referrals WHERE referred_id = ?",
            (user_id,),
        )
        ref = cur.fetchone()
        if ref and ref[2] == 0:
            referral_id = ref[0]
            referrer_id = ref[1]
            cur.execute("UPDATE users SET xp = xp + 50 WHERE id = ?", (referrer_id,))
            cur.execute(
                "UPDATE referrals SET xp_awarded = 1 WHERE id = ?", (referral_id,)
            )
            # get referrer telegram id
            cur.execute("SELECT telegram_id FROM users WHERE id = ?", (referrer_id,))
            r = cur.fetchone()
            if r:
                referrer_telegram_id = r[0]

        conn.commit()

        # compute total xp and rank
        cur.execute("SELECT xp FROM users WHERE id = ?", (user_id,))
        total_xp = cur.fetchone()[0]
        cur.execute("SELECT COUNT(1) FROM users WHERE xp > ?", (total_xp,))
        higher = cur.fetchone()[0]
        rank = higher + 1

        return {
            "approved": True,
            "xp_earned": xp_earned,
            "total_xp": total_xp,
            "rank": rank,
            "referrer_telegram_id": referrer_telegram_id,
        }
    finally:
        conn.close()


def get_leaderboard() -> List[Dict]:
    """Return top 10 users ordered by xp desc as list of dicts with rank."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT username, segment, xp FROM users ORDER BY xp DESC LIMIT 10")
        rows = cur.fetchall()
        result = []
        for idx, r in enumerate(rows, start=1):
            result.append({"rank": idx, "username": r[0], "segment": r[1], "xp": r[2]})
        return result
    finally:
        conn.close()


def get_user_profile(telegram_id: int) -> Optional[Dict]:
    """Return user profile with rank, tasks completed and referral counts."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, username, segment, xp, referral_code FROM users WHERE telegram_id = ?",
            (telegram_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        user_id, username, segment, xp, referral_code = row

        cur.execute("SELECT COUNT(1) FROM submissions WHERE user_id = ?", (user_id,))
        tasks_completed = cur.fetchone()[0]

        cur.execute("SELECT COUNT(1) FROM referrals WHERE referrer_id = ?", (user_id,))
        referred_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(1) FROM users WHERE xp > ?", (xp,))
        higher = cur.fetchone()[0]
        rank = higher + 1

        return {
            "username": username,
            "segment": segment,
            "xp": xp,
            "rank": rank,
            "tasks_completed": tasks_completed,
            "referral_code": referral_code,
            "referred_count": referred_count,
        }
    finally:
        conn.close()


def get_referral_link(telegram_id: int) -> Optional[str]:
    """Return referral link using BOT_USERNAME from .env and user's referral_code."""
    # read BOT_USERNAME from .env in project root
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
    bot_username = None
    try:
        with open(env_path, "r", encoding="utf8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("BOT_USERNAME="):
                    bot_username = line.split("=", 1)[1].strip()
                    break
    except Exception:
        bot_username = None

    if not bot_username:
        return None

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT referral_code FROM users WHERE telegram_id = ?", (telegram_id,)
        )
        row = cur.fetchone()
        if not row or not row[0]:
            return None
        code = row[0]
        return f"https://t.me/{bot_username}?start={code}"
    finally:
        conn.close()


__all__ = [
    "register_user",
    "get_next_task",
    "submit_proof",
    "get_leaderboard",
    "get_user_profile",
    "get_referral_link",
]
