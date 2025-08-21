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
    url = None
    key = None
    
    # Try Streamlit secrets first (for Cloud deployment)
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_ANON_KEY"]
        st.write(f"✅ Secrets loaded from st.secrets - URL: {url[:30]}..., KEY: {key[:20]}...")
    except Exception as e:
        st.write(f"❌ Failed to load from st.secrets: {str(e)}")
        
        # Fallback to environment variables
        try:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_ANON_KEY")
            st.write(f"✅ Environment variables loaded - URL: {url[:30] if url else 'None'}..., KEY: {key[:20] if key else 'None'}...")
        except Exception as e2:
            st.write(f"❌ Failed to load from environment: {str(e2)}")

    if not url or not key:
        st.error(f"❌ Configuration missing - URL: {'Present' if url else 'Missing'}, KEY: {'Present' if key else 'Missing'}")
        st.write("Available st.secrets keys:", list(st.secrets.keys()) if hasattr(st, 'secrets') else "No secrets available")
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
