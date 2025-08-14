import streamlit as st
from datetime import datetime, date
from database.database import get_db
from database.models import Task

class TaskManager:
    def __init__(self):
        self.db = get_db()
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
    
    def render(self):
        """Render task management interface"""
        st.markdown("<h1 style='color: white;'>📋 Görev Yönetimi</h1>", unsafe_allow_html=True)
        
        # Add new task section
        self._render_add_task()
        
        st.markdown("---")
        
        # Filter and display tasks
        self._render_task_filters()
        self._render_task_list()
    
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
                self._add_task(title, description, priority, due_date)
    
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
        task = Task(
            title=title,
            description=description,
            priority=priority,
            due_date=datetime.combine(due_date, datetime.min.time()) if due_date else None
        )
        
        task_id = self.db.save_task(task)
        
        if task_id:
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
    
    def _render_task_list(self):
        """Render task list based on current filter"""
        tasks = self._get_filtered_tasks()
        
        if not tasks:
            self._render_empty_state()
            return
        
        st.markdown(f"### 📝 Görevler ({len(tasks)} adet)")
        
        for task in tasks:
            self._render_task_item(task)
    
    def _get_filtered_tasks(self):
        """Get tasks based on current filter"""
        if st.session_state.task_filter == 'all':
            return self.db.get_tasks()
        elif st.session_state.task_filter == 'pending':
            return self.db.get_tasks(completed=False)
        elif st.session_state.task_filter == 'completed':
            return self.db.get_tasks(completed=True)
        elif st.session_state.task_filter == 'high_priority':
            all_tasks = self.db.get_tasks()
            return [task for task in all_tasks if task.priority == 'high']
        else:
            return self.db.get_tasks()
    
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
    
    def _render_task_item(self, task: Task):
        """Render individual task item"""
        # Determine task styling
        priority_classes = {
            'high': 'priority-high',
            'medium': 'priority-medium', 
            'low': 'priority-low'
        }
        
        priority_class = priority_classes.get(task.priority, 'priority-medium')
        completed_class = ' completed-task' if task.completed else ''
        
        # Task container
        with st.container():
            st.markdown(f"""
                <div class="task-item {priority_class}{completed_class}">
            """, unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                # Task title and description
                title_style = "text-decoration: line-through; opacity: 0.6;" if task.completed else ""
                st.markdown(f"**<span style='{title_style}'>{task.title}</span>**", unsafe_allow_html=True)
                
                if task.description:
                    desc_style = "opacity: 0.6;" if task.completed else "opacity: 0.8;"
                    st.markdown(f"<small style='{desc_style}'>{task.description}</small>", unsafe_allow_html=True)
                
                # Due date
                if task.due_date:
                    due_text = task.due_date.strftime("%d.%m.%Y")
                    is_overdue = task.due_date.date() < date.today() and not task.completed
                    due_color = "color: #ef4444;" if is_overdue else "color: #f59e0b;"
                    st.markdown(f"<small style='{due_color}'>📅 {due_text}</small>", unsafe_allow_html=True)
            
            with col2:
                # Priority indicator
                priority_display = self._format_priority(task.priority)
                st.markdown(f"<small>{priority_display}</small>", unsafe_allow_html=True)
            
            with col3:
                # Complete/Uncomplete button
                if task.completed:
                    if st.button("↩️", key=f"uncomplete_{task.id}", help="Tamamlanmadı olarak işaretle"):
                        self.db.toggle_task_completion(task.id)
                        st.rerun()
                else:
                    if st.button("✅", key=f"complete_{task.id}", help="Tamamlandı olarak işaretle"):
                        self.db.toggle_task_completion(task.id)
                        st.rerun()
            
            with col4:
                # Delete button - Simple version
                if st.button("🗑️", key=f"delete_{task.id}", help="Görevi sil"):
                    # Simple delete without confirmation
                    try:
                        self.db.delete_task(task.id)
                        st.success(f"'{task.title}' görevi silindi!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Görev silinirken hata oluştu: {str(e)}")
                
                # Alternative: Delete with confirmation
                # if st.button("🗑️", key=f"delete_{task.id}", help="Görevi sil"):
                #     self._confirm_delete_task(task.id, task.title)
            
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
    
    def _confirm_delete_task(self, task_id: int, task_title: str):
        """Confirm and delete task"""
        # Use a more reliable confirmation system
        confirm_key = f"confirm_delete_{task_id}"
        
        if confirm_key not in st.session_state:
            st.session_state[confirm_key] = False
        
        if not st.session_state[confirm_key]:
            st.session_state[confirm_key] = True
            st.warning(f"'{task_title}' görevini silmek istediğinizden emin misiniz?")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Evet, Sil", key=f"confirm_yes_{task_id}"):
                    try:
                        self.db.delete_task(task_id)
                        st.session_state[confirm_key] = False
                        st.success("Görev başarıyla silindi!")
                        # Force page refresh
                        st.rerun()
                    except Exception as e:
                        st.error(f"Görev silinirken hata oluştu: {str(e)}")
                        st.session_state[confirm_key] = False
            
            with col2:
                if st.button("❌ Hayır, İptal", key=f"confirm_no_{task_id}"):
                    st.session_state[confirm_key] = False
                    st.rerun()
        else:
            # Reset confirmation state
            st.session_state[confirm_key] = False
    
    def get_task_stats(self):
        """Get task statistics"""
        all_tasks = self.db.get_tasks()
        completed_tasks = [t for t in all_tasks if t.completed]
        pending_tasks = [t for t in all_tasks if not t.completed]
        high_priority_tasks = [t for t in pending_tasks if t.priority == 'high']
        
        # Today's tasks
        today = date.today()
        today_completed = [t for t in completed_tasks 
                          if t.completed_at and t.completed_at.date() == today]
        
        return {
            'total_tasks': len(all_tasks),
            'completed_tasks': len(completed_tasks),
            'pending_tasks': len(pending_tasks),
            'high_priority_pending': len(high_priority_tasks),
            'today_completed': len(today_completed),
            'completion_rate': len(completed_tasks) / len(all_tasks) * 100 if all_tasks else 0
        }
