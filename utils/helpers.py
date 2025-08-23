from datetime import datetime, timedelta, date
from typing import Dict, Any, List
import streamlit as st
import logging
from database.database import get_pomodoro_sessions, get_tasks

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@st.cache_data(ttl=300)  # Cache for 5 minutes
def format_duration(minutes: int) -> str:
    """Format duration in minutes to human readable format"""
    try:
        if minutes < 60:
            return f"{minutes} dk"
        
        hours = minutes // 60
        remaining_minutes = minutes % 60
        
        if remaining_minutes == 0:
            return f"{hours} sa"
        else:
            return f"{hours} sa {remaining_minutes} dk"
    except Exception as e:
        logger.error(f"Error formatting duration: {e}")
        return f"{minutes} dk"

@st.cache_data(ttl=60)  # Cache for 1 minute
def _parse_date_safely(date_str: str) -> datetime:
    """Safely parse date strings from Supabase with different formats"""
    if not date_str:
        return datetime.now()
    
    try:
        # Handle different date formats from Supabase
        if '+' in date_str and '.' in date_str:
            # Format: '2025-08-21T21:07:14.58982+00:00'
            # Remove microseconds and keep timezone
            parts = date_str.split('+')
            if len(parts) == 2:
                date_part = parts[0]
                timezone_part = parts[1]
                
                # Remove microseconds from date_part
                if '.' in date_part:
                    date_part = date_part.split('.')[0]
                
                # Reconstruct with timezone
                clean_date_str = date_part + '+' + timezone_part
                return datetime.fromisoformat(clean_date_str)
        
        elif date_str.endswith('Z'):
            # Format: '2025-08-21T21:07:14Z'
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        
        else:
            # Standard ISO format
            return datetime.fromisoformat(date_str)
            
    except (ValueError, TypeError) as e:
        logger.warning(f"Failed to parse date '{date_str}': {e}")
        # Fallback to current time if parsing fails
        return datetime.now()

def get_productivity_stats(detailed: bool = False, user_id: str = None) -> Dict[str, Any]:
    """Get productivity statistics for specific user"""
    try:
        if not user_id:
            return {
                'today_pomodoros': 0,
                'today_focus_time': '0 dk',
                'completed_tasks': 0,
                'pending_tasks': 0,
                'today_completed_tasks': 0
            }
        
        # Get today's data
        today = date.today()
        today_sessions = get_pomodoro_sessions(user_id, days=1)
        today_pomodoros = len([s for s in today_sessions if s.get('completed', False) and s.get('phase') == 'work'])
        today_focus_time = sum(s.get('duration_minutes', 0) for s in today_sessions if s.get('completed', False) and s.get('phase') == 'work')
        
        # Get task statistics
        all_tasks = get_tasks(user_id)
        completed_tasks = len([t for t in all_tasks if t.get('completed', False)])
        pending_tasks = len([t for t in all_tasks if not t.get('completed', False)])
        
        today_completed_tasks = len([t for t in all_tasks 
                                   if t.get('completed', False) and t.get('completed_at') 
                                   and _parse_date_safely(t.get('completed_at', '')).date() == today])
        
        basic_stats = {
            'today_pomodoros': today_pomodoros,
            'today_focus_time': format_duration(today_focus_time),
            'today_completed_tasks': today_completed_tasks,
            'completed_tasks': completed_tasks,
            'pending_tasks': pending_tasks
        }
        
        if not detailed:
            return basic_stats
        
        # Detailed statistics
        # Weekly data
        weekly_sessions = get_pomodoro_sessions(user_id, days=7)
        weekly_data = []
        
        for i in range(7):
            target_date = today - timedelta(days=i)
            day_sessions = [s for s in weekly_sessions 
                           if s.get('created_at') and _parse_date_safely(s.get('created_at', '')).date() == target_date 
                           and s.get('completed', False) and s.get('phase') == 'work']
            
            weekly_data.append({
                'date': target_date.strftime('%Y-%m-%d'),
                'pomodoros': len(day_sessions),
                'focus_time': sum(s.get('duration_minutes', 0) for s in day_sessions)
            })
        
        # Task completion breakdown
        task_completion = {
            'Tamamlanan': completed_tasks,
            'Bekleyen': pending_tasks
        }
        
        # Calculate averages
        total_pomodoros = len([s for s in weekly_sessions if s.get('completed', False) and s.get('phase') == 'work'])
        avg_pomodoros = round(total_pomodoros / 7, 1) if weekly_sessions else 0
        
        # Find best day
        best_day_data = max(weekly_data, key=lambda x: x['pomodoros']) if weekly_data else None
        best_day = best_day_data['date'] if best_day_data and best_day_data['pomodoros'] > 0 else 'Henüz yok'
        
        detailed_stats = {
            **basic_stats,
            'weekly_data': weekly_data,
            'task_completion': task_completion,
            'total_pomodoros': total_pomodoros,
            'total_completed_tasks': completed_tasks,
            'avg_pomodoros': avg_pomodoros,
            'best_day': best_day
        }
        
        return detailed_stats
        
    except Exception as e:
        logger.error(f"Error getting productivity stats: {e}")
        # Return safe fallback values
        return {
            'today_pomodoros': 0,
            'today_focus_time': '0 dk',
            'completed_tasks': 0,
            'pending_tasks': 0,
            'today_completed_tasks': 0,
            'weekly_data': [],
            'task_completion': {},
            'total_pomodoros': 0,
            'total_completed_tasks': 0,
            'avg_pomodoros': 0,
            'best_day': 'Henüz yok'
        }

