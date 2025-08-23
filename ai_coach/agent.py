import os
import random
from datetime import datetime
from typing import Dict, Any, List
import google.generativeai as genai
from database.database import add_chat_message, get_chat_messages, get_pomodoro_sessions, get_tasks
from utils.helpers import get_productivity_stats
from .prompts import SYSTEM_PROMPT, CONTEXT_PROMPT_TEMPLATE, DAILY_TIPS, BREAK_ACTIVITIES

class FocusCoachAgent:
    def __init__(self):
        # Configure Gemini API
        api_key = os.getenv('GOOGLE_API_KEY')
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
            self.enabled = True
        else:
            self.enabled = False
            print("⚠️  Google API Key bulunamadı. AI Coach özelliği deaktif.")
    
    def get_context(self, user_id: str = None) -> Dict[str, Any]:
        """Get user context for personalized responses"""
        stats = get_productivity_stats(user_id=user_id)
        return {
            'today_pomodoros': stats['today_pomodoros'],
            'today_tasks': stats['completed_tasks'],
            'pending_tasks': stats['pending_tasks'],
            'avg_pomodoros': stats.get('avg_pomodoros', 0),
            'current_status': self._get_current_status(user_id)
        }
    
    def _get_current_status(self, user_id: str = None) -> str:
        """Determine current user status"""
        stats = get_productivity_stats(user_id=user_id)
        
        if stats['today_pomodoros'] == 0:
            return "Henüz bugün hiç pomodoro yapmamış"
        elif stats['today_pomodoros'] < 3:
            return "Güne yavaş başlamış, tempo artırılabilir"
        elif stats['today_pomodoros'] < 6:
            return "İyi bir ritim yakalamış"
        else:
            return "Çok üretken bir gün geçiriyor"
    
    def get_daily_tip(self) -> str:
        """Get random daily productivity tip"""
        return random.choice(DAILY_TIPS)
    
    def get_break_activity(self) -> str:
        """Get random break activity suggestion"""
        return random.choice(BREAK_ACTIVITIES)
    
    def get_motivational_message(self, context: str = "general", user_id: str = None) -> str:
        """Get motivational message based on context"""
        stats = get_productivity_stats(user_id=user_id)
        
        if context == "start_pomodoro":
            if stats['today_pomodoros'] == 0:
                return "🎯 İlk pomodoro! En zor adım atmak, şimdi akış zamanı!"
            else:
                return f"🔥 {stats['today_pomodoros']+1}. pomodoron! Ritmin harika!"
        
        elif context == "complete_pomodoro":
            return f"✅ Tebrikler! {stats['today_pomodoros']} pomodoro tamamladın. Odaklanman süper!"
        
        elif context == "break_time":
            return f"🌈 Mola zamanı! {self.get_break_activity()}"
        
        elif context == "task_complete":
            return "🎉 Bir görev daha tamamlandı! Küçük adımlar büyük başarılar yaratır."
        
        else:
            return self.get_daily_tip()
    
    async def get_response(self, user_message: str, session_id: str) -> str:
        """Get AI response to user message"""
        if not self.enabled:
            return "⚠️ AI Coach şu anda kullanılamıyor. Google API anahtarını kontrol edin."
        
        try:
            # Get current user ID from session state first
            import streamlit as st
            user = st.session_state.get("user")
            user_id = None
            
            if user:
                # Handle both User object and dict
                if hasattr(user, 'id'):
                    user_id = user.id
                elif isinstance(user, dict):
                    user_id = user.get('id')
            
            # Check if user is asking about performance analysis
            performance_keywords = [
                'performans', 'analiz', 'nasıl gidiyor', 'bugün nasıl', 'istatistik', 
                'verimlilik', 'çalışma', 'görev', 'pomodoro', 'mola', 'trend'
            ]
            
            is_performance_question = any(keyword in user_message.lower() for keyword in performance_keywords)
            
            if is_performance_question:
                # Provide detailed performance analysis
                return self._get_performance_analysis_response(user_id)
            
            # Get user context
            context = self.get_context(user_id)
            
            # Build full prompt
            context_prompt = CONTEXT_PROMPT_TEMPLATE.format(**context)
            full_prompt = f"{SYSTEM_PROMPT}\n\n{context_prompt}\n\nKullanıcı: {user_message}\nAI Koç:"
            
            # Generate response
            response = self.model.generate_content(full_prompt)
            ai_response = response.text
            
            # Save to database
            from database.models import ChatMessage
            
            if user_id:
                message = ChatMessage(
                    user_message=user_message,
                    ai_response=ai_response,
                    session_id=session_id
                )
                add_chat_message(message, user_id)
            
            return ai_response
            
        except Exception as e:
            error_msg = f"AI Coach hatası: {str(e)}"
            print(error_msg)
            
            # Provide fallback response with beautiful formatting
            return self._get_fallback_response(user_message)
    
    def _get_performance_analysis_response(self, user_id: str = None) -> str:
        """Generate comprehensive performance analysis response"""
        try:
            insights = self.analyze_performance(user_id)
            
            response = "🎉 **Merhaba Dostum! Bugünkü Performans Raporun Hazır!** 📊\n\n"
            
            # Work Efficiency
            work_eff = insights.get('work_efficiency', {})
            response += "**🎯 Çalışma Verimliliği**\n"
            response += f"• **Seviye:** {work_eff.get('level', 'N/A')} ⭐\n"
            response += f"• **Mesaj:** {work_eff.get('message', 'Veri yok')}\n"
            response += f"• **📈 Tamamlanma Oranı:** {work_eff.get('completion_rate', 'N/A')}\n"
            response += f"• **⏱️ Toplam Çalışma:** {work_eff.get('total_work_time', 'N/A')}\n\n"
            
            # Break Balance
            break_bal = insights.get('break_balance', {})
            response += "**☕ Mola Dengesi**\n"
            response += f"• **Durum:** {break_bal.get('balance', 'N/A')} ⚖️\n"
            response += f"• **Mesaj:** {break_bal.get('message', 'Veri yok')}\n"
            response += f"• **📊 Çalışma:Mola Oranı:** {break_bal.get('ratio', 'N/A')}\n"
            response += f"• **🔢 Oran:** {break_bal.get('work_break_ratio', 'N/A')}\n\n"
            
            # Task Management
            task_mgmt = insights.get('task_management', {})
            response += "**📋 Görev Yönetimi**\n"
            response += f"• **Durum:** {task_mgmt.get('status', 'N/A')} 🎯\n"
            response += f"• **Mesaj:** {task_mgmt.get('message', 'Veri yok')}\n"
            response += f"• **✅ Tamamlanan:** {task_mgmt.get('completed', 0)} | **⏳ Bekleyen:** {task_mgmt.get('pending', 0)}\n"
            response += f"• **📊 Tamamlanma Oranı:** {task_mgmt.get('completion_rate', 'N/A')}\n\n"
            
            # Productivity Trends
            trends = insights.get('productivity_trends', {})
            response += "**📈 Üretkenlik Trendi**\n"
            response += f"• **Trend:** {trends.get('trend', 'N/A')} 📊\n"
            response += f"• **Mesaj:** {trends.get('message', 'Veri yok')}\n"
            response += f"• **📅 Analiz Periyodu:** {trends.get('pattern', 'N/A')}\n\n"
            
            # Recommendations
            recommendations = insights.get('recommendations', [])
            if recommendations:
                response += "**💡 Kişisel Önerilerim**\n"
                for i, rec in enumerate(recommendations, 1):
                    response += f"• {rec}\n"
                response += "\n"
            
            # Motivational ending
            response += "---\n"
            response += "**🎊 Motivasyon Mesajı**\n"
            response += "**Harika gidiyorsun dostum!** Her gün bir öncekinden daha iyi olmaya odaklan. "
            response += "Küçük adımlar büyük değişimler yaratır! 💪\n\n"
            response += "**🚀 Sonraki Adım**\n"
            response += "Bu analizi kullanarak yarın için bir hedef belirle. "
            response += "Hangi alanı geliştirmek istiyorsun? Birlikte plan yapalım! 🤝"
            
            return response
            
        except Exception as e:
            return f"😔 Üzgünüm dostum, performans analizi yapılırken bir hata oluştu: {str(e)}\n\n"
            return "💡 **Önerim:** Şimdilik basit bir pomodoro seansı başlat ve veri toplamaya başla!"
    
    def _get_fallback_response(self, user_message: str) -> str:
        """Get fallback response when AI is not available"""
        user_message_lower = user_message.lower()
        
        # Check message content and provide appropriate response
        if any(word in user_message_lower for word in ['odaklan', 'odaklanamıyorum', 'dikkat']):
            return """🎯 **Hey dostum, odaklanma sorunu yaşadığını duyduğuma üzüldüm!** 

**🔍 Hemen Deneyebileceğin Çözümler:**
1. **5 Dakika Kuralı:** Sadece 5 dakika odaklanmayı dene
2. **Çevre Temizliği:** Masanı temizle, sadece ihtiyacın olan şeyler kalsın
3. **Pomodoro Başlat:** 25 dakikalık kısa bir seansla başla
4. **Telefonu Uzaklaştır:** Bildirimleri kapat ve görüş alanından çıkar

**🧘 **Hızlı Nefes Egzersizi:**
• 4 saniye nefes al
• 7 saniye tut
• 8 saniye ver
• 3 kez tekrarla

**🚀 Sonraki Adım:** Şimdi masanı temizle ve 5 dakika odaklanmayı dene. Nasıl gittiğini söyle! 💪"""
        
        elif any(word in user_message_lower for word in ['görev', 'task', 'yapılacak']):
            return """📋 **Görev yönetimi konusunda yardım edeyim!**

**🎯 Eisenhower Matrisi ile Önceliklendirme:**
```
        Acil     |    Acil Değil
        ⚡       |    📅
   ┌─────────────┼─────────────┐
   │            │             │
Önemli │   1. YAP    │  2. PLANLA   │
   │            │             │
   ├─────────────┼─────────────┤
   │            │             │
Önemli │   3. DELEGE │  4. ELİMİNE │
Değil  │            │             │
   └─────────────┴─────────────┘
```

**💪 Bugün İçin 3 Görev Seç:**
1. **En Zor Olan:** Sabah enerjinle hallet
2. **En Hızlı Olan:** Momentum kazanmak için
3. **En Önemli Olan:** Uzun vadeli hedefler için

**🚀 Sonraki Adım:** Görevlerini bu matrise göre sınıflandır. Hangi 3 tanesi bugün yapılmalı? 📝"""
        
        elif any(word in user_message_lower for word in ['mola', 'break', 'dinlen']):
            return """☕ **Mola zamanı! İşte harika mola aktiviteleri:**

**🧘 **Hızlı Rahatlama (2-3 dk):**
• 4-7-8 nefes tekniği
• Boyun ve omuz germe
• Gözlerini dinlendir (20-20-20 kuralı)

**💧 **Enerji Artırıcı (5 dk):**
• Bir bardak su iç
• Pencereden dışarı bak
• Sevdiğin bir şarkı dinle

**🌿 **Doğa Molası (10 dk):**
• Dışarıda kısa yürüyüş
• Temiz hava al
• Gözlerini yeşilliklerle dinlendir

**🚀 Sonraki Adım:** Şimdi bu aktivitelerden birini dene. Hangi mola türünü seçtin? 🎯"""
        
        elif any(word in user_message_lower for word in ['motivasyon', 'enerji', 'yorgun']):
            return """🔥 **Motivasyon ve enerji konusunda yardım edeyim!**

**💪 **Enerji Artırıcı Teknikler:**
1. **Power Pose:** 2 dakika güçlü duruş (eller belde, baş yukarı)
2. **Hızlı Egzersiz:** 10 jumping jack veya 20 squat
3. **Soğuk Su:** Yüzünü soğuk suyla yıka
4. **Müzik:** Enerjik bir şarkı aç ve dans et

**🧠 **Motivasyon İpuçları:**
• **Küçük Hedefler:** Büyük görevi parçalara böl
• **Ödül Sistemi:** Her başarıdan sonra kendini ödüllendir
• **Görselleştirme:** Hedefini başardığını hayal et
• **Pozitif Konuşma:** Kendine "Yapabilirim!" de

**🚀 Sonraki Adım:** Şimdi bu tekniklerden birini dene. Hangi enerji artırıcıyı seçtin? ⚡"""
        
        else:
            return """🤖 **Merhaba dostum! Ben FocusCore AI Koç'un.**

**🎯 Size nasıl yardımcı olabilirim?**
• Odaklanma sorunları
• Görev yönetimi
• Pomodoro tekniği
• Mola stratejileri
• Motivasyon ve enerji
• Performans analizi

**💡 **Önerim:** Şu anda AI özelliği geçici olarak kullanılamıyor, ama size yardımcı olmaya devam ediyorum!

**🚀 Sonraki Adım:** Hangi konuda yardım istiyorsun? Detaylı olarak anlat, size özel çözümler sunayım! 💪"""
    
    def get_productivity_analysis(self) -> str:
        """Get AI analysis of user's productivity"""
        if not self.enabled:
            return "AI analiz özelliği şu anda kullanılamıyor."
        
        try:
            stats = get_productivity_stats(detailed=True)
            
            analysis_prompt = f"""
            Kullanıcının son 7 günlük üretkenlik verilerini analiz et:
            - Toplam pomodoro: {stats.get('total_pomodoros', 0)}
            - Tamamlanan görev: {stats.get('total_completed_tasks', 0)}
            - Ortalama günlük odaklanma: {stats.get('avg_daily_focus', 0)} dakika
            - En üretken gün: {stats.get('best_day', 'Belirtilmemiş')}
            - Tutarlılık skoru: {stats.get('consistency_score', 0)}%
            
            Kısa bir analiz ve 3 pratik gelişim önerisi sun.
            """
            
            response = self.model.generate_content(f"{SYSTEM_PROMPT}\n\n{analysis_prompt}")
            return response.text
            
        except Exception as e:
            print(f"Analiz hatası: {e}")
            return "📊 Analiz yapılırken bir sorun oluştu. Daha sonra tekrar dene."
    
    def suggest_pomodoro_duration(self) -> int:
        """Suggest optimal pomodoro duration based on user performance"""
        sessions = get_pomodoro_sessions(limit=10)
        
        if not sessions:
            return 25  # Default duration
        
        # Calculate completion rate for different durations
        completed_sessions = [s for s in sessions if s.completed]
        
        if len(completed_sessions) < 3:
            return 25  # Not enough data
        
        avg_completed_duration = sum(s.duration_minutes for s in completed_sessions) / len(completed_sessions)
        
        # Suggest based on performance
        if avg_completed_duration >= 25:
            return min(30, int(avg_completed_duration + 5))  # Increase gradually
        else:
            return max(15, int(avg_completed_duration))  # Decrease for better completion
    
    def get_focus_score(self, user_id: str = None) -> Dict[str, Any]:
        """Calculate user's focus score"""
        stats = get_productivity_stats(detailed=True, user_id=user_id)
        
        # Calculate different metrics
        consistency = min(100, stats.get('consistency_score', 0))
        task_completion = min(100, (stats['completed_tasks'] / max(1, stats['pending_tasks'] + stats['completed_tasks'])) * 100)
        daily_target_achievement = min(100, (stats['today_pomodoros'] / 6) * 100)  # Target: 6 pomodoros/day
        
        overall_score = (consistency + task_completion + daily_target_achievement) / 3
        
        return {
            'overall_score': round(overall_score),
            'consistency': round(consistency),
            'task_completion': round(task_completion),
            'daily_achievement': round(daily_target_achievement),
            'level': self._get_focus_level(overall_score),
            'next_level_tips': self._get_level_tips(overall_score)
        }
    
    def _get_focus_level(self, score: float) -> str:
        """Get focus level based on score"""
        if score >= 90:
            return "🏆 Odaklanma Ustası"
        elif score >= 75:
            return "⭐ İleri Seviye"
        elif score >= 60:
            return "🎯 Orta Seviye"
        elif score >= 40:
            return "🌱 Başlangıç"
        else:
            return "🚀 Yeni Başlayan"
    
    def _get_level_tips(self, score: float) -> List[str]:
        """Get tips for reaching next level"""
        if score >= 90:
            return ["Harika! Bu tempoyu sürdür.", "Başkalarına mentor ol."]
        elif score >= 75:
            return ["Daha uzun pomodoro seansları dene.", "Daha zor görevlere odaklan."]
        elif score >= 60:
            return ["Günlük rutinini güçlendir.", "Mola zamanlarını optimize et."]
        elif score >= 40:
            return ["Küçük hedeflerle başla.", "Dikkat dağıtıcıları minimize et."]
        else:
            return ["Pomodoro tekniğini öğren.", "Basit görevlerle başla."]
    
    def analyze_performance(self, user_id: str = None) -> Dict[str, Any]:
        """Analyze user's performance and provide insights"""
        try:
            stats = get_productivity_stats(detailed=True, user_id=user_id)
            
            # Get recent sessions for trend analysis
            recent_sessions = get_pomodoro_sessions(user_id, days=7)
            work_sessions = [s for s in recent_sessions if s.get('phase') == 'work']
            break_sessions = [s for s in recent_sessions if s.get('phase') == 'break']
            
            # Check if there are any sessions
            if not recent_sessions:
                return {
                    'work_efficiency': {
                        'level': "Başlangıç",
                        'message': "Henüz pomodoro seansı yapmamışsın. İlk 25 dakikalık odaklanma seansını başlatmaya ne dersin?",
                        'completion_rate': "0%",
                        'total_work_time': "0 dakika"
                    },
                    'break_balance': {
                        'balance': "N/A",
                        'message': "Henüz çalışma verisi yok",
                        'ratio': "0:0"
                    },
                    'task_management': {
                        'status': "Görev yok",
                        'message': "Henüz görev eklenmemiş",
                        'completion_rate': "0%",
                        'total_tasks': 0,
                        'completed': 0,
                        'pending': 0
                    },
                    'productivity_trends': {
                        'trend': "Veri yok",
                        'message': "Henüz yeterli veri yok"
                    },
                    'recommendations': [
                        "🍅 İlk pomodoro seansını başlat",
                        "📋 Günlük görevler ekle",
                        "⏰ 25 dakika odaklan, 5 dakika mola ver"
                    ]
                }
            
            # Calculate performance metrics
            total_work_time = sum(s.get('duration_minutes', 0) for s in work_sessions if s.get('completed', False))
            total_break_time = sum(s.get('duration_minutes', 0) for s in break_sessions if s.get('completed', False))
            completion_rate = len([s for s in work_sessions if s.get('completed', False)]) / len(work_sessions) * 100 if work_sessions else 0
        
            # Get task completion stats
            all_tasks = get_tasks(user_id)
            completed_tasks = [t for t in all_tasks if t.get('completed', False)]
            pending_tasks = [t for t in all_tasks if not t.get('completed', False)]
            
            # Performance insights
            insights = {
                'work_efficiency': self._analyze_work_efficiency(stats, total_work_time, completion_rate),
                'break_balance': self._analyze_break_balance(total_work_time, total_break_time),
                'task_management': self._analyze_task_management(completed_tasks, pending_tasks),
                'productivity_trends': self._analyze_productivity_trends(recent_sessions),
                'recommendations': self._generate_recommendations(stats, completion_rate, total_work_time)
            }
            
            return insights
        
        except Exception as e:
            # Return friendly error message if analysis fails
            return {
                'work_efficiency': {
                    'level': "Hata",
                    'message': f"Performans analizi yapılırken bir hata oluştu: {str(e)}",
                    'completion_rate': "N/A",
                    'total_work_time': "N/A"
                },
                'break_balance': {
                    'balance': "Hata",
                    'message': "Analiz yapılamadı",
                    'ratio': "N/A"
                },
                'task_management': {
                    'status': "Hata",
                    'message': "Analiz yapılamadı",
                    'completion_rate': "N/A",
                    'total_tasks': 0,
                    'completed': 0,
                    'pending': 0
                },
                'productivity_trends': {
                    'trend': "Hata",
                    'message': "Analiz yapılamadı"
                },
                'recommendations': [
                    "🔄 Sayfayı yenile ve tekrar dene",
                    "📱 Uygulamayı yeniden başlat",
                    "🔧 Teknik destek al"
                ]
            }
    
    def _analyze_work_efficiency(self, stats: Dict, total_work_time: int, completion_rate: float) -> Dict[str, Any]:
        """Analyze work efficiency"""
        today_pomodoros = stats['today_pomodoros']
        avg_pomodoros = stats.get('avg_pomodoros', 0)
        
        if today_pomodoros == 0:
            efficiency_level = "Başlangıç"
            message = "Bugün henüz pomodoro yapmamışsın. Küçük bir 25 dakikalık seansla başlamaya ne dersin?"
        elif today_pomodoros < avg_pomodoros * 0.5:
            efficiency_level = "Düşük"
            message = f"Bugün {today_pomodoros} pomodoro yapmışsın, ortalamanın altında. Enerjini toplamaya odaklan!"
        elif today_pomodoros < avg_pomodoros:
            efficiency_level = "Orta"
            message = f"Bugün {today_pomodoros} pomodoro yapmışsın. Ortalama performansın, biraz daha odaklanabilirsin!"
        elif today_pomodoros < avg_pomodoros * 1.5:
            efficiency_level = "İyi"
            message = f"Harika! Bugün {today_pomodoros} pomodoro yapmışsın. Ortalamanın üstünde performans!"
        else:
            efficiency_level = "Mükemmel"
            message = f"İnanılmaz! Bugün {today_pomodoros} pomodoro yapmışsın. Çok üretken bir gün!"
        
        return {
            'level': efficiency_level,
            'message': message,
            'completion_rate': f"{completion_rate:.1f}%",
            'total_work_time': f"{total_work_time} dakika"
        }
    
    def _analyze_break_balance(self, total_work_time: int, total_break_time: int) -> Dict[str, Any]:
        """Analyze work-break balance"""
        if total_work_time == 0:
            return {
                'balance': "N/A",
                'message': "Henüz çalışma verisi yok",
                'ratio': "0:0"
            }
        
        work_break_ratio = total_break_time / total_work_time if total_work_time > 0 else 0
        
        if work_break_ratio < 0.1:
            balance = "Dengesiz (Çok az mola)"
            message = "Çok az mola veriyorsun! Pomodoro tekniğinde 25dk çalışma + 5dk mola önemli."
        elif work_break_ratio < 0.25:
            balance = "İyi"
            message = "İyi bir çalışma-mola dengesi kurmuşsun. Devam et!"
        elif work_break_ratio < 0.4:
            balance = "Optimal"
            message = "Mükemmel denge! Çalışma ve mola sürelerin ideal oranda."
        else:
            balance = "Çok mola"
            message = "Çok fazla mola veriyorsun. Odaklanma süreni artırmaya çalış!"
        
        return {
            'balance': balance,
            'message': message,
            'ratio': f"{total_work_time}:{total_break_time}",
            'work_break_ratio': f"{work_break_ratio:.2f}"
        }
    
    def _analyze_task_management(self, completed_tasks: List, pending_tasks: List) -> Dict[str, Any]:
        """Analyze task management effectiveness"""
        total_tasks = len(completed_tasks) + len(pending_tasks)
        
        if total_tasks == 0:
            return {
                'status': "Görev yok",
                'message': "Henüz görev eklenmemiş",
                'completion_rate': "0%",
                'total_tasks': 0,
                'completed': 0,
                'pending': 0
            }
        
        completion_rate = len(completed_tasks) / total_tasks * 100
        
        if completion_rate < 30:
            status = "Düşük"
            message = f"Görev tamamlama oranın düşük ({completion_rate:.0f}%). Küçük görevlerle başla!"
        elif completion_rate < 60:
            status = "Orta"
            message = f"Görev tamamlama oranın orta ({completion_rate:.0f}%). Daha fazla odaklanmaya çalış!"
        elif completion_rate < 80:
            status = "İyi"
            message = f"Görev tamamlama oranın iyi ({completion_rate:.0f}%). Harika gidiyorsun!"
        else:
            status = "Mükemmel"
            message = f"Görev tamamlama oranın mükemmel ({completion_rate:.0f}%)! Çok başarılısın!"
        
        return {
            'status': status,
            'message': message,
            'completion_rate': f"{completion_rate:.0f}%",
            'total_tasks': total_tasks,
            'completed': len(completed_tasks),
            'pending': len(pending_tasks)
        }
    
    def _analyze_productivity_trends(self, recent_sessions: List) -> Dict[str, Any]:
        """Analyze productivity trends over time"""
        if not recent_sessions:
            return {
                'trend': "Veri yok",
                'message': "Henüz yeterli veri yok",
                'pattern': "N/A"
            }
        
        # Group sessions by day
        from collections import defaultdict
        daily_sessions = defaultdict(list)
        
        for session in recent_sessions:
            if session.get('created_at'):
                try:
                    # Handle different date formats from Supabase
                    created_at_str = session.get('created_at', '')
                    if created_at_str:
                        # Remove microseconds and handle timezone
                        if '+' in created_at_str:
                            # Format: '2025-08-21T21:07:14.58982+00:00'
                            created_at_str = created_at_str.split('+')[0] + '+00:00'
                        elif created_at_str.endswith('Z'):
                            created_at_str = created_at_str.replace('Z', '+00:00')
                        
                        created_at = datetime.fromisoformat(created_at_str)
                        day = created_at.strftime('%Y-%m-%d')
                        daily_sessions[day].append(session)
                except (ValueError, TypeError):
                    continue
        
        # Calculate daily productivity
        daily_productivity = {}
        for day, sessions in daily_sessions.items():
            work_sessions = [s for s in sessions if s.get('phase') == 'work' and s.get('completed', False)]
            daily_productivity[day] = sum(s.get('duration_minutes', 0) for s in work_sessions)
        
        if len(daily_productivity) < 2:
            return {
                'trend': "Tek gün",
                'message': "Sadece bir gün veri var, trend analizi için daha fazla gün gerekli",
                'pattern': "N/A"
            }
        
        # Determine trend
        days = sorted(daily_productivity.keys())
        if len(days) >= 2:
            recent_days = days[-2:]
            recent_productivity = [daily_productivity[d] for d in recent_days]
            
            if recent_productivity[1] > recent_productivity[0] * 1.2:
                trend = "Yükselen"
                message = "Son günlerde üretkenliğin artıyor! Harika gidiyorsun!"
            elif recent_productivity[1] < recent_productivity[0] * 0.8:
                trend = "Düşen"
                message = "Son günlerde üretkenliğin biraz düşmüş. Motivasyonunu artırmaya odaklan!"
            else:
                trend = "Stabil"
                message = "Üretkenliğin stabil seviyede. Tutarlılık çok önemli!"
        else:
            trend = "Belirsiz"
            message = "Trend analizi için daha fazla veri gerekli"
        
        return {
            'trend': trend,
            'message': message,
            'pattern': f"Son {len(daily_productivity)} gün",
            'daily_data': daily_productivity
        }
    
    def _generate_recommendations(self, stats: Dict, completion_rate: float, total_work_time: int) -> List[str]:
        """Generate personalized recommendations"""
        recommendations = []
        
        # Work efficiency recommendations
        if stats['today_pomodoros'] == 0:
            recommendations.append("🎯 Bugün ilk pomodoronu yap! 25 dakika ile başla, momentum kazan.")
        
        if completion_rate < 70:
            recommendations.append("✅ Görev tamamlama oranını artırmak için küçük, yönetilebilir görevlerle başla.")
        
        if total_work_time > 300:  # 5+ hours
            recommendations.append("☕ Çok uzun çalışıyorsun! Düzenli molalar ver, yanma sendromunu önle.")
        
        # Task management recommendations
        if stats['pending_tasks'] > 5:
            recommendations.append("📋 Çok fazla bekleyen görevin var. En kritik 3 tanesine odaklan, diğerlerini sonraya bırak.")
        
        # Break recommendations
        if stats['today_pomodoros'] > 0 and stats['today_pomodoros'] % 4 == 0:
            recommendations.append("🌿 4 pomodoro tamamladın! Uzun mola zamanı. 15-20 dakika dinlen.")
        
        # Motivation recommendations
        if stats['today_pomodoros'] < 3:
            recommendations.append("🔥 Enerjini artırmak için kısa, yoğun pomodoro seansları yap. 15 dakika ile başla!")
        
        return recommendations[:3]  # Return top 3 recommendations