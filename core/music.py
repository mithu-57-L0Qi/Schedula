"""
Music Library Engine
====================
Manages uploaded audio files and playlist metadata.
Files stored in data/music/{user_id}/
Metadata stored under data["music_library"] in user's data file.
"""

import uuid
from pathlib import Path
from datetime import datetime

from core import storage as _storage

MUSIC_BASE = Path(__file__).parent.parent / "data" / "music"
SUPPORTED_FORMATS = {".mp3", ".wav", ".aac", ".flac", ".m4a", ".ogg"}
SUPPORTED_MIME = {
    ".mp3": "audio/mpeg", ".wav": "audio/wav", ".aac": "audio/aac",
    ".flac": "audio/flac", ".m4a": "audio/mp4", ".ogg": "audio/ogg",
}

DEFAULT_PLAYLISTS = ["All Songs", "Favorites"]


# ─── Internal helpers ─────────────────────────────────────────────────────────

def _user_dir() -> Path:
    uid = _storage._get_current_user_id()
    d = MUSIC_BASE / uid
    d.mkdir(parents=True, exist_ok=True)
    return d


def _get_library() -> dict:
    data = _storage.load_data()
    lib = data.get("music_library", {})
    lib.setdefault("songs", [])
    lib.setdefault("playlists", list(DEFAULT_PLAYLISTS))
    return lib


def _save_library(lib: dict) -> bool:
    data = _storage.load_data()
    data["music_library"] = lib
    return _storage.save_data(data)


# ─── Songs ────────────────────────────────────────────────────────────────────

def add_song(
    file_bytes: bytes,
    original_filename: str,
    display_name: str = "",
    artist: str = "",
    playlist: str = "All Songs",
) -> tuple[dict | None, str]:
    suffix = Path(original_filename).suffix.lower()
    if suffix not in SUPPORTED_FORMATS:
        return None, f"Unsupported format. Supported: {', '.join(SUPPORTED_FORMATS)}"

    song_id = str(uuid.uuid4())[:10]
    filename = f"{song_id}{suffix}"
    dest = _user_dir() / filename

    try:
        dest.write_bytes(file_bytes)
    except OSError as e:
        return None, f"Failed to save file: {e}"

    lib = _get_library()
    if playlist not in lib["playlists"]:
        playlist = "All Songs"

    song = {
        "id": song_id,
        "filename": filename,
        "name": (display_name.strip() or Path(original_filename).stem).strip(),
        "artist": artist.strip(),
        "playlist": playlist,
        "favorite": False,
        "play_count": 0,
        "date_added": datetime.now().isoformat(),
        "last_played": "",
        "file_path": str(dest),
        "mime": SUPPORTED_MIME.get(suffix, "audio/mpeg"),
    }
    lib["songs"].append(song)
    _save_library(lib)
    return song, ""


def delete_song(song_id: str) -> bool:
    lib = _get_library()
    song = next((s for s in lib["songs"] if s["id"] == song_id), None)
    if not song:
        return False
    try:
        Path(song["file_path"]).unlink(missing_ok=True)
    except Exception:
        pass
    lib["songs"] = [s for s in lib["songs"] if s["id"] != song_id]
    return _save_library(lib)


def get_songs(playlist: str | None = None, search: str = "") -> list[dict]:
    songs = _get_library().get("songs", [])
    # Verify files still exist
    songs = [s for s in songs if Path(s.get("file_path", "")).exists()]
    if playlist and playlist != "All Songs":
        if playlist == "Favorites":
            songs = [s for s in songs if s.get("favorite")]
        else:
            songs = [s for s in songs if s.get("playlist") == playlist]
    if search:
        q = search.lower()
        songs = [s for s in songs if q in s.get("name","").lower() or q in s.get("artist","").lower()]
    return songs


def get_song(song_id: str) -> dict | None:
    for s in _get_library().get("songs", []):
        if s["id"] == song_id:
            return s
    return None


def read_song_bytes(song_id: str) -> tuple[bytes | None, str]:
    """Returns (file_bytes, mime_type) or (None, '')."""
    song = get_song(song_id)
    if not song:
        return None, ""
    try:
        return Path(song["file_path"]).read_bytes(), song.get("mime", "audio/mpeg")
    except Exception:
        return None, ""


def toggle_favorite(song_id: str) -> bool:
    lib = _get_library()
    for s in lib["songs"]:
        if s["id"] == song_id:
            s["favorite"] = not s.get("favorite", False)
            break
    return _save_library(lib)


def record_play(song_id: str) -> None:
    lib = _get_library()
    for s in lib["songs"]:
        if s["id"] == song_id:
            s["play_count"] = s.get("play_count", 0) + 1
            s["last_played"] = datetime.now().isoformat()
            break
    _save_library(lib)


def update_song(song_id: str, name: str = "", artist: str = "", playlist: str = "") -> bool:
    lib = _get_library()
    for s in lib["songs"]:
        if s["id"] == song_id:
            if name:
                s["name"] = name.strip()
            if artist:
                s["artist"] = artist.strip()
            if playlist and playlist in lib["playlists"]:
                s["playlist"] = playlist
            break
    return _save_library(lib)


# ─── Playlists ────────────────────────────────────────────────────────────────

def get_playlists() -> list[str]:
    return _get_library().get("playlists", list(DEFAULT_PLAYLISTS))


def add_playlist(name: str) -> tuple[bool, str]:
    name = name.strip()
    if not name:
        return False, "Name required."
    lib = _get_library()
    if name in lib["playlists"]:
        return False, "Playlist already exists."
    lib["playlists"].append(name)
    return _save_library(lib), ""


def delete_playlist(name: str) -> tuple[bool, str]:
    if name in DEFAULT_PLAYLISTS:
        return False, "Cannot delete built-in playlists."
    lib = _get_library()
    lib["playlists"] = [p for p in lib["playlists"] if p != name]
    for s in lib["songs"]:
        if s.get("playlist") == name:
            s["playlist"] = "All Songs"
    return _save_library(lib), ""


# ─── Stats ────────────────────────────────────────────────────────────────────

def get_library_stats() -> dict:
    songs = get_songs()
    return {
        "total": len(songs),
        "favorites": sum(1 for s in songs if s.get("favorite")),
        "most_played": sorted(songs, key=lambda s: s.get("play_count", 0), reverse=True)[:5],
        "recently_played": sorted(
            [s for s in songs if s.get("last_played")],
            key=lambda s: s.get("last_played", ""), reverse=True
        )[:5],
        "total_plays": sum(s.get("play_count", 0) for s in songs),
    }
