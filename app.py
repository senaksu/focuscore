import streamlit as st
import sqlite3
import time
import datetime
from datetime import timedelta
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from database.database import init_database, PomodoroSession, Task
from ai_coach.agent import FocusCoachAgent
from components.pomodoro import PomodoroTimer
from components.tasks import TaskManager
from components.chat import ChatInterface
from utils.helpers import format_duration, get_productivity_stats
import os
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="FocusCore - AI Koç",
    page_icon="🧠⏰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
    }
    
    .main-card {
        background: linear-gradient(135deg, #1e2130 0%, #2d3748 100%);
        border-radius: 15px;
        padding: 30px;
        margin: 20px 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center;
        transition: all 0.3s ease;
        cursor: pointer;
        height: 200px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    
    .main-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(59, 130, 246, 0.15);
        border: 1px solid rgba(59, 130, 246, 0.3);
    }
    
    .card-icon {
        font-size: 48px;
        margin-bottom: 15px;
        color: #3b82f6;
    }
    
    .card-title {
        font-size: 24px;
        font-weight: 700;
        color: white;
        margin-bottom: 10px;
    }
    
    .card-description {
        color: #94a3b8;
        font-size: 16px;
    }
    
    .sidebar .sidebar-content {
        background-color: #1a1d23;
    }
    
    .timer-display {
        font-size: 72px;
        font-weight: 700;
        text-align: center;
        color: #3b82f6;
        text-shadow: 0 0 20px rgba(59, 130, 246, 0.5);
        margin: 20px 0;
    }
    
    .status-active {
        color: #10b981;
        font-weight: bold;
    }
    
    .status-break {
        color: #f59e0b;
        font-weight: bold;
    }
    
    .status-inactive {
        color: #6b7280;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #1e2130 0%, #2d3748 100%);
        border-radius: 10px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .chat-message {
        background: linear-gradient(135deg, #1e2130 0%, #2d3748 100%);
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #3b82f6;
    }
    
    .task-item {
        background: linear-gradient(135deg, #1e2130 0%, #2d3748 100%);
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .priority-high { border-left: 4px solid #ef4444; }
    .priority-medium { border-left: 4px solid #f59e0b; }
    .priority-low { border-left: 4px solid #10b981; }
    
    .completed-task {
        opacity: 0.6;
        text-decoration: line-through;
    }
</style>
""", unsafe_allow_html=True)

class FocusCoreApp:
    def __init__(self):
        # Initialize database
        init_database()
        
        # Initialize session state
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 'Ana Sayfa'
        if 'pomodoro_timer' not in st.session_state:
            st.session_state.pomodoro_timer = PomodoroTimer()
        if 'ai_coach' not in st.session_state:
            st.session_state.ai_coach = FocusCoachAgent()
        if 'task_manager' not in st.session_state:
            st.session_state.task_manager = TaskManager()
    
    def _get_logo_base64(self):
        """Load and return the logo as a base64-encoded PNG."""
        logo_path = os.path.join(os.path.dirname(__file__), "images", "logo.png")
        if not os.path.exists(logo_path):
            return "" # Return empty string if logo not found
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()

    def render_sidebar(self):
        """Render sidebar navigation"""
        with st.sidebar:
            st.markdown("""
                <div style='text-align: center; padding: 20px 0;'>
                    <img src="data:image/png;base64,{}" style="width: 200px; height: auto; margin-bottom: 25px; object-fit: contain;">
                    <p style='color: #94a3b8; font-size: 14px; margin: 5px 0 0 0;'>AI Destekli Üretkenlik Koçu</p>
                </div>
            """.format(self._get_logo_base64()), unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Navigation menu
            pages = {
                "🏠 Ana Sayfa": "Ana Sayfa",
                "🍅 Pomodoro Timer": "Pomodoro",
                "📋 Görev Yönetimi": "Görevler", 
                "🤖 AI Koç Asistan": "AI Koç",
                "📊 İstatistikler": "İstatistikler"
            }
            
            for display_name, page_key in pages.items():
                if st.button(display_name, key=f"nav_{page_key}", use_container_width=True):
                    st.session_state.current_page = page_key
            
            st.markdown("---")
            
            # Show timer status in sidebar
            timer_status = st.session_state.pomodoro_timer.get_status()
            if timer_status['is_running']:
                remaining = timer_status['remaining_time']
                mins, secs = divmod(int(remaining), 60)
                st.markdown(f"""
                    <div style='text-align: center; padding: 10px; background: rgba(59, 130, 246, 0.1); border-radius: 8px;'>
                        <div style='color: #3b82f6; font-weight: bold;'>⏱️ Aktif Timer</div>
                        <div style='color: white; font-size: 20px; font-weight: bold;'>{mins:02d}:{secs:02d}</div>
                        <div style='color: #94a3b8; font-size: 12px;'>{timer_status['phase'].title()}</div>
                    </div>
                """, unsafe_allow_html=True)
    
    def render_homepage(self):
        """Render main homepage with 3 main cards"""
        st.markdown("""
            <div style='text-align: center; padding: 40px 0;'>
                <img src="data:image/png;base64,{}" style="width: 450px; height: auto; margin-bottom: 30px; object-fit: contain;">
                <p style='color: #94a3b8; font-size: 20px; margin-bottom: 40px;'>
                    AI destekli odaklanma ve üretkenlik artırma platformu
                </p>
            </div>
        """.format(self._get_logo_base64()), unsafe_allow_html=True)
        
        # Main cards
        col1, col2, col3 = st.columns(3, gap="large")
        
        with col1:
            if st.button("", key="pomodoro_card"):
                st.session_state.current_page = "Pomodoro"
                st.rerun()
            
            st.markdown("""
                <div class="main-card" onclick="document.querySelector('[data-testid=\\"pomodoro_card\\"]').click()">
                    <div class="card-icon">🍅</div>
                    <div class="card-title">Pomodoro Study Time</div>
                    <div class="card-description">AI destekli odaklanma seansları</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            if st.button("", key="tasks_card"):
                st.session_state.current_page = "Görevler"
                st.rerun()
                
            st.markdown("""
                <div class="main-card" onclick="document.querySelector('[data-testid=\\"tasks_card\\"]').click()">
                    <div class="card-icon">📋</div>
                    <div class="card-title">Görev Yönetimi</div>
                    <div class="card-description">Günlük planlamanı organize et</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col3:
            if st.button("", key="ai_card"):
                st.session_state.current_page = "AI Koç"
                st.rerun()
                
            st.markdown("""
                <div class="main-card" onclick="document.querySelector('[data-testid=\\"pomodoro_card\\"]').click()">
                    <div class="card-icon">🤖</div>
                    <div class="card-title">FocusCore Asistan</div>
                    <div class="card-description">Kişiselleştirilmiş üretkenlik tavsiyeleri</div>
                </div>
            """, unsafe_allow_html=True)
        
        # Show recent stats
        self.show_quick_stats()
    
    def show_quick_stats(self):
        """Show quick productivity stats on homepage"""
        st.markdown("---")
        st.markdown("<h3 style='color: white; text-align: center;'>📊 Bugünkü Performansın</h3>", unsafe_allow_html=True)
        
        today_stats = get_productivity_stats()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
                <div class="metric-card">
                    <h4 style='color: #3b82f6; margin: 0;'>{today_stats['today_pomodoros']}</h4>
                    <p style='color: #94a3b8; margin: 5px 0 0 0;'>Tamamlanan Pomodoro</p>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
                <div class="metric-card">
                    <h4 style='color: #10b981; margin: 0;'>{today_stats['today_focus_time']}</h4>
                    <p style='color: #94a3b8; margin: 5px 0 0 0;'>Toplam Odaklanma</p>
                </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
                <div class="metric-card">
                    <h4 style='color: #f59e0b; margin: 0;'>{today_stats['completed_tasks']}</h4>
                    <p style='color: #94a3b8; margin: 5px 0 0 0;'>Tamamlanan Görev</p>
                </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
                <div class="metric-card">
                    <h4 style='color: #ef4444; margin: 0;'>{today_stats['pending_tasks']}</h4>
                    <p style='color: #94a3b8; margin: 5px 0 0 0;'>Bekleyen Görev</p>
                </div>
            """, unsafe_allow_html=True)
    
    def run(self):
        """Main application runner"""
        self.render_sidebar()
        
        # Route to appropriate page
        if st.session_state.current_page == "Ana Sayfa":
            self.render_homepage()
        elif st.session_state.current_page == "Pomodoro":
            st.session_state.pomodoro_timer.render()
        elif st.session_state.current_page == "Görevler":
            st.session_state.task_manager.render()
        elif st.session_state.current_page == "AI Koç":
            ChatInterface(st.session_state.ai_coach).render()
        elif st.session_state.current_page == "İstatistikler":
            self.render_statistics()
    
    def render_statistics(self):
        """Render detailed statistics page"""
        st.markdown("<h1 style='color: white;'>📊 Üretkenlik İstatistiklerin</h1>", unsafe_allow_html=True)
        
        # Get detailed stats
        stats = get_productivity_stats(detailed=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Weekly pomodoro chart
            if stats['weekly_data']:
                df = pd.DataFrame(stats['weekly_data'])
                fig = px.line(df, x='date', y='pomodoros', 
                             title='Son 7 Gün Pomodoro Trendi',
                             color_discrete_sequence=['#3b82f6'])
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='white'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Task completion rate
            if stats['task_completion']:
                fig = px.pie(values=list(stats['task_completion'].values()), 
                           names=list(stats['task_completion'].keys()),
                           title='Görev Tamamlanma Oranı',
                           color_discrete_sequence=['#10b981', '#ef4444'])
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='white'
                )
                st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    app = FocusCoreApp()
    app.run()
