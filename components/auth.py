import streamlit as st
from database.supabase_client import get_supabase_client


def render_auth() -> bool:
    """Render login/signup UI. Returns True if user is authenticated."""
    sb = get_supabase_client()

    if "user" in st.session_state and st.session_state.get("session"):
        # Already logged in
        with st.sidebar:
            # Get user's name from metadata or use email as fallback
            user = st.session_state['user']
            user_data = getattr(user, 'user_metadata', {}) or {}
            first_name = user_data.get('first_name', '')
            last_name = user_data.get('last_name', '')

            if first_name and last_name:
                display_name = f"{first_name} {last_name}"
            elif first_name:
                display_name = first_name
            else:
                display_name = user.email.split('@')[0]  # Use part before @ as fallback

            st.success(f"👋 {display_name}")
            if st.button("Çıkış Yap", use_container_width=True):
                try:
                    sb.auth.sign_out()
                finally:
                    for k in ("user", "session"):
                        st.session_state.pop(k, None)
                    st.rerun()
        return True

    # Updated CSS to fix the logo alignment
    st.markdown("""
    <style>
    .auth-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        min-height: 80vh;
        padding: 20px;
    }
    .auth-form {
        flex: 1;
        max-width: 400px;
        padding: 40px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 20px;
        backdrop-filter: blur(10px);
        border: none;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    .auth-logo {
        flex: 1;
        display: flex;
        justify-content: center;
        align-items: center; /* Logonun dikeyde ortalanması için değiştirildi */
        padding: 20px;
        width: 100%;
        /* Yüksekliği sabitleyen satırlar kaldırıldı */
    }
    .auth-logo img {
        width: 400px !important;
        height: auto !important;
        max-width: 400px !important;
        max-height: 400px !important;
        object-fit: contain !important;
    }
    .auth-title {
        text-align: center;
        margin-bottom: 30px;
        color: #3b82f6;
        font-size: 28px;
        font-weight: bold;
    }
    .form-group {
        margin-bottom: 20px;
    }
    .form-group label {
        display: block;
        margin-bottom: 8px;
        color: #e5e7eb;
        font-weight: 600;
    }
    .form-group input {
        width: 100%;
        padding: 12px 16px;
        border: 2px solid rgba(59, 130, 246, 0.3);
        border-radius: 10px;
        background: rgba(255, 255, 255, 0.05);
        color: #ffffff;
        font-size: 16px;
        transition: all 0.3s ease;
    }
    .form-group input:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        outline: none;
    }
    .auth-button {
        width: 100%;
        padding: 14px;
        background: linear-gradient(135deg, #3b82f6, #1d4ed8);
        border: none;
        border-radius: 10px;
        color: white;
        font-size: 16px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        margin-top: 10px;
    }
    .auth-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4);
    }
    .auth-tabs {
        display: flex;
        margin-bottom: 30px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 4px;
    }
    .auth-tab {
        flex: 1;
        padding: 12px 20px;
        text-align: center;
        cursor: pointer;
        border-radius: 8px;
        transition: all 0.3s ease;
        color: #9ca3af;
    }
    .auth-tab.active {
        background: #3b82f6;
        color: white;
    }
    .password-rules {
        background: rgba(59, 130, 246, 0.1);
        border-radius: 10px;
        padding: 15px;
        margin: 20px 0;
        border-left: 4px solid #3b82f6;
    }
    .password-rules h4 {
        color: #3b82f6;
        margin-bottom: 10px;
        font-size: 16px;
    }
    .password-rules ul {
        margin: 0;
        padding-left: 20px;
        color: #e5e7eb;
    }
    .password-rules li {
        margin: 5px 0;
    }
    </style>
    """, unsafe_allow_html=True)

    # Ana container
    col1, col2 = st.columns([1, 1])

    with col1:
        # Sol taraf - Logo
        st.markdown('<div class="auth-logo">', unsafe_allow_html=True)
        st.image("images/logo.png", width=400)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        # Sağ taraf - Login formu
        # Tabs
        tab1, tab2 = st.tabs(["🔐 Giriş", "📝 Kayıt"])

        with tab1:
            st.markdown('<div class="auth-title">Hoş Geldiniz</div>', unsafe_allow_html=True)

            with st.form("login_form", clear_on_submit=False):
                email = st.text_input("E-posta", key="login_email")
                password = st.text_input("Şifre", type="password", key="login_password")

                if st.form_submit_button("Giriş Yap", use_container_width=True):
                    try:
                        resp = sb.auth.sign_in_with_password({"email": email, "password": password})
                        if resp.user:
                            st.session_state["user"] = resp.user
                            st.session_state["session"] = resp.session
                            st.success("Giriş başarılı")
                            st.rerun()
                        else:
                            st.error("E-posta veya şifre hatalı. Lütfen kontrol edin.")
                    except Exception as e:
                        st.error("E-posta veya şifre hatalı. Lütfen kontrol edin.")

        with tab2:
            st.markdown('<div class="auth-title">Hesap Oluştur</div>', unsafe_allow_html=True)

            with st.form("signup_form", clear_on_submit=False):
                s_email = st.text_input("E-posta", key="signup_email")
                s_password = st.text_input("Şifre", type="password", key="signup_password")

                # Şifre kuralları
                st.markdown("""
                <div class="password-rules">
                    <h4>🔐 Şifre Kuralları</h4>
                    <ul>
                        <li>✅ <strong>Minimum uzunluk:</strong> 6 karakter</li>
                        <li>✅ <strong>Büyük harf:</strong> Gerekli (A-Z)</li>
                        <li>✅ <strong>Küçük harf:</strong> Gerekli (a-z)</li>
                        <li>✅ <strong>Rakam:</strong> Gerekli (0-9)</li>
                        <li>✅ <strong>Özel karakter:</strong> Gerekli (!@#$%^&*)</li>
                    </ul>
                    <p style="margin-top: 10px; color: #3b82f6;"><strong>💡 Örnek:</strong> Test123!</p>
                </div>
                """, unsafe_allow_html=True)

                first = st.text_input("Ad")
                last = st.text_input("Soyad")

                if st.form_submit_button("Kayıt Ol", use_container_width=True):
                    try:
                        resp = sb.auth.sign_up({
                            "email": s_email,
                            "password": s_password,
                            "options": {"data": {"first_name": first, "last_name": last}},
                        })
                        # Eğer email doğrulama kapalıysa session döner, otomatik giriş yapalım
                        if getattr(resp, "session", None) and resp.session:
                            st.session_state["user"] = resp.user
                            st.session_state["session"] = resp.session
                            st.success("Kayıt başarılı, otomatik giriş yapıldı")
                            st.rerun()
                        else:
                            st.success("Kayıt oluşturuldu. Lütfen e-posta doğrulamasını tamamlayın.")
                    except Exception as e:
                        st.error("Kayıt sırasında bir hata oluştu. Lütfen bilgileri kontrol edin.")

    return False