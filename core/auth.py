"""
Authentication Engine
=====================
Local user accounts with HMAC-SHA256 salted passwords.
Accounts stored in data/users.json.
Schedula works fine without login (guest mode).
"""

import hashlib
import hmac
import os
import json
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).parent.parent / "data"
USERS_FILE = DATA_DIR / "users.json"

GUEST_USER: dict = {
    "id": "guest",
    "username": "guest",
    "display_name": "Guest",
    "email": "",
    "created_at": "",
    "last_login": "",
    "theme": "dark",
}


# ─── Internal helpers ─────────────────────────────────────────────────────────

def _load_users() -> dict:
    if not USERS_FILE.exists():
        return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_users(users: dict) -> bool:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        tmp = USERS_FILE.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
        tmp.replace(USERS_FILE)
        return True
    except Exception:
        return False


def _hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    if salt is None:
        salt = os.urandom(16).hex()
    h = hmac.new(salt.encode(), password.encode(), hashlib.sha256).hexdigest()
    return h, salt


def _public_user(user: dict) -> dict:
    return {k: v for k, v in user.items() if k not in ("password_hash", "salt")}


# ─── Public API ───────────────────────────────────────────────────────────────

def create_user(username: str, password: str, display_name: str = "", email: str = "") -> tuple[dict | None, str]:
    username = username.strip().lower()
    if len(username) < 3:
        return None, "Username must be at least 3 characters."
    if not all(c.isalnum() or c == "_" for c in username):
        return None, "Username: letters, numbers, underscores only."
    if len(password) < 6:
        return None, "Password must be at least 6 characters."

    users = _load_users()
    if username in users:
        return None, "Username already taken."

    password_hash, salt = _hash_password(password)
    user = {
        "id": username,
        "username": username,
        "display_name": display_name.strip() or username.title(),
        "email": email.strip(),
        "password_hash": password_hash,
        "salt": salt,
        "created_at": datetime.now().isoformat(),
        "last_login": datetime.now().isoformat(),
        "theme": "dark",
    }
    users[username] = user
    _save_users(users)
    return _public_user(user), ""


def login(username: str, password: str) -> tuple[dict | None, str]:
    username = username.strip().lower()
    users = _load_users()
    user = users.get(username)
    if not user:
        return None, "Invalid username or password."

    expected, _ = _hash_password(password, user.get("salt", ""))
    if expected != user.get("password_hash", ""):
        return None, "Invalid username or password."

    user["last_login"] = datetime.now().isoformat()
    users[username] = user
    _save_users(users)
    return _public_user(user), ""


def get_user(username: str) -> dict | None:
    u = _load_users().get(username.strip().lower())
    return _public_user(u) if u else None


def update_display_name(username: str, new_name: str) -> bool:
    users = _load_users()
    u = users.get(username.lower())
    if not u:
        return False
    u["display_name"] = new_name.strip()
    users[username.lower()] = u
    return _save_users(users)


def change_password(username: str, old_pw: str, new_pw: str) -> tuple[bool, str]:
    if len(new_pw) < 6:
        return False, "New password must be at least 6 characters."
    users = _load_users()
    u = users.get(username.lower())
    if not u:
        return False, "User not found."
    expected, _ = _hash_password(old_pw, u.get("salt", ""))
    if expected != u.get("password_hash", ""):
        return False, "Current password is incorrect."
    new_hash, new_salt = _hash_password(new_pw)
    u["password_hash"] = new_hash
    u["salt"] = new_salt
    users[username.lower()] = u
    return _save_users(users), ""


def has_any_users() -> bool:
    return bool(_load_users())
