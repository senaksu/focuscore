import sqlite3
import os
from datetime import datetime
from typing import List, Optional
from .models import PomodoroSession, Task, ChatMessage

def get_database_path():
    """Get the database file path"""
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'focuscore.db')

def init_database():
    """Initialize the database and create tables if they don't exist"""
    db_path = get_database_path()
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create pomodoro_sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pomodoro_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time TEXT,
            end_time TEXT,
            duration_minutes INTEGER DEFAULT 25,
            phase TEXT DEFAULT 'work',
            completed BOOLEAN DEFAULT FALSE,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create tasks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            priority TEXT DEFAULT 'medium',
            completed BOOLEAN DEFAULT FALSE,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            completed_at TEXT,
            due_date TEXT
        )
    ''')
    
    # Create chat_messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_message TEXT NOT NULL,
            ai_response TEXT NOT NULL,
            session_id TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def add_pomodoro_session(session: PomodoroSession) -> int:
    """Add a new pomodoro session to the database"""
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO pomodoro_sessions (start_time, end_time, duration_minutes, phase, completed, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        session.start_time.isoformat() if session.start_time else None,
        session.end_time.isoformat() if session.end_time else None,
        session.duration_minutes,
        session.phase,
        session.completed,
        datetime.now().isoformat()
    ))
    
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return session_id

def get_pomodoro_sessions(days: Optional[int] = None, limit: Optional[int] = None) -> List[PomodoroSession]:
    """Get pomodoro sessions. If days is provided, return sessions from the last N days. If limit is provided, cap the number of rows."""
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    query = 'SELECT * FROM pomodoro_sessions'
    params: list = []
    
    if days is not None and days > 0:
        from datetime import timedelta
        threshold = (datetime.now() - timedelta(days=days)).isoformat()
        query += ' WHERE created_at >= ?'
        params.append(threshold)
    
    query += ' ORDER BY created_at DESC'
    
    if limit is not None and limit > 0:
        query += ' LIMIT ?'
        params.append(limit)
    
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    
    sessions = []
    for row in rows:
        session = PomodoroSession(
            id=row[0],
            start_time=datetime.fromisoformat(row[1]) if row[1] else None,
            end_time=datetime.fromisoformat(row[2]) if row[2] else None,
            duration_minutes=row[3],
            phase=row[4],
            completed=bool(row[5]),
            created_at=datetime.fromisoformat(row[6]) if row[6] else None
        )
        sessions.append(session)
    
    conn.close()
    return sessions

def add_task(task: Task) -> int:
    """Add a new task to the database"""
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO tasks (title, description, priority, completed, created_at, due_date)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        task.title,
        task.description,
        task.priority,
        task.completed,
        datetime.now().isoformat(),
        task.due_date.isoformat() if task.due_date else None
    ))
    
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return task_id

def get_tasks(completed: Optional[bool] = None) -> List[Task]:
    """Get tasks, optionally filtered by completion status"""
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    if completed is None:
        cursor.execute('SELECT * FROM tasks ORDER BY created_at DESC')
    else:
        cursor.execute('SELECT * FROM tasks WHERE completed = ? ORDER BY created_at DESC', (1 if completed else 0,))
    
    rows = cursor.fetchall()
    tasks: List[Task] = []
    for row in rows:
        task = Task(
            id=row[0],
            title=row[1],
            description=row[2],
            priority=row[3],
            completed=bool(row[4]),
            created_at=datetime.fromisoformat(row[5]) if row[5] else None,
            completed_at=datetime.fromisoformat(row[6]) if row[6] else None,
            due_date=datetime.fromisoformat(row[7]) if row[7] else None
        )
        tasks.append(task)
    
    conn.close()
    return tasks

def update_task(task_id: int, **kwargs):
    """Update a task in the database"""
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Build update query dynamically
    update_fields = []
    values = []
    
    set_completed_at = False
    
    for key, value in kwargs.items():
        if key in ['title', 'description', 'priority', 'completed', 'due_date']:
            if key == 'due_date' and value:
                value = value.isoformat()
            if key == 'completed':
                # completed should be 1/0 boolean; track if switching to True
                set_completed_at = bool(value)
            
            update_fields.append(f"{key} = ?")
            values.append(value)
    
    if set_completed_at:
        update_fields.append("completed_at = ?")
        values.append(datetime.now().isoformat())
    
    if update_fields:
        query = f"UPDATE tasks SET {', '.join(update_fields)} WHERE id = ?"
        values.append(task_id)
        
        cursor.execute(query, values)
        conn.commit()
    
    conn.close()

def delete_task(task_id: int):
    """Delete a task from the database"""
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()

def toggle_task_completion(task_id: int):
    """Toggle task completion and update completed_at accordingly"""
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('SELECT completed FROM tasks WHERE id = ?', (task_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return
    current = bool(row[0])
    new_completed = 0 if current else 1
    new_completed_at = None if current else datetime.now().isoformat()
    
    cursor.execute('UPDATE tasks SET completed = ?, completed_at = ? WHERE id = ?',
                   (new_completed, new_completed_at, task_id))
    conn.commit()
    conn.close()

def add_chat_message(message: ChatMessage) -> int:
    """Add a new chat message to the database"""
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO chat_messages (user_message, ai_response, session_id, created_at)
        VALUES (?, ?, ?, ?)
    ''', (
        message.user_message,
        message.ai_response,
        message.session_id,
        datetime.now().isoformat()
    ))
    
    message_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return message_id

