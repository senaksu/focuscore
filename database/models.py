from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class PomodoroSession:
    """Pomodoro session data model"""
    id: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_minutes: int = 25
    phase: str = "work"  # "work" or "break"
    completed: bool = False
    created_at: Optional[datetime] = None
    
    def to_dict(self):
        return {
            'id': self.id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_minutes': self.duration_minutes,
            'phase': self.phase,
            'completed': self.completed,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

@dataclass  
class Task:
    """Task data model"""
    id: Optional[int] = None
    title: str = ""
    description: str = ""
    priority: str = "medium"  # "low", "medium", "high"
    completed: bool = False
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'priority': self.priority,
            'completed': self.completed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'due_date': self.due_date.isoformat() if self.due_date else None
        }

@dataclass
class ChatMessage:
    """Chat message data model"""
    id: Optional[int] = None
    user_message: str = ""
    ai_response: str = ""
    created_at: Optional[datetime] = None
    session_id: str = ""
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_message': self.user_message,
            'ai_response': self.ai_response,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'session_id': self.session_id
        }
