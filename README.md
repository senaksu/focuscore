# 🧠⏰ FocusCore - AI Destekli Üretkenlik Platformu

FocusCore, yapay zeka destekli odaklanma ve üretkenlik artırma platformudur. Pomodoro tekniği, görev yönetimi ve kişiselleştirilmiş AI koçluk özellikleri ile kullanıcıların hedeflerine ulaşmasına yardımcı olur.

## ✨ Özellikler

### 🍅 **Pomodoro Timer**
- Özelleştirilebilir çalışma ve mola süreleri
- Otomatik faz geçişleri
- İstatistik takibi ve raporlama
- Sesli bildirimler

### 📋 **Görev Yönetimi**
- Öncelik bazlı görev sınıflandırma
- Tarih bazlı planlama
- İlerleme takibi
- Görev tamamlama oranları

### 🤖 **AI Coach**
- Google Gemini AI entegrasyonu
- Kişiselleştirilmiş üretkenlik tavsiyeleri
- Performans analizi
- Motivasyon mesajları

## 🚀 Kurulum

### Gereksinimler
- Python 3.8+
- Streamlit 1.35.0+
- Supabase hesabı
- Google AI API anahtarı

### 1. Repository'yi klonlayın
```bash
git clone https://github.com/yourusername/focuscore.git
cd focuscore
```

### 2. Sanal ortam oluşturun
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# veya
.venv\Scripts\activate  # Windows
```

### 3. Bağımlılıkları yükleyin
```bash
pip install -r requirements.txt
```

### 4. Environment variables ayarlayın
```bash
cp env.example .env
```

`.env` dosyasını düzenleyin:
```env
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
GOOGLE_API_KEY=your_google_api_key
ENVIRONMENT=development
```

### 5. Uygulamayı çalıştırın
```bash
streamlit run app.py
```

## 🗄️ Veritabanı Kurulumu

### Supabase Kurulumu
1. [Supabase](https://supabase.com) hesabı oluşturun
2. Yeni proje oluşturun
3. SQL Editor'de aşağıdaki tabloları oluşturun:

```sql
-- Pomodoro sessions table
CREATE TABLE pomodoro_sessions (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    start_time TIMESTAMPTZ,
    end_time TIMESTAMPTZ,
    duration_minutes INTEGER DEFAULT 25,
    phase TEXT DEFAULT 'work',
    completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tasks table
CREATE TABLE tasks (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    priority TEXT DEFAULT 'medium',
    completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    due_date TIMESTAMPTZ
);

-- Chat messages table
CREATE TABLE chat_messages (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    user_message TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    session_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE pomodoro_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Users can view own pomodoro sessions" ON pomodoro_sessions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own pomodoro sessions" ON pomodoro_sessions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own pomodoro sessions" ON pomodoro_sessions
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own pomodoro sessions" ON pomodoro_sessions
    FOR DELETE USING (auth.uid() = user_id);

-- Similar policies for tasks and chat_messages
```

## 🏗️ Proje Yapısı

```
focuscore/
├── 🚀 app.py                    # Ana Streamlit uygulaması
├── 🗄️ database/                # Veritabanı katmanı
│   ├── database.py             # Supabase işlemleri
│   ├── models.py               # Veri modelleri
│   └── supabase_client.py      # Supabase bağlantısı
├── 🧩 components/               # UI bileşenleri
│   ├── pomodoro.py             # Pomodoro timer
│   ├── tasks.py                # Görev yönetimi
│   ├── chat.py                 # AI chat arayüzü
│   └── auth.py                 # Kimlik doğrulama
├── 🤖 ai_coach/                # AI Coach sistemi
│   ├── agent.py                # AI agent
│   └── prompts.py              # AI promptları
├── 🛠️ utils/                   # Yardımcı fonksiyonlar
│   └── helpers.py              # Genel yardımcılar
└── ⚙️ .streamlit/              # Streamlit konfigürasyonu
```

## 🔧 Geliştirme

### Kod Standartları
- **Type Hints**: Tüm fonksiyonlarda type hints kullanın
- **Error Handling**: Try-catch blokları ile hata yönetimi
- **Logging**: Uygun log seviyeleri kullanın
- **Documentation**: Docstring'ler ekleyin

### Test Çalıştırma
```bash
# Unit testler
python -m pytest tests/

# Coverage raporu
python -m pytest --cov=. tests/
```

### Linting ve Formatting
```bash
# Code formatting
black .
isort .

# Linting
flake8 .
mypy .
```

## 🚀 Deployment

### Streamlit Cloud
1. GitHub repository'yi Streamlit Cloud'a bağlayın
2. Environment variables'ları ayarlayın
3. Deploy edin

### Docker ile
```bash
docker build -t focuscore .
docker run -p 8501:8501 focuscore
```

## 🤝 Katkıda Bulunma

1. Fork edin
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit edin (`git commit -m 'Add amazing feature'`)
4. Push edin (`git push origin feature/amazing-feature`)
5. Pull Request oluşturun

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakın.

## 🆘 Destek

- **Issues**: [GitHub Issues](https://github.com/yourusername/focuscore/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/focuscore/discussions)
- **Email**: support@focuscore.com

## 🙏 Teşekkürler

- [Streamlit](https://streamlit.io) - Web uygulama framework'ü
- [Supabase](https://supabase.com) - Backend as a Service
- [Google Gemini AI](https://ai.google.dev/) - AI modeli
- [Pomodoro Technique](https://en.wikipedia.org/wiki/Pomodoro_Technique) - Zaman yönetimi tekniği

---

**FocusCore** ile üretkenliğinizi artırın! 🚀