def get_chat_messages(session_id: Optional[str] = None) -> List[ChatMessage]:
    """Get chat messages from the database"""
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    if session_id:
        cursor.execute('SELECT * FROM chat_messages WHERE session_id = ? ORDER BY created_at ASC', (session_id,))
    else:
        cursor.execute('SELECT * FROM chat_messages ORDER BY created_at DESC LIMIT 50')
    
    rows = cursor.fetchall()
    
    messages = []
    for row in rows:
        message = ChatMessage(
            id=row[0],
            user_message=row[1],
            ai_response=row[2],
            session_id=row[3],
            created_at=datetime.fromisoformat(row[4]) if row[4] else None
        )
        messages.append(message)
    
    conn.close()
    return messages

def get_chat_history(session_id: str, limit: int = 10) -> List[ChatMessage]:
    """Get chat history for a session id, oldest first, limited"""
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM chat_messages WHERE session_id = ? ORDER BY created_at ASC LIMIT ?', (session_id, limit))
    rows = cursor.fetchall()
    messages: List[ChatMessage] = []
    for row in rows:
        messages.append(ChatMessage(
            id=row[0],
            user_message=row[1],
            ai_response=row[2],
            session_id=row[3],
            created_at=datetime.fromisoformat(row[4]) if row[4] else None
        ))
    conn.close()
    return messages

def get_productivity_stats():
    """Get productivity statistics from the database"""
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get total pomodoro sessions
    cursor.execute('SELECT COUNT(*) FROM pomodoro_sessions WHERE completed = 1')
    total_sessions = cursor.fetchone()[0]
    
    # Get total work time in minutes
    cursor.execute('SELECT SUM(duration_minutes) FROM pomodoro_sessions WHERE completed = 1 AND phase = "work"')
    total_work_time = cursor.fetchone()[0] or 0
    
    # Get total tasks
    cursor.execute('SELECT COUNT(*) FROM tasks')
    total_tasks = cursor.fetchone()[0]
    
    # Get completed tasks
    cursor.execute('SELECT COUNT(*) FROM tasks WHERE completed = 1')
    completed_tasks = cursor.fetchone()[0]
    
    # Get today's sessions
    today = datetime.now().date().isoformat()
    cursor.execute('SELECT COUNT(*) FROM pomodoro_sessions WHERE DATE(created_at) = ? AND completed = 1', (today,))
    today_sessions = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'total_sessions': total_sessions,
        'total_work_time': total_work_time,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'today_sessions': today_sessions,
        'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    } 

