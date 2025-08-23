import streamlit as st
import asyncio
from datetime import datetime
import uuid
import re
from ai_coach.agent import FocusCoachAgent
from database.database import get_chat_messages

class ChatInterface:
    def __init__(self, ai_coach: FocusCoachAgent):
        self.ai_coach = ai_coach
        self._init_session_state()
    
    def _init_session_state(self):
        """Initialize session state for chat"""
        if 'chat_session_id' not in st.session_state:
            st.session_state.chat_session_id = str(uuid.uuid4())
        
        if 'chat_messages' not in st.session_state:
            st.session_state.chat_messages = []
        
        if 'chat_input' not in st.session_state:
            st.session_state.chat_input = ""
    
    def render(self):
        """Render chat interface"""
        st.markdown("<h1 style='color: white;'>🤖 FocusCore AI Koç Asistan</h1>", unsafe_allow_html=True)
        
        # Add custom CSS for better performance report formatting
        st.markdown("""
        <style>
        .performance-report {
            background: rgba(59, 130, 246, 0.05);
            border-radius: 15px;
            padding: 20px;
            margin: 15px 0;
            border-left: 4px solid #3b82f6;
        }
        .performance-section {
            margin: 20px 0;
            padding: 15px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
        }
        .performance-title {
            color: #3b82f6;
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 15px;
            border-bottom: 2px solid #3b82f6;
            padding-bottom: 8px;
        }
        .performance-item {
            margin: 8px 0;
            padding: 5px 0;
            line-height: 1.6;
        }
        .performance-bullet {
            color: #3b82f6;
            font-weight: bold;
            margin-right: 8px;
        }
        .performance-label {
            color: #e5e7eb;
            font-weight: 600;
        }
        .performance-value {
            color: #fbbf24;
        }
        .chat-message {
            background: rgba(59, 130, 246, 0.1);
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #3b82f6;
        }
        .chat-message h3 {
            color: #3b82f6;
            margin-bottom: 10px;
        }
        .chat-message strong {
            color: #ffffff;
        }
        .chat-message p {
            color: #e5e7eb;
            line-height: 1.6;
        }
        .chat-timestamp {
            color: #9ca3af;
            font-size: 12px;
            text-align: right;
            margin-top: 8px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Check if AI is enabled
        if not self.ai_coach.enabled:
            self._render_api_key_warning()
            return
        
        # Quick action buttons
        self._render_quick_actions()
        
        st.markdown("---")
        
        # Chat messages
        self._render_chat_messages()
        
        # Chat input
        self._render_chat_input()
        
        # Focus score sidebar
        self._render_focus_score()
    
    def _render_api_key_warning(self):
        """Render API key warning"""
        st.error("""
        🔑 **Google Gemini API Anahtarı Gerekli**
        
        AI Koç özelliğini kullanabilmek için Google Gemini API anahtarınızı `.env` dosyasına eklemeniz gerekiyor.
        
        1. [Google AI Studio](https://makersuite.google.com/app/apikey) adresinden API anahtarı alın
        2. `.env` dosyasına `GOOGLE_API_KEY=your_key_here` şeklinde ekleyin
        3. Uygulamayı yeniden başlatın
        """)
        
        st.markdown("### 💡 AI Koç ile Neler Yapabilirsin?")
        
        features = [
            "🎯 Kişiselleştirilmiş odaklanma tavsiyeleri",
            "📊 Üretkenlik analizi ve önerileri",
            "🍅 Pomodoro tekniği rehberliği",
            "📋 Görev önceliklendirme yardımı",
            "💪 Motivasyon ve destek",
            "🧘 Stres yönetimi teknikleri"
        ]
        
        for feature in features:
            st.markdown(f"- {feature}")
    
    def _render_quick_actions(self):
        """Render quick action buttons"""
        st.markdown("### ⚡ Hızlı Sorular")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🎯 Odaklanma Tavsiyesi", use_container_width=True):
                self._send_message("Daha iyi odaklanmam için ne önerirsin?")
        
        with col2:
            if st.button("📊 Performans Analizi", use_container_width=True):
                self._send_message("Bugünkü performansımı analiz eder misin?")
        
        with col3:
            if st.button("💡 Günlük İpucu", use_container_width=True):
                tip = self.ai_coach.get_daily_tip()
                self._add_message("AI Koç", tip)
    
    def _strip_html_tags(self, text: str) -> str:
        """Remove any HTML tags from text to avoid stray raw HTML in output."""
        if not text:
            return text
        # Remove <tag ...> and </tag>
        cleaned = re.sub(r"<[^>]+>", "", text)
        return cleaned
    
    def _render_chat_messages(self):
        """Render chat message history"""
        st.markdown("### 💬 Sohbet")
        
        # Load chat history if empty
        if not st.session_state.chat_messages:
            self._load_chat_history()
        
        # Display messages
        chat_container = st.container()
        
        with chat_container:
            if not st.session_state.chat_messages:
                st.markdown("""
                    <div class="chat-message">
                        <strong>🤖 AI Koç:</strong><br>
                        Merhaba! Ben FocusCore AI Koç'un. Odaklanma ve üretkenlik konularında sana yardımcı olmak için buradayım. 
                        <br><br>
                        Nasıl yardımcı olabilirim? 🎯
                    </div>
                """, unsafe_allow_html=True)
            
            for message in st.session_state.chat_messages:
                sender_icon = "👤" if message['sender'] == 'user' else "🤖"
                sender_name = "Sen" if message['sender'] == 'user' else "AI Koç"
                
                # Check if this is a performance report
                is_performance_report = "Bugünkü Performans Raporun Hazır" in message['content']
                
                if is_performance_report and message['sender'] == 'AI Koç':
                    # Display performance report with special styling
                    import html as _html
                    clean_content = self._strip_html_tags(message['content'])
                    safe_content = _html.escape(clean_content)
                    st.markdown(f"""
                    <div class="performance-report">
                        <div class="performance-title">{sender_icon} {sender_name}</div>
                        <div style="color: #e5e7eb; line-height: 1.8;">
                            {safe_content}
                        </div>
                        <div class="chat-timestamp">
                            🕐 {message['timestamp'].strftime('%H:%M')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # Regular message display
                    import html as _html
                    clean_content = self._strip_html_tags(message['content'])
                    safe_content = _html.escape(clean_content)
                    st.markdown(f"""
                    <div class="chat-message">
                        <h3>{sender_icon} {sender_name}</h3>
                        <div style="color: #e5e7eb; line-height: 1.6;">
                            {safe_content}
                        </div>
                        <div class="chat-timestamp">
                            🕐 {message['timestamp'].strftime('%H:%M')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    
    def _render_chat_input(self):
        """Render chat input form"""
        with st.form("chat_form", clear_on_submit=True):
            user_input = st.text_area(
                "Mesajını buraya yaz...", 
                placeholder="Örnek: 'Daha verimli nasıl çalışabilirim?'",
                height=100,
                key="chat_input_area"
            )
            
            col1, col2 = st.columns([3, 1])
            with col2:
                submit = st.form_submit_button("📤 Gönder", use_container_width=True, type="primary")
            
            if submit and user_input.strip():
                self._send_message(user_input.strip())
    
    def _send_message(self, message: str):
        """Send message to AI and get response"""
        # Add user message
        self._add_message("user", message)
        
        # Show loading indicator
        with st.spinner("AI Koç düşünüyor..."):
            try:
                # Get AI response
                response = asyncio.run(
                    self.ai_coach.get_response(message, st.session_state.chat_session_id)
                )
                
                # Add AI response
                self._add_message("AI Koç", response)
                
            except Exception as e:
                error_message = "Üzgünüm, şu anda bir teknik sorun yaşıyorum. Lütfen biraz sonra tekrar dene. 🤖"
                self._add_message("AI Koç", error_message)
                print(f"Chat error: {e}")
        
        st.rerun()
    
    def _add_message(self, sender: str, content: str):
        """Add message to chat history"""
        message = {
            'sender': sender,
            'content': content,
            'timestamp': datetime.now()
        }
        
        st.session_state.chat_messages.append(message)
        
        # Keep only last 20 messages in session
        if len(st.session_state.chat_messages) > 20:
            st.session_state.chat_messages = st.session_state.chat_messages[-20:]
    
    def _load_chat_history(self):
        """Load chat history from database"""
        try:
            # Get current user ID from session state
            user = st.session_state.get("user")
            user_id = None
            
            if user:
                # Handle both User object and dict
                if hasattr(user, 'id'):
                    user_id = user.id
                elif isinstance(user, dict):
                    user_id = user.get('id')
            
            if not user_id:
                return
            
            db_messages = get_chat_messages(
                user_id,
                st.session_state.chat_session_id, 
                limit=10
            )
            
            for db_msg in db_messages:
                # Add user message
                self._add_message("user", db_msg.get('user_message', ''))
                # Add AI response
                self._add_message("AI Koç", db_msg.get('ai_response', ''))
                
        except Exception as e:
            print(f"Error loading chat history: {e}")
    
    def _render_focus_score(self):
        """Render focus score in sidebar"""
        with st.sidebar:
            st.markdown("---")
            st.markdown("### 🎯 Odaklanma Skoru")
            
            try:
                # Get current user ID from session state
                user = st.session_state.get("user")
                user_id = None
                
                if user:
                    # Handle both User object and dict
                    if hasattr(user, 'id'):
                        user_id = user.id
                    elif isinstance(user, dict):
                        user_id = user.get('id')
                
                if not user_id:
                    st.warning("Giriş yapmanız gerekiyor.")
                    return
                
                focus_data = self.ai_coach.get_focus_score(user_id)
                
                # Overall score with circular progress
                score = focus_data['overall_score']
                st.markdown(f"""
                    <div style="text-align: center; padding: 20px; background: rgba(59, 130, 246, 0.1); border-radius: 10px;">
                        <div style="font-size: 36px; font-weight: bold; color: #3b82f6;">{score}%</div>
                        <div style="color: #94a3b8;">{focus_data['level']}</div>
                    </div>
                """, unsafe_allow_html=True)
                
                # Detailed metrics
                st.markdown("**📊 Detaylar:**")
                st.progress(focus_data['consistency'] / 100)
                st.caption(f"Tutarlılık: {focus_data['consistency']}%")
                
                st.progress(focus_data['task_completion'] / 100)
                st.caption(f"Görev Tamamlama: {focus_data['task_completion']}%")
                
                st.progress(focus_data['daily_achievement'] / 100)
                st.caption(f"Günlük Hedef: {focus_data['daily_achievement']}%")
                
                # Tips for improvement
                if focus_data['next_level_tips']:
                    st.markdown("**💡 İyileştirme Önerileri:**")
                    for tip in focus_data['next_level_tips']:
                        st.markdown(f"• {tip}")
                
            except Exception as e:
                st.error("Odaklanma skoru hesaplanırken hata oluştu.")
                print(f"Focus score error: {e}")