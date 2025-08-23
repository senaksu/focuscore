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
    
    try:
        client = create_client(url, key)
        
        # Attach session if available for RLS
        session = st.session_state.get("session")
        if session:
            try:
                # Handle different session types
                if hasattr(session, 'access_token') and hasattr(session, 'refresh_token'):
                    # Session object with attributes
                    access_token = session.access_token
                    refresh_token = session.refresh_token
                elif isinstance(session, dict):
                    # Session dict
                    access_token = session.get("access_token")
                    refresh_token = session.get("refresh_token")
                else:
                    access_token = None
                    refresh_token = None
                
                if access_token and refresh_token:
                    client.auth.set_session(access_token, refresh_token)
            except Exception:
                pass

        return client
        
    except Exception as e:
        raise RuntimeError(f"Failed to create Supabase client: {e}")