def update_pomodoro_session(session_id: int, **kwargs):
    """Update a pomodoro session in the database"""
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Build update query dynamically
    update_fields = []
    values = []
    
    for key, value in kwargs.items():
        if key in ['start_time', 'end_time', 'duration_minutes', 'phase', 'completed']:
            if key in ['start_time', 'end_time'] and value:
                value = value.isoformat()
            update_fields.append(f"{key} = ?")
            values.append(value)
    
    if not update_fields:
        conn.close()
        return
    
    values.append(session_id)
    query = f"UPDATE pomodoro_sessions SET {', '.join(update_fields)} WHERE id = ?"
    
    cursor.execute(query, tuple(values))
    conn.commit()
    conn.close()

def delete_pomodoro_sessions_all():
    """Delete all pomodoro sessions (SQLite local cleanup)."""
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM pomodoro_sessions')
    conn.commit()
    conn.close()


def delete_pomodoro_sessions_before(dt: datetime):
    """Delete pomodoro sessions before a given datetime."""
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM pomodoro_sessions WHERE created_at < ?', (dt.isoformat(),))
    conn.commit()
    conn.close()

class DatabaseManager:
    """Database manager class for all database operations"""
    
    def __init__(self):
        self.db_path = get_database_path()
    
    def save_pomodoro_session(self, session: PomodoroSession) -> int:
        """Save pomodoro session to database"""
        return add_pomodoro_session(session)
    
    def save_task(self, task: Task) -> int:
        """Save task to database"""
        return add_task(task)
    
    def get_tasks(self, completed: Optional[bool] = None) -> List[Task]:
        """Get tasks with optional completion filter"""
        return get_tasks(completed)
    
    def update_task(self, task_id: int, **kwargs):
        """Update task in database"""
        update_task(task_id, **kwargs)
    
    def delete_task(self, task_id: int):
        """Delete task from database"""
        delete_task(task_id)
    
    def toggle_task_completion(self, task_id: int):
        """Toggle task completion state"""
        toggle_task_completion(task_id)
    
    def update_pomodoro_session(self, session_id: int, **kwargs):
        """Update pomodoro session"""
        update_pomodoro_session(session_id, **kwargs)
    
    def get_pomodoro_sessions(self, days: Optional[int] = None, limit: Optional[int] = None) -> List[PomodoroSession]:
        """Get pomodoro sessions, optionally filtered by last N days and limited"""
        return get_pomodoro_sessions(days, limit)
    
    def save_chat_message(self, message: ChatMessage) -> int:
        """Save chat message to database"""
        return add_chat_message(message)
    
    def get_chat_messages(self, session_id: Optional[str] = None) -> List[ChatMessage]:
        """Get chat messages from database"""
        return get_chat_messages(session_id)
    
    def get_chat_history(self, session_id: str, limit: int = 10) -> List[ChatMessage]:
        """Get chat history for session id"""
        return get_chat_history(session_id, limit)
    
    def add_chat_message(self, message: ChatMessage) -> int:
        """Add chat message to database"""
        return add_chat_message(message)
    
    def get_productivity_stats(self):
        """Get productivity statistics from database"""
        return get_productivity_stats()
    
    def delete_all_pomodoro_sessions(self):
        """Delete all pomodoro sessions (local cleanup)."""
        delete_pomodoro_sessions_all()
    
    def delete_pomodoro_sessions_before(self, dt: datetime):
        """Delete pomodoro sessions before datetime (local cleanup)."""
        delete_pomodoro_sessions_before(dt)

def get_db() -> DatabaseManager:
    """Get database manager instance"""
    return DatabaseManager() 