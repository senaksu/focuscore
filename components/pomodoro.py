import streamlit as st
import time
import asyncio
from datetime import datetime
from database.database import add_pomodoro_session, update_pomodoro_session, get_pomodoro_sessions
from database.models import PomodoroSession

class PomodoroTimer:
    def __init__(self):
        self._init_session_state()
    
    def _init_session_state(self):
        """Initialize session state variables"""
        if 'pomodoro_state' not in st.session_state:
            st.session_state.pomodoro_state = {
                'is_running': False,
                'start_time': None,
                'duration_minutes': 25,
                'break_duration': 5,
                'current_phase': 'work',  # 'work' or 'break'
                'session_count': 0,
                'current_session_id': None,
                'paused_time': 0,
                'break_ready': False
            }
    
    def get_status(self):
        """Get current timer status"""
        state = st.session_state.pomodoro_state
        
        if not state['is_running']:
            return {
                'is_running': False,
                'remaining_time': 0,
                'phase': state['current_phase'],
                'progress': 0
            }
        
        elapsed_seconds = (datetime.now() - state['start_time']).total_seconds() + state.get('paused_time', 0)
        total_seconds = state['duration_minutes'] * 60
        
        if state['current_phase'] == 'break':
            total_seconds = state['break_duration'] * 60
        
        remaining_seconds = max(0, total_seconds - elapsed_seconds)
        progress = min(1.0, elapsed_seconds / total_seconds)
        
        return {
            'is_running': True,
            'remaining_time': remaining_seconds,
            'phase': state['current_phase'],
            'progress': progress
        }
    
    def start_timer(self, duration_minutes: int = None):
        """Start pomodoro timer"""
        state = st.session_state.pomodoro_state
        
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
            st.error("❌ Giriş yapmanız gerekiyor.")
            return
        
        if duration_minutes:
            state['duration_minutes'] = duration_minutes
        
        state['is_running'] = True
        state['start_time'] = datetime.now()
        state['current_phase'] = 'work'
        state['paused_time'] = 0
        state['break_ready'] = False
        
        # Create new session in database
        session = PomodoroSession(
            start_time=datetime.now(),
            duration_minutes=state['duration_minutes'],
            phase='work',
            completed=False
        )
        
        result = add_pomodoro_session(session, user_id)
        if result:
            state['current_session_id'] = result.get('id')
            st.success(f"🍅 {state['duration_minutes']} dakikalık pomodoro başladı!")
        else:
            st.error("❌ Pomodoro başlatılırken hata oluştu.")
        
        st.rerun()
    
    def pause_timer(self):
        """Pause timer"""
        state = st.session_state.pomodoro_state
        if state['is_running'] and state['start_time']:
            # Calculate elapsed time and store it
            elapsed = (datetime.now() - state['start_time']).total_seconds()
            state['paused_time'] += elapsed
        
        st.session_state.pomodoro_state['is_running'] = False
        st.info("⏸️ Timer duraklatıldı")
        st.rerun()
    
    def resume_timer(self):
        """Resume timer"""
        state = st.session_state.pomodoro_state
        # Resume counting from now; keep accumulated elapsed in 'paused_time'
        state['start_time'] = datetime.now()
        state['is_running'] = True
        st.success("▶️ Timer devam ediyor")
        st.rerun()
    
    def stop_timer(self):
        """Stop and reset timer"""
        state = st.session_state.pomodoro_state
        
        # Get current user ID from session state
        user = st.session_state.get("user")
        user_id = None
        
        if user:
            # Handle both User object and dict
            if hasattr(user, 'id'):
                user_id = user.id
            elif isinstance(user, dict):
                user_id = user.get('id')
        
        # Mark current session as incomplete if exists
        if state['current_session_id'] and user_id:
            actual_duration = state['duration_minutes'] if state['current_phase'] == 'work' else state['break_duration']
            update_pomodoro_session(
                state['current_session_id'],
                {
                    'end_time': datetime.now().isoformat(),
                    'duration_minutes': actual_duration,
                    'completed': False
                },
                user_id
            )
        
        # Reset state
        state['is_running'] = False
        state['start_time'] = None
        state['current_session_id'] = None
        state['current_phase'] = 'work'
        state['paused_time'] = 0
        state['break_ready'] = False
        
        st.warning("⏹️ Timer durduruldu")
        st.rerun()
    
    def complete_session(self):
        """Mark current session as completed"""
        state = st.session_state.pomodoro_state
        
        # Get current user ID from session state
        user = st.session_state.get("user")
        user_id = None
        
        if user:
            # Handle both User object and dict
            if hasattr(user, 'id'):
                user_id = user.id
            elif isinstance(user, dict):
                user_id = user.get('id')
        
        if state['current_session_id'] and user_id:
            # Calculate actual duration based on current phase
            if state['current_phase'] == 'work':
                actual_duration = state['duration_minutes']
            else:  # break phase
                actual_duration = state['break_duration']
            
            # Update existing session instead of creating new one
            update_pomodoro_session(
                state['current_session_id'],
                {
                    'end_time': datetime.now().isoformat(),
                    'duration_minutes': actual_duration,
                    'completed': True
                },
                user_id
            )
            
            state['session_count'] += 1
            
            # Start break or end session
            if state['current_phase'] == 'work':
                self._prepare_break()
            else:
                self._end_session()
    
    def _prepare_break(self):
        """Prepare break period (don't auto-start)"""
        state = st.session_state.pomodoro_state
        state['is_running'] = False
        state['start_time'] = None
        state['current_session_id'] = None
        state['paused_time'] = 0
        state['break_ready'] = True
        
        st.success("🎉 Pomodoro tamamlandı! İstersen molaya başlayabilirsin.")
        st.balloons()
    
    def start_break(self):
        """Start break period manually"""
        state = st.session_state.pomodoro_state
        
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
            st.error("❌ Giriş yapmanız gerekiyor.")
            return
        
        state['current_phase'] = 'break'
        state['start_time'] = datetime.now()
        state['is_running'] = True
        state['paused_time'] = 0
        state['break_ready'] = False
        
        # Create break session
        session = PomodoroSession(
            start_time=datetime.now(),
            duration_minutes=state['break_duration'],
            phase='break',
            completed=False
        )
        
        result = add_pomodoro_session(session, user_id)
        if result:
            state['current_session_id'] = result.get('id')
            st.success(f"☕ {state['break_duration']} dakikalık mola başladı!")
        else:
            st.error("❌ Mola başlatılırken hata oluştu.")
        
        st.rerun()
    
    def _end_session(self):
        """End current session"""
        state = st.session_state.pomodoro_state
        state['is_running'] = False
        state['start_time'] = None
        state['current_session_id'] = None
        state['current_phase'] = 'work'
        state['paused_time'] = 0
        state['break_ready'] = False
        
        st.success("🎉 Harika! Bir pomodoro daha tamamlandı!")
        st.balloons()
    
    def render(self, is_embedded: bool = False):
        """Render the Pomodoro timer component"""
        if not is_embedded:
            st.markdown("<h1 style='color: white;'>🍅 Pomodoro Zamanlayıcı</h1>", unsafe_allow_html=True)
        
        # Get current status
        status = self.get_status()
        
        # Initial choice section (only show when timer is not running and not in break_ready state)
        if not status['is_running'] and not st.session_state.pomodoro_state['break_ready']:
            st.markdown("### 🎯 Ne Yapmak İstiyorsun?")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🍅 Pomodoro Çalışması Başlat", use_container_width=True, type="primary"):
                    st.session_state.pomodoro_state['current_phase'] = 'work'
                    st.rerun()
            
            with col2:
                if st.button("☕ Mola Başlat", use_container_width=True, type="secondary"):
                    self.start_break()
            
            st.markdown("---")
        
        # Settings section
        if not status['is_running']:
            st.markdown("### ⚙️ Timer Ayarları")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🍅 Çalışma Süresi (dakika)**")
                work_duration = st.number_input(
                    "Çalışma Süresi", 
                    min_value=1, 
                    max_value=120, 
                    value=st.session_state.pomodoro_state['duration_minutes'],
                    step=1,
                    label_visibility="collapsed"
                )
                st.session_state.pomodoro_state['duration_minutes'] = work_duration
            
            with col2:
                st.markdown("**☕ Mola Süresi (dakika)**")
                break_duration = st.number_input(
                    "Mola Süresi", 
                    min_value=1, 
                    max_value=60, 
                    value=st.session_state.pomodoro_state['break_duration'],
                    step=1,
                    label_visibility="collapsed"
                )
                st.session_state.pomodoro_state['break_duration'] = break_duration
        
        st.markdown("---")
        
        # Timer display
        if status['is_running']:
            remaining = status['remaining_time']
            mins, secs = divmod(int(remaining), 60)
            
            # Large timer display
            st.markdown(f"""
                <div class="timer-display">
                    {mins:02d}:{secs:02d}
                </div>
            """, unsafe_allow_html=True)
            
            # Progress bar
            progress = status['progress']
            st.progress(progress)
            
            # Phase indicator
            phase_text = "🍅 Çalışma Zamanı" if status['phase'] == 'work' else "☕ Mola Zamanı"
            phase_class = "status-active" if status['phase'] == 'work' else "status-break"
            
            st.markdown(f"""
                <div class="{phase_class}" style="text-align: center; font-size: 20px; margin: 20px 0;">
                    {phase_text}
                </div>
            """, unsafe_allow_html=True)
            
            # Check if session completed
            if remaining <= 0:
                self.complete_session()
                st.rerun()
            
            # Control buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("⏸️ Duraklat", use_container_width=True):
                    self.pause_timer()
            with col2:
                if st.button("⏹️ Durdur", use_container_width=True):
                    self.stop_timer()
            with col3:
                if st.button("✅ Tamamlandı", use_container_width=True):
                    self.complete_session()
            
            # Auto-refresh every second for real-time updates
            time.sleep(1)
            st.rerun()
        
        elif st.session_state.pomodoro_state['break_ready']:
            # Break ready state
            st.markdown(f"""
                <div class="timer-display status-break">
                    {st.session_state.pomodoro_state['break_duration']:02d}:00
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
                <div class="status-break" style="text-align: center; font-size: 20px; margin: 20px 0;">
                    ☕ Mola Hazır - İstersen molaya başla
                </div>
            """, unsafe_allow_html=True)
            
            # Break control buttons
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("☕ Mola Başlat", use_container_width=True, type="secondary"):
                    self.start_break()
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🍅 Yeni Pomodoro", use_container_width=True, type="primary"):
                    st.session_state.pomodoro_state['break_ready'] = False
                    st.session_state.pomodoro_state['current_phase'] = 'work'
                    st.rerun()
            with col2:
                if st.button("🏁 Bitir", use_container_width=True):
                    st.session_state.pomodoro_state['break_ready'] = False
                    st.session_state.pomodoro_state['current_phase'] = 'work'
                    st.success("Çalışma seansı tamamlandı!")
                    st.rerun()
        
        else:
            # Timer not running
            st.markdown(f"""
                <div class="timer-display status-inactive">
                    {st.session_state.pomodoro_state['duration_minutes']:02d}:00
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
                <div class="status-inactive" style="text-align: center; font-size: 20px; margin: 20px 0;">
                    Timer Hazır - Başlamak için butona bas
                </div>
            """, unsafe_allow_html=True)
            
            # Start button
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🚀 Pomodoro Başlat", use_container_width=True, type="primary"):
                    self.start_timer()
        
        st.markdown("---")
        
        # Today's statistics
        self._show_today_stats()
        
        # Recent sessions
        if not is_embedded:
            self._show_recent_sessions()

        # Note about data management
        st.info("💡 **Veri Yönetimi:** Tüm verileriniz Supabase'de güvenli şekilde saklanıyor ve sadece size özel. Eski verileri temizlemek için Supabase Dashboard'ı kullanabilirsiniz.")
    
    def _show_today_stats(self):
        """Show today's pomodoro statistics"""
        st.markdown("### 📊 Bugünkü İstatistikler")
        
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
        
        today_sessions = get_pomodoro_sessions(user_id, days=1)
        completed_work_sessions = [s for s in today_sessions if s.get('completed', False) and s.get('phase') == 'work']
        total_focus_time = sum(s.get('duration_minutes', 0) for s in completed_work_sessions)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Tamamlanan Pomodoro", len(completed_work_sessions))
        
        with col2:
            st.metric("Toplam Odaklanma", f"{total_focus_time} dk")
        
        with col3:
            avg_duration = total_focus_time / len(completed_work_sessions) if completed_work_sessions else 0
            st.metric("Ortalama Süre", f"{avg_duration:.0f} dk")
        
        with col4:
            work_sessions = [s for s in today_sessions if s.get('phase') == 'work']
            completion_rate = len(completed_work_sessions) / len(work_sessions) * 100 if work_sessions else 0
            st.metric("Tamamlanma Oranı", f"{completion_rate:.0f}%")
    
    def _show_recent_sessions(self):
        """Show recent pomodoro sessions"""
        st.markdown("### 📝 Son Seanslar")
        
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
        
        recent_sessions = get_pomodoro_sessions(user_id, limit=5)
        
        if not recent_sessions:
            st.info("Henüz pomodoro seansın yok. İlkini başlat!")
            return
        
        for session in recent_sessions:
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                phase_icon = "🍅" if session.get('phase') == 'work' else "☕"
                created_at = session.get('start_time', '') # Use start_time for recent sessions
                if created_at:
                    try:
                        from datetime import datetime
                        # Handle different date formats from Supabase
                        if '+' in created_at and '.' in created_at:
                            # Format: '2025-08-21T21:07:14.58982+00:00'
                            parts = created_at.split('+')
                            if len(parts) == 2:
                                date_part = parts[0]
                                timezone_part = parts[1]
                                
                                # Remove microseconds from date_part
                                if '.' in date_part:
                                    date_part = date_part.split('.')[0]
                                
                                # Reconstruct with timezone
                                clean_date_str = date_part + '+' + timezone_part
                                dt = datetime.fromisoformat(clean_date_str)
                            else:
                                dt = datetime.fromisoformat(created_at)
                        elif created_at.endswith('Z'):
                            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        else:
                            dt = datetime.fromisoformat(created_at)
                        
                        time_str = dt.strftime('%H:%M')
                    except:
                        time_str = created_at[:5]
                else:
                    time_str = 'N/A'
                st.write(f"{phase_icon} {session.get('phase', 'unknown').title()} - {time_str}")
            
            with col2:
                st.write(f"{session.get('duration_minutes', 0)} dk")
            
            with col3:
                if session.get('completed', False):
                    st.markdown("<span style='color: #10b981;'>✅ Tamamlandı</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span style='color: #ef4444;'>❌ Yarıda Bırakıldı</span>", unsafe_allow_html=True)