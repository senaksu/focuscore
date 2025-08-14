from datetime import datetime, timedelta, date
from typing import Dict, Any, List
from database.database import get_db

def format_duration(minutes: int) -> str:
    """Format duration in minutes to human readable format"""
    if minutes < 60:
        return f"{minutes} dk"
    
    hours = minutes // 60
    remaining_minutes = minutes % 60
    
    if remaining_minutes == 0:
        return f"{hours} sa"
    else:
        return f"{hours} sa {remaining_minutes} dk"

def get_productivity_stats(detailed: bool = False) -> Dict[str, Any]:
    """Get productivity statistics"""
    db = get_db()
    
    # Get today's data
    today = date.today()
    today_sessions = db.get_pomodoro_sessions(days=1)
    today_pomodoros = len([s for s in today_sessions if s.completed and s.phase == 'work'])
    today_focus_time = sum(s.duration_minutes for s in today_sessions if s.completed and s.phase == 'work')
    
    # Get task statistics
    all_tasks = db.get_tasks()
    completed_tasks = len([t for t in all_tasks if t.completed])
    pending_tasks = len([t for t in all_tasks if not t.completed])
    
    today_completed_tasks = len([t for t in all_tasks 
                               if t.completed and t.completed_at 
                               and t.completed_at.date() == today])
    
    basic_stats = {
        'today_pomodoros': today_pomodoros,
        'today_focus_time': format_duration(today_focus_time),
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'today_completed_tasks': today_completed_tasks
    }
    
    if not detailed:
        return basic_stats
    
    # Detailed statistics
    # Weekly data
    weekly_sessions = db.get_pomodoro_sessions(days=7)
    weekly_data = []
    
    for i in range(7):
        target_date = today - timedelta(days=i)
        day_sessions = [s for s in weekly_sessions 
                       if s.created_at and s.created_at.date() == target_date 
                       and s.completed and s.phase == 'work']
        
        weekly_data.append({
            'date': target_date.strftime('%d.%m'),
            'pomodoros': len(day_sessions),
            'focus_time': sum(s.duration_minutes for s in day_sessions)
        })
    
    weekly_data.reverse()  # Oldest to newest
    
    # Task completion breakdown
    task_completion = {
        'Tamamlanan': completed_tasks,
        'Bekleyen': pending_tasks
    } if (completed_tasks + pending_tasks) > 0 else {}
    
    # Calculate additional metrics
    avg_pomodoros = sum(day['pomodoros'] for day in weekly_data) / 7 if weekly_data else 0
    best_day_data = max(weekly_data, key=lambda x: x['pomodoros']) if weekly_data else None
    best_day = best_day_data['date'] if best_day_data and best_day_data['pomodoros'] > 0 else "Henüz yok"
    
    # Consistency score (how many days worked in last 7 days)
    working_days = len([day for day in weekly_data if day['pomodoros'] > 0])
    consistency_score = (working_days / 7) * 100
    
    # Average daily focus time
    total_weekly_focus = sum(day['focus_time'] for day in weekly_data)
    avg_daily_focus = total_weekly_focus / 7
    
    detailed_stats = {
        **basic_stats,
        'weekly_data': weekly_data,
        'task_completion': task_completion,
        'total_pomodoros': sum(day['pomodoros'] for day in weekly_data),
        'total_completed_tasks': completed_tasks,
        'avg_pomodoros': round(avg_pomodoros, 1),
        'best_day': best_day,
        'consistency_score': round(consistency_score),
        'avg_daily_focus': round(avg_daily_focus),
        'total_focus_time': format_duration(total_weekly_focus)
    }
    
    return detailed_stats

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

def export_data_summary() -> Dict[str, Any]:
    """Export summary of user data for analysis"""
    db = get_db()
    
    # Get all data
    sessions = db.get_pomodoro_sessions(days=30)  # Last 30 days
    tasks = db.get_tasks()
    
    # Process pomodoro data
    work_sessions = [s for s in sessions if s.phase == 'work' and s.completed]
    total_focus_time = sum(s.duration_minutes for s in work_sessions)
    
    # Process task data
    completed_tasks = [t for t in tasks if t.completed]
    high_priority_tasks = [t for t in tasks if t.priority == 'high']
    
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
        'daily_breakdown': get_productivity_stats(detailed=True)['weekly_data']
    }
