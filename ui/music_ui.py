"""
Music Library UI
================
Upload songs, manage playlists, play audio via st.audio().
st.audio() persists across Streamlit reruns (same bytes → same DOM element),
so music continues playing while using the Focus timer.
"""

import streamlit as st
from pathlib import Path

from core.music import (
    add_song, delete_song, get_songs, get_song, read_song_bytes,
    toggle_favorite, record_play, update_song,
    get_playlists, add_playlist, delete_playlist,
    get_library_stats,
)
from ui.components import section_header, divider, empty_state, metric_card


def render_music() -> None:
    section_header("Music Library", "Your personal focus soundtrack")

    stats = get_library_stats()
    cols = st.columns(4)
    with cols[0]:
        metric_card("Total Songs", stats["total"], color="#6366F1")
    with cols[1]:
        metric_card("Favorites", f"⭐ {stats['favorites']}", color="#F59E0B")
    with cols[2]:
        metric_card("Total Plays", stats["total_plays"], color="#10B981")
    with cols[3]:
        playlists = get_playlists()
        metric_card("Playlists", len(playlists), color="#8B5CF6")

    divider()

    tab_player, tab_library, tab_upload, tab_playlists = st.tabs([
        "▶ Now Playing", "🎵 Library", "⬆ Upload", "📂 Playlists"
    ])

    with tab_player:
        _render_player()

    with tab_library:
        _render_library()

    with tab_upload:
        _render_upload()

    with tab_playlists:
        _render_playlists()


# ─── Player ───────────────────────────────────────────────────────────────────