def calculate_productivity_score(user_data: Dict[str, Any]) -> int:
    """Calculate overall productivity score (0-100)"""
    score = 0
    
    # Pomodoro completion (40 points max)
    daily_pomodoros = user_data.get('today_pomodoros', 0)
    score += min(40, daily_pomodoros * 7)  # 7 points per pomodoro, max 40
    
    # Task completion (30 points max)
    completion_rate = user_data.get('completion_rate', 0)
    score += min(30, completion_rate * 0.3)
    
    # Consistency (30 points max)  
    consistency = user_data.get('consistency_score', 0)
    score += min(30, consistency * 0.3)
    
    return min(100, int(score))

def get_motivational_message(context: str, user_stats: Dict[str, Any]) -> str:
    """Get contextual motivational message"""
    messages = {
        'morning': [
            "🌅 Güne harika başlayacaksın! İlk pomodoronu başlat.",
            "☀️ Yeni gün, yeni fırsatlar! Hedeflerine odaklan.",
            "🚀 Sabah enerjinle en zor işi halletme zamanı!"
        ],
        'afternoon': [
            "🌞 Öğlen motivasyonu! Bir pomodoro daha yapabilirsin.",
            "💪 Güçlü devam et! Hedeflerine yaklaşıyorsun.",
            "⚡ Enerjini topla ve odaklan!"
        ],
        'evening': [
            "🌅 Güne son bir pomodoro ile nokta koy!",
            "⭐ Bugün ne kadar ilerlediğine bak - harikasın!",
            "🎯 Son bir odaklanma seansı ile günü tamamla!"
        ],
        'low_productivity': [
            "💪 Yavaş başlamak sorun değil, önemli olan devam etmek!",
            "🌱 Her büyük başarı küçük adımlarla başlar.",
            "🎯 Bugün sadece bir pomodoro yap - bu bile büyük bir adım!"
        ],
        'high_productivity': [
            "🔥 Harika gidiyorsun! Bu ritmi sürdür!",
            "⭐ Bugünkü performansın muhteşem!",
            "🏆 Sen gerçek bir odaklanma şampiyonusun!"
        ]
    }
    
    if context in messages:
        import random
        return random.choice(messages[context])
    
    return "🎯 Odaklanma zamanı! Başarabilirsin!"

def get_time_of_day() -> str:
    """Get current time of day category"""
    current_hour = datetime.now().hour
    
    if 5 <= current_hour < 12:
        return 'morning'
    elif 12 <= current_hour < 17:
        return 'afternoon'  
    elif 17 <= current_hour < 22:
        return 'evening'
    else:
        return 'night'

def validate_task_input(title: str, description: str = "", priority: str = "medium") -> Dict[str, Any]:
    """Validate task input data"""
    errors = []
    
    if not title or not title.strip():
        errors.append("Görev başlığı boş olamaz")
    
    if len(title) > 200:
        errors.append("Görev başlığı 200 karakterden uzun olamaz")
    
    if len(description) > 1000:
        errors.append("Açıklama 1000 karakterden uzun olamaz")
    
    if priority not in ['low', 'medium', 'high']:
        errors.append("Geçersiz öncelik seviyesi")
    
    return {
        'is_valid': len(errors) == 0,
        'errors': errors,
        'cleaned_data': {
            'title': title.strip(),
            'description': description.strip(),
            'priority': priority
        }
    }

def format_task_due_date(due_date: datetime) -> str:
    """Format task due date for display"""
    if not due_date:
        return ""
    
    today = date.today()
    due_date = due_date.date()
    
    diff = (due_date - today).days
    
    if diff < 0:
        return f"🔴 {abs(diff)} gün geçti"
    elif diff == 0:
        return "🟡 Bugün"
    elif diff == 1:
        return "🟢 Yarın"
    elif diff <= 7:
        return f"🟢 {diff} gün sonra"
    else:
        return f"📅 {due_date.strftime('%d.%m.%Y')}"

def export_data_summary(user_id: str = None) -> Dict[str, Any]:
    """Export summary of user data for analysis"""
    if not user_id:
        return {
            'export_date': datetime.now().isoformat(),
            'summary': {
                'total_pomodoros': 0,
                'total_focus_time_minutes': 0,
                'total_tasks': 0,
                'completed_tasks': 0,
                'high_priority_tasks': 0,
                'average_session_length': 0,
                'completion_rate': 0
            },
            'daily_breakdown': []
        }
    
    # Get all data
    sessions = get_pomodoro_sessions(user_id, days=30)  # Last 30 days
    tasks = get_tasks(user_id)
    
    # Process pomodoro data
    work_sessions = [s for s in sessions if s.get('phase') == 'work' and s.get('completed', False)]
    total_focus_time = sum(s.get('duration_minutes', 0) for s in work_sessions)
    
    # Process task data
    completed_tasks = [t for t in tasks if t.get('completed', False)]
    high_priority_tasks = [t for t in tasks if t.get('priority') == 'high']
    
    return {
        'export_date': datetime.now().isoformat(),
        'summary': {
            'total_pomodoros': len(work_sessions),
            'total_focus_time_minutes': total_focus_time,
            'total_tasks': len(tasks),
            'completed_tasks': len(completed_tasks),
            'high_priority_tasks': len(high_priority_tasks),
            'average_session_length': total_focus_time / len(work_sessions) if work_sessions else 0,
            'completion_rate': len(completed_tasks) / len(tasks) * 100 if tasks else 0
        },
        'daily_breakdown': get_productivity_stats(detailed=True, user_id=user_id)['weekly_data']
    }
