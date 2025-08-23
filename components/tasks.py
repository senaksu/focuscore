import streamlit as st
from datetime import datetime, date
from database.database import add_task, get_tasks, update_task, delete_task
from database.models import Task
import html
from typing import Optional

class TaskManager:
    def __init__(self):
        self._init_session_state()
    
    def _init_session_state(self):
        """Initialize session state variables"""
        if 'task_filter' not in st.session_state:
            st.session_state.task_filter = 'all'
        if 'new_task' not in st.session_state:
            st.session_state.new_task = {
                'title': '',
                'description': '',
                'priority': 'medium',
                'due_date': None
            }
    
    def render(self, is_embedded: bool = False, limit: Optional[int] = None):
        """Render task management interface"""
        if not is_embedded:
            st.markdown("<h1 style='color: white;'>📋 Görev Yönetimi</h1>", unsafe_allow_html=True)
        
        # Add new task section
        self._render_add_task()
        
        st.markdown("---")
        
        # Filter and display tasks
        self._render_task_filters()
        self._render_task_list(limit=limit)
    
    def _render_add_task(self):
        """Render add new task form"""
        st.markdown("### ➕ Yeni Görev Ekle")
        
        with st.form("add_task_form"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                title = st.text_input("Görev Başlığı", placeholder="Görevinizi buraya yazın...")
                description = st.text_area("Açıklama (Opsiyonel)", placeholder="Detaylar...")
            
            with col2:
                priority = st.selectbox("Öncelik", ["low", "medium", "high"], 
                                      format_func=self._format_priority)
                due_date = st.date_input("Bitiş Tarihi (Opsiyonel)", value=None, min_value=date.today())
            
            submit_button = st.form_submit_button("🎯 Görev Ekle", use_container_width=True, type="primary")
            
            if submit_button and title.strip():
                # Sanitize inputs
                sanitized_title = html.escape(title.strip())
                sanitized_description = html.escape(description.strip()) if description else ""
                
                # Validate input
                if len(sanitized_title) > 200:
                    st.error("Görev başlığı 200 karakterden uzun olamaz.")
                    return
                
                if len(sanitized_description) > 1000:
                    st.error("Açıklama 1000 karakterden uzun olamaz.")
                    return
                
                self._add_task(sanitized_title, sanitized_description, priority, due_date)
    
    def _format_priority(self, priority: str) -> str:
        """Format priority display"""
        priority_map = {
            'low': '🟢 Düşük',
            'medium': '🟡 Orta', 
            'high': '🔴 Yüksek'
        }
        return priority_map.get(priority, priority)
    
    def _add_task(self, title: str, description: str, priority: str, due_date):
        """Add new task to database"""
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
        
        task = Task(
            title=title,
            description=description,
            priority=priority,
            due_date=datetime.combine(due_date, datetime.min.time()) if due_date else None
        )
        
        result = add_task(task, user_id)
        
        if result:
            st.success("✅ Görev başarıyla eklendi!")
            st.rerun()
        else:
            st.error("❌ Görev eklenirken hata oluştu.")
    
    def _render_task_filters(self):
        """Render task filter options"""
        st.markdown("### 🔍 Görev Filtresi")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📋 Tüm Görevler", use_container_width=True, 
                        type="primary" if st.session_state.task_filter == 'all' else "secondary"):
                st.session_state.task_filter = 'all'
                st.rerun()
        
        with col2:
            if st.button("⏳ Bekleyenler", use_container_width=True,
                        type="primary" if st.session_state.task_filter == 'pending' else "secondary"):
                st.session_state.task_filter = 'pending'
                st.rerun()
        
        with col3:
            if st.button("✅ Tamamlananlar", use_container_width=True,
                        type="primary" if st.session_state.task_filter == 'completed' else "secondary"):
                st.session_state.task_filter = 'completed'
                st.rerun()
        
        with col4:
            if st.button("🔴 Yüksek Öncelikli", use_container_width=True,
                        type="primary" if st.session_state.task_filter == 'high_priority' else "secondary"):
                st.session_state.task_filter = 'high_priority'
                st.rerun()
    
    def _render_task_list(self, limit: Optional[int] = None):
        """Render task list based on current filter"""
        tasks = self._get_filtered_tasks()
        
        if limit:
            tasks = tasks[:limit]
        
        if not tasks:
            self._render_empty_state()
            return
        
        st.markdown(f"### 📝 Görevler ({len(tasks)} adet)")
        
        for task in tasks:
            self._render_task_item(task)
    
    def _get_filtered_tasks(self):
        """Get tasks based on current filter"""
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
            return []
        
        all_tasks = get_tasks(user_id=user_id)
        
        if st.session_state.task_filter == 'all':
            return all_tasks
        elif st.session_state.task_filter == 'pending':
            return [task for task in all_tasks if not task.get('completed')]
        elif st.session_state.task_filter == 'completed':
            return [task for task in all_tasks if task.get('completed')]
        elif st.session_state.task_filter == 'high_priority':
            return [task for task in all_tasks if task.get('priority') == 'high' and not task.get('completed')]
        else:
            return all_tasks
    
    def _render_empty_state(self):
        """Render empty state message"""
        filter_messages = {
            'all': "Henüz hiç görev eklenmemiş.",
            'pending': "Tüm görevler tamamlanmış! 🎉",
            'completed': "Henüz hiç görev tamamlanmamış.",
            'high_priority': "Yüksek öncelikli görev yok."
        }
        
        message = filter_messages.get(st.session_state.task_filter, "Görev bulunamadı.")
        st.info(f"📝 {message}")
    
    def _render_task_item(self, task):
        """Render individual task item"""
        # Determine task styling
        priority_classes = {
            'high': 'priority-high',
            'medium': 'priority-medium', 
            'low': 'priority-low'
        }
        
        priority_class = priority_classes.get(task.get('priority', 'medium'), 'priority-medium')
        completed_class = ' completed-task' if task.get('completed') else ''
        
        # Task container
        with st.container():
            st.markdown(f"""
                <div class="task-item {priority_class}{completed_class}">
            """, unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                # Task title and description
                title_style = "text-decoration: line-through; opacity: 0.6;" if task.get('completed') else ""
                st.markdown(f"**<span style='{title_style}'>{html.escape(task.get('title', ''))}</span>**", unsafe_allow_html=True)
                
                if task.get('description'):
                    desc_style = "opacity: 0.6;" if task.get('completed') else "opacity: 0.8;"
                    st.markdown(f"<small style='{desc_style}'>{html.escape(task.get('description', ''))}</small>", unsafe_allow_html=True)
                
                # Due date
                if task.get('due_date'):
                    try:
                        due_date = datetime.fromisoformat(task.get('due_date').replace('Z', '+00:00'))
                        due_text = due_date.strftime("%d.%m.%Y")
                        is_overdue = due_date.date() < date.today() and not task.get('completed')
                        due_color = "color: #ef4444;" if is_overdue else "color: #f59e0b;"
                        st.markdown(f"<small style='{due_color}'>📅 {due_text}</small>", unsafe_allow_html=True)
                    except:
                        pass
            
            with col2:
                # Priority indicator
                priority_display = self._format_priority(task.get('priority', 'medium'))
                st.markdown(f"<small>{priority_display}</small>", unsafe_allow_html=True)
            
            with col3:
                # Complete/Uncomplete button
                if task.get('completed'):
                    if st.button("↩️", key=f"uncomplete_{task.get('id')}", help="Tamamlanmadı olarak işaretle"):
                        self._toggle_task_status(task.get('id'), False)
                else:
                    if st.button("✅", key=f"complete_{task.get('id')}", help="Tamamlandı olarak işaretle"):
                        self._toggle_task_status(task.get('id'), True)
            
            with col4:
                # Delete button
                if st.button("🗑️", key=f"delete_{task.get('id')}", help="Görevi sil"):
                    self._delete_task(task.get('id'))
            
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
    
    def _toggle_task_status(self, task_id, new_status):
        """Toggle task completion status"""
        try:
            updates = {'completed': new_status}
            if new_status:
                updates['completed_at'] = datetime.now().isoformat()
            else:
                updates['completed_at'] = None
            
            # Get current user ID from session state
            user = st.session_state.get("user")
            user_id = None
            
            if user:
                if hasattr(user, 'id'):
                    user_id = user.id
                elif isinstance(user, dict):
                    user_id = user.get('id')
            
            if user_id:
                result = update_task(task_id, updates, user_id)
                if result:
                    st.toast("✅ Görev durumu güncellendi!")
                    st.rerun()
                else:
                    st.error("❌ Görev güncellenirken hata oluştu.")
            else:
                st.error("❌ Kullanıcı kimliği bulunamadı.")
        except Exception as e:
            st.error(f"❌ Hata: {str(e)}")
    
    def _delete_task(self, task_id):
        """Delete task"""
        try:
            # Get current user ID from session state
            user = st.session_state.get("user")
            user_id = None
            
            if user:
                if hasattr(user, 'id'):
                    user_id = user.id
                elif isinstance(user, dict):
                    user_id = user.get('id')
            
            if user_id:
                result = delete_task(task_id, user_id)
                if result:
                    st.success("✅ Görev başarıyla silindi!")
                    st.rerun()
                else:
                    st.error("❌ Görev silinirken hata oluştu.")
            else:
                st.error("❌ Kullanıcı kimliği bulunamadı.")
        except Exception as e:
            st.error(f"❌ Hata: {str(e)}")
    
    def get_task_stats(self):
        """Get task statistics"""
        # Get current user ID from session state
        user = st.session_state.get("user")
        user_id = None
        
        if user:
            if hasattr(user, 'id'):
                user_id = user.id
            elif isinstance(user, dict):
                user_id = user.get('id')
        
        if not user_id:
            return {
                'total_tasks': 0,
                'completed_tasks': 0,
                'pending_tasks': 0,
                'high_priority_pending': 0,
                'today_completed': 0,
                'completion_rate': 0
            }
        
        all_tasks = get_tasks(user_id=user_id)
        completed_tasks = [t for t in all_tasks if t.get('completed')]
        pending_tasks = [t for t in all_tasks if not t.get('completed')]
        high_priority_tasks = [t for t in pending_tasks if t.get('priority') == 'high']
        
        # Today's tasks
        today = date.today()
        today_completed = [t for t in completed_tasks 
                          if t.get('completed_at') and 
                          datetime.fromisoformat(t.get('completed_at').replace('Z', '+00:00')).date() == today]
        
        return {
            'total_tasks': len(all_tasks),
            'completed_tasks': len(completed_tasks),
            'pending_tasks': len(pending_tasks),
            'high_priority_pending': len(high_priority_tasks),
            'today_completed': len(today_completed),
            'completion_rate': len(completed_tasks) / len(all_tasks) * 100 if all_tasks else 0
        }