def _render_player() -> None:
    songs = get_songs()

    if not songs:
        empty_state("No songs yet. Upload some music to get started!", "🎵")
        return

    playlists = get_playlists()
    col_pl, col_search = st.columns([2, 3])
    with col_pl:
        playlist_sel = st.selectbox("Playlist", playlists, key="player_playlist")
    with col_search:
        search = st.text_input("Search", placeholder="🔍 Song or artist...", label_visibility="collapsed", key="player_search")

    filtered = get_songs(playlist_sel if playlist_sel != "All Songs" else None, search)

    if not filtered:
        empty_state("No songs match filters.", "🎵")
        return

    # Song selector
    song_names = [f"{'⭐ ' if s.get('favorite') else ''}{s.get('name','')} — {s.get('artist','Unknown')}" for s in filtered]
    sel_idx = st.session_state.get("music_sel_idx", 0)
    sel_idx = min(sel_idx, len(filtered) - 1)

    col_prev, col_sel, col_next = st.columns([1, 6, 1])
    with col_prev:
        if st.button("⏮", key="prev_song"):
            st.session_state["music_sel_idx"] = max(0, sel_idx - 1)
            st.rerun()
    with col_sel:
        new_idx = st.selectbox("Now playing", range(len(filtered)), index=sel_idx,
                               format_func=lambda i: song_names[i], label_visibility="collapsed",
                               key="music_player_sel")
        if new_idx != sel_idx:
            st.session_state["music_sel_idx"] = new_idx
            st.rerun()
    with col_next:
        if st.button("⏭", key="next_song"):
            st.session_state["music_sel_idx"] = min(len(filtered) - 1, sel_idx + 1)
            st.rerun()

    song = filtered[sel_idx]
    song_bytes, mime = read_song_bytes(song["id"])

    if song_bytes:
        # Render audio element — persists across reruns (same bytes = same hash = same DOM node)
        st.markdown(
            f'<div style="background:rgba(255,255,255,0.04);border-radius:14px;padding:20px 24px;'
            f'text-align:center;margin:12px 0">'
            f'<div style="font-size:1.2rem;font-weight:700;color:#E5E7EB;margin-bottom:4px">'
            f'{"⭐ " if song.get("favorite") else "🎵 "}{song.get("name","")}</div>'
            f'<div style="color:#6B7280;font-size:0.82rem">{song.get("artist","Unknown Artist")}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.audio(song_bytes, format=mime)

        col_fav, col_play_count = st.columns(2)
        with col_fav:
            fav_label = "⭐ Unfavorite" if song.get("favorite") else "☆ Add to Favorites"
            if st.button(fav_label, key=f"fav_{song['id']}", use_container_width=True):
                toggle_favorite(song["id"])
                st.rerun()
        with col_play_count:
            st.markdown(
                f'<div style="text-align:center;padding:8px;color:#6B7280;font-size:0.82rem">'
                f'▶ {song.get("play_count",0)} plays</div>',
                unsafe_allow_html=True,
            )

        if st.button("Record play", key=f"rec_{song['id']}", type="secondary", use_container_width=True):
            record_play(song["id"])
            st.session_state["music_sel_idx"] = min(len(filtered) - 1, sel_idx + 1)
            st.rerun()

        # Store for focus mode
        st.session_state["music_current_id"]    = song["id"]
        st.session_state["music_current_bytes"] = song_bytes
        st.session_state["music_current_mime"]  = mime
        st.session_state["music_current_name"]  = song.get("name", "")
    else:
        st.error("Could not load audio file. It may have been moved or deleted.")


# ─── Library ──────────────────────────────────────────────────────────────────

def _render_library() -> None:
    playlists = get_playlists()
    col_f1, col_f2 = st.columns([2, 3])
    with col_f1:
        pl = st.selectbox("Filter by playlist", playlists, key="lib_pl")
    with col_f2:
        search = st.text_input("Search", placeholder="🔍 Search songs...", label_visibility="collapsed", key="lib_search")

    songs = get_songs(pl if pl != "All Songs" else None, search)

    if not songs:
        empty_state("No songs found.", "🎵")
        return

    # Sort
    sort_by = st.radio("Sort by", ["Name", "Artist", "Plays", "Recently added"], horizontal=True, key="lib_sort")
    sort_map = {
        "Name":          lambda s: s.get("name","").lower(),
        "Artist":        lambda s: s.get("artist","").lower(),
        "Plays":         lambda s: -s.get("play_count", 0),
        "Recently added": lambda s: s.get("date_added",""),
    }
    songs = sorted(songs, key=sort_map.get(sort_by, sort_map["Name"]))

    for song in songs:
        col_icon, col_info, col_acts = st.columns([1, 8, 2])
        with col_icon:
            st.markdown(
                f'<div style="font-size:1.4rem;padding:6px 0">{"⭐" if song.get("favorite") else "🎵"}</div>',
                unsafe_allow_html=True,
            )
        with col_info:
            artist = song.get("artist","") or "Unknown Artist"
            playlist_tag = song.get("playlist","All Songs")
            added = song.get("date_added","")[:10]
            st.markdown(
                f'<div style="background:rgba(255,255,255,0.03);border-radius:8px;padding:8px 12px">'
                f'<div style="color:#E5E7EB;font-weight:600;font-size:0.9rem">{song.get("name","")}</div>'
                f'<div style="color:#6B7280;font-size:0.75rem">{artist} · {playlist_tag} · Added {added}'
                f' · ▶ {song.get("play_count",0)}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with col_acts:
            c1, c2 = st.columns(2)
            with c1:
                if st.button("⭐" if not song.get("favorite") else "✕❤", key=f"lib_fav_{song['id']}",
                             help="Toggle favorite"):
                    toggle_favorite(song["id"])
                    st.rerun()
            with c2:
                if st.button("🗑", key=f"lib_del_{song['id']}", help="Delete song"):
                    delete_song(song["id"])
                    st.rerun()


# ─── Upload ───────────────────────────────────────────────────────────────────

def _render_upload() -> None:
    st.markdown(
        '<div style="color:#6B7280;font-size:0.84rem;margin-bottom:12px">'
        'Supported formats: MP3, WAV, AAC, FLAC, M4A, OGG<br>'
        'Files are stored locally on this device.</div>',
        unsafe_allow_html=True,
    )

    playlists = get_playlists()
    uploaded = st.file_uploader(
        "Choose audio files",
        type=["mp3","wav","aac","flac","m4a","ogg"],
        accept_multiple_files=True,
        key="music_uploader",
    )

    if uploaded:
        col1, col2 = st.columns(2)
        with col1:
            display_name = st.text_input("Song name (optional)", placeholder="Auto-detected from filename")
        with col2:
            artist = st.text_input("Artist (optional)", placeholder="Artist name")
        playlist = st.selectbox("Add to playlist", playlists)

        if st.button("⬆ Upload Songs", type="primary", use_container_width=True):
            success_count = 0
            for f in uploaded:
                song, err = add_song(
                    file_bytes=f.read(),
                    original_filename=f.name,
                    display_name=display_name.strip() if len(uploaded) == 1 else "",
                    artist=artist.strip(),
                    playlist=playlist,
                )
                if err:
                    st.error(f"{f.name}: {err}")
                else:
                    success_count += 1
            if success_count:
                st.success(f"✓ Uploaded {success_count} song(s)!")
                st.rerun()

    divider()
    st.markdown(
        '<div style="color:#6B7280;font-size:0.82rem">'
        '💡 Tip: Open the Now Playing tab, select a song, then switch to Focus Mode — '
        'the audio player will stay active.</div>',
        unsafe_allow_html=True,
    )


# ─── Playlists ────────────────────────────────────────────────────────────────

def _render_playlists() -> None:
    playlists = get_playlists()

    for pl in playlists:
        is_builtin = pl in ("All Songs", "Favorites")
        count = len(get_songs(pl if pl != "All Songs" else None))
        col_name, col_count, col_del = st.columns([5, 2, 1])
        with col_name:
            st.markdown(
                f'<div style="background:rgba(255,255,255,0.04);border-radius:8px;'
                f'padding:10px 14px;color:#E5E7EB;font-weight:600">📂 {pl}</div>',
                unsafe_allow_html=True,
            )
        with col_count:
            st.markdown(
                f'<div style="padding:10px 0;color:#6B7280;font-size:0.84rem">{count} songs</div>',
                unsafe_allow_html=True,
            )
        with col_del:
            if not is_builtin:
                if st.button("✕", key=f"del_pl_{pl}"):
                    ok, err = delete_playlist(pl)
                    if ok:
                        st.rerun()
                    else:
                        st.error(err)

    divider()
    st.markdown("#### Create New Playlist")
    col_inp, col_btn = st.columns([4, 1])
    with col_inp:
        new_pl = st.text_input("Playlist name", placeholder="e.g. Deep Work, Chill...", label_visibility="collapsed", key="new_pl_input")
    with col_btn:
        if st.button("+ Create", key="create_pl_btn") and new_pl.strip():
            ok, err = add_playlist(new_pl.strip())
            if ok:
                st.rerun()
            else:
                st.error(err)


# ─── Compact player for Focus Mode ───────────────────────────────────────────

def render_focus_music_player() -> None:
    """Embedded compact player for use inside Focus Mode UI."""
    songs = get_songs()
    if not songs:
        st.markdown(
            '<div style="color:#4B5563;font-size:0.82rem;padding:8px 0">'
            'No songs in library. Upload music in the Music page.</div>',
            unsafe_allow_html=True,
        )
        return

    cur_id = st.session_state.get("music_current_id", songs[0]["id"])
    cur_song = get_song(cur_id) or songs[0]

    col_prev, col_song, col_next = st.columns([1, 6, 1])
    song_names = [s.get("name","") for s in songs]
    song_ids   = [s["id"] for s in songs]

    try:
        cur_idx = song_ids.index(cur_id)
    except ValueError:
        cur_idx = 0

    with col_prev:
        if st.button("⏮", key="fm_prev"):
            new_idx = max(0, cur_idx - 1)
            st.session_state["music_current_id"] = song_ids[new_idx]
            st.rerun()
    with col_song:
        sel = st.selectbox("Track", range(len(songs)), index=cur_idx,
                           format_func=lambda i: song_names[i],
                           label_visibility="collapsed", key="fm_track_sel")
        if sel != cur_idx:
            st.session_state["music_current_id"] = song_ids[sel]
            st.rerun()
    with col_next:
        if st.button("⏭", key="fm_next"):
            new_idx = min(len(songs) - 1, cur_idx + 1)
            st.session_state["music_current_id"] = song_ids[new_idx]
            st.rerun()

    song_bytes, mime = read_song_bytes(cur_song["id"])
    if song_bytes:
        st.audio(song_bytes, format=mime)
        st.session_state["music_current_bytes"] = song_bytes
        st.session_state["music_current_name"]  = cur_song.get("name","")
