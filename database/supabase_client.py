import os
import streamlit as st
from supabase import create_client, Client


def get_supabase_client() -> Client:
    """Create and return a Supabase client.
    Preference order:
    1) Streamlit secrets (for Cloud or local secrets.toml)
    2) Environment variables (e.g., .env)
    Also attaches current auth session from st.session_state if present.
    """
    # Prefer secrets on Streamlit Cloud
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_ANON_KEY"]
    except Exception:
        # Fallback to environment variables (local dev)
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")

    if not url or not key:
        raise RuntimeError("Supabase configuration missing: SUPABASE_URL or SUPABASE_ANON_KEY.")

    client = create_client(url, key)

    # Attach session if available for RLS
    sess = st.session_state.get("session") if isinstance(st.session_state, dict) else None
    if sess:
        access_token = getattr(sess, "access_token", None) or (sess.get("access_token") if isinstance(sess, dict) else None)
        refresh_token = getattr(sess, "refresh_token", None) or (sess.get("refresh_token") if isinstance(sess, dict) else None)
        try:
            if access_token and refresh_token:
                client.auth.set_session(access_token, refresh_token)
        except Exception:
            pass

    return client 
