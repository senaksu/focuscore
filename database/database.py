"""
Supabase database management for FocusCore application.
All functions now use Supabase client for proper user data isolation.
"""

import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from supabase import Client
from .supabase_client import get_supabase_client
from .models import PomodoroSession, Task, ChatMessage

def get_supabase_db() -> Client:
    """Get Supabase client for database operations"""
    return get_supabase_client()

def init_database():
    """Initialize database - no longer needed as Supabase handles this"""
    pass

def add_pomodoro_session(session: PomodoroSession, user_id: str) -> Dict[str, Any]:
    """Add a new pomodoro session to Supabase with user_id"""
    try:
        supabase = get_supabase_db()
        
        data = {
            'user_id': user_id,
            'start_time': session.start_time.isoformat() if session.start_time else None,
            'end_time': session.end_time.isoformat() if session.end_time else None,
            'duration_minutes': session.duration_minutes,
            'phase': session.phase,
            'completed': session.completed,
            'created_at': datetime.now().isoformat()
        }
        
        result = supabase.table('pomodoro_sessions').insert(data).execute()
        return result.data[0] if result.data else {}
        
    except Exception as e:
        print(f"Error adding pomodoro session: {e}")
        return {}

def get_pomodoro_sessions(user_id: str, days: Optional[int] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Get pomodoro sessions for specific user from Supabase"""
    try:
        supabase = get_supabase_db()
        
        query = supabase.table('pomodoro_sessions').select('*').eq('user_id', user_id)
        
        if days is not None and days > 0:
            threshold = (datetime.now() - timedelta(days=days)).isoformat()
            query = query.gte('created_at', threshold)
        
        query = query.order('created_at', desc=True)
        
        if limit is not None and limit > 0:
            query = query.limit(limit)
        
        result = query.execute()
        return result.data if result.data else []
        
    except Exception as e:
        print(f"Error getting pomodoro sessions: {e}")
        return []

def update_pomodoro_session(session_id: int, updates: Dict[str, Any], user_id: str) -> bool:
    """Update a pomodoro session for specific user"""
    try:
        supabase = get_supabase_db()
        
        result = supabase.table('pomodoro_sessions').update(updates).eq('id', session_id).eq('user_id', user_id).execute()
        return len(result.data) > 0 if result.data else False
        
    except Exception as e:
        print(f"Error updating pomodoro session: {e}")
        return False

def delete_pomodoro_session(session_id: int, user_id: str) -> bool:
    """Delete a pomodoro session for specific user"""
    try:
        supabase = get_supabase_db()
        
        result = supabase.table('pomodoro_sessions').delete().eq('id', session_id).eq('user_id', user_id).execute()
        return len(result.data) > 0 if result.data else False
        
    except Exception as e:
        print(f"Error deleting pomodoro session: {e}")
        return False

def add_task(task: Task, user_id: str) -> Dict[str, Any]:
    """Add a new task to Supabase with user_id"""
    try:
        supabase = get_supabase_db()
        
        data = {
            'user_id': user_id,
            'title': task.title,
            'description': task.description,
            'priority': task.priority,
            'completed': task.completed,
            'created_at': datetime.now().isoformat(),
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'due_date': task.due_date.isoformat() if task.due_date else None
        }
        
        result = supabase.table('tasks').insert(data).execute()
        return result.data[0] if result.data else {}
        
    except Exception as e:
        print(f"Error adding task: {e}")
        return {}

def get_tasks(user_id: str, completed: Optional[bool] = None, priority: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get tasks for specific user from Supabase"""
    try:
        supabase = get_supabase_db()
        
        query = supabase.table('tasks').select('*').eq('user_id', user_id)
        
        if completed is not None:
            query = query.eq('completed', completed)
        
        if priority:
            query = query.eq('priority', priority)
        
        query = query.order('created_at', desc=True)
        
        result = query.execute()
        return result.data if result.data else []
        
    except Exception as e:
        print(f"Error getting tasks: {e}")
        return []

def update_task(task_id: int, updates: Dict[str, Any], user_id: str) -> bool:
    """Update a task for specific user"""
    try:
        supabase = get_supabase_db()
        
        result = supabase.table('tasks').update(updates).eq('id', task_id).eq('user_id', user_id).execute()
        return len(result.data) > 0 if result.data else False
        
    except Exception as e:
        print(f"Error updating task: {e}")
        return False

def delete_task(task_id: int, user_id: str) -> bool:
    """Delete a task for specific user"""
    try:
        supabase = get_supabase_db()
        
        result = supabase.table('tasks').delete().eq('id', task_id).eq('user_id', user_id).execute()
        return len(result.data) > 0 if result.data else False
        
    except Exception as e:
        print(f"Error deleting task: {e}")
        return False

def add_chat_message(message: ChatMessage, user_id: str) -> Dict[str, Any]:
    """Add a new chat message to Supabase with user_id"""
    try:
        supabase = get_supabase_db()
        
        data = {
            'user_id': user_id,
            'user_message': message.user_message,
            'ai_response': message.ai_response,
            'session_id': message.session_id,
            'created_at': datetime.now().isoformat()
        }
        
        result = supabase.table('chat_messages').insert(data).execute()
        return result.data[0] if result.data else {}
        
    except Exception as e:
        print(f"Error adding chat message: {e}")
        return {}

def get_chat_messages(user_id: str, session_id: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Get chat messages for specific user from Supabase"""
    try:
        supabase = get_supabase_db()
        
        query = supabase.table('chat_messages').select('*').eq('user_id', user_id)
        
        if session_id:
            query = query.eq('session_id', session_id)
        
        query = query.order('created_at', desc=True)
        
        if limit is not None and limit > 0:
            query = query.limit(limit)
        
        result = query.execute()
        return result.data if result.data else []
        
    except Exception as e:
        print(f"Error getting chat messages: {e}")
        return []

def delete_chat_messages(user_id: str, session_id: Optional[str] = None) -> bool:
    """Delete chat messages for specific user"""
    try:
        supabase = get_supabase_db()
        
        query = supabase.table('chat_messages').delete().eq('user_id', user_id)
        
        if session_id:
            query = query.eq('session_id', session_id)
        
        result = query.execute()
        return True
        
    except Exception as e:
        print(f"Error deleting chat messages: {e}")
        return False 