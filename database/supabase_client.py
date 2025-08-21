import os
import streamlit as st
from supabase import create_client, Client


def get_supabase_client() -> Client:
    """Create and return a Supabase client.
    Preference order:
    1) Environment variables (e.g., .env)
    2) Streamlit secrets (for Cloud or local secrets.toml)
    This avoids accessing st.secrets when not configured.
    Also attaches current auth session from st.session_state if present.
    """
    # Debug: Print current working directory and env vars
    print(f"Current working directory: {os.getcwd()}")
    print(f"SUPABASE_URL from env: {os.getenv('SUPABASE_URL')}")
    print(f"SUPABASE_ANON_KEY from env: {os.getenv('SUPABASE_ANON_KEY')[:20] if os.getenv('SUPABASE_ANON_KEY') else 'None'}")
    
    # Prefer environment variables first
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")

    # Fallback to Streamlit secrets if env not provided
    if not url or not key:
        try:
            if not url:
                url = st.secrets["SUPABASE_URL"]
                print(f"SUPABASE_URL from secrets: {url}")
            if not key:
                key = st.secrets["SUPABASE_ANON_KEY"]
                print(f"SUPABASE_ANON_KEY from secrets: {key[:20] if key else 'None'}")
        except Exception as e:
            print(f"Error reading from secrets: {e}")
            pass

    if not url or not key:
        print(f"Final check - URL: {url}, KEY: {key[:20] if key else 'None'}")
        raise RuntimeError("Supabase configuration missing: SUPABASE_URL or SUPABASE_ANON_KEY.")

    client = create_client(url, key)

    # Attach session if available for RLS
    sess = st.session_state.get("session") if isinstance(st.session_state, dict) else None
    if sess:
        access_token = getattr(sess, "access_token", None) or sess.get("access_token") if isinstance(sess, dict) else None
        refresh_token = getattr(sess, "refresh_token", None) or sess.get("refresh_token") if isinstance(sess, dict) else None
        try:
            if access_token and refresh_token:
                client.auth.set_session(access_token, refresh_token)
        except Exception:
            pass

    return client 
