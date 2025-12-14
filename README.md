# RAG-Асистент для студентів СумДУ

Інтелектуальний асистент для студентів Сумського державного університету з використанням технологій RAG (Retrieval-Augmented Generation) та SGR (Schema-Guided Reasoning).

## 🎯 Основні можливості

- **RAG (Retrieval-Augmented Generation)**: Пошук релевантної інформації в нормативних документах університету
- **SGR (Schema-Guided Reasoning)**: Структуроване міркування для покращення якості відповідей
- **Векторний пошук**: Використання PostgreSQL + pgvector для швидкого семантичного пошуку
- **Grok LLM**: Генерація відповідей через Grok API (xAI)
- **Crawl4AI**: Парсинг документів з https://normative.sumdu.edu.ua/
- **FastAPI**: REST API для інтеграції з іншими сервісами

## 📋 Вимоги

- Python 3.10+
- PostgreSQL 15+ з розширенням pgvector
- Grok API key (xAI)
- Cohere API key (для embeddings - embed-multilingual-v3.0)

## 🚀 Швидкий старт

### 1. Встановлення залежностей

```bash
# Активувати віртуальне середовище
.venv\Scripts\activate  # Windows
# або
source .venv/bin/activate  # Linux/Mac

# Встановити залежності
uv pip install fastapi uvicorn sqlalchemy psycopg2-binary pgvector pydantic-settings pydantic-ai openai cohere tiktoken crawl4ai pypdf python-multipart beautifulsoup4
```

### 2. Налаштування

Створіть файл `.env` на основі `.env.example`:

```bash
cp .env.example .env
```

Відредагуйте `.env` та вкажіть:
- `DATABASE_URL` - підключення до PostgreSQL
- `GROK_API_KEY` - ваш API ключ Grok (https://x.ai/api)
- `COHERE_API_KEY` - ваш API ключ Cohere (https://dashboard.cohere.com/api-keys)

### 3. Ініціалізація бази даних

```bash
python scripts/init_db.py
```

### 4. Запуск сервера

```bash
uvicorn main:app --reload
# або
python main.py
```

API буде доступне за адресою: http://localhost:8000

Документація (Swagger): http://localhost:8000/docs

## 📚 Використання

### API Endpoints

#### Health Check
```bash
GET /health
GET /health/detailed
```

#### Запити до асистента (RAG)
```bash
POST /api/query
Content-Type: application/json

{
  "query": "Які умови отримання стипендії?",
  "top_k": 5
}
```

#### Управління документами (CRUD)

**Список документів:**
```bash
GET /api/documents?skip=0&limit=20
```

**Деталі документа:**
```bash
GET /api/documents/{id}
```

**Створити документ (URL):**
```bash
POST /api/documents
Content-Type: multipart/form-data

url=https://normative.sumdu.edu.ua/...
title=Положення про стипендії
```

**Створити документ (file upload):**
```bash
POST /api/documents
Content-Type: multipart/form-data

file=@document.pdf
title=Положення 2133
document_number=2133
```

**Оновити документ:**
```bash
PUT /api/documents/{id}
Content-Type: application/json

{
  "title": "Нова назва",
  "document_number": "2133-A"
}
```

**Видалити документ:**
```bash
DELETE /api/documents/{id}
```

**Перегенерувати chunks:**
```bash
POST /api/documents/{id}/reprocess
```

### Скрипти

**Тестування парсингу документа:**
```bash
python scripts/crawl_sumdu.py --url "https://normative.sumdu.edu.ua/..."
```

**Скидання бази даних:**
```bash
python scripts/init_db.py --drop
```

## 🏗️ Архітектура

```
┌─────────────────────────────────────────┐
│       CLIENT (HTTP Requests)            │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│         FastAPI (main.py)               │
│  - POST /api/query                      │
│  - GET/POST/PUT/DELETE /api/documents   │
│  - GET /health                          │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│         RAG Engine + SGR                │
│  1. Query → SGR (розуміння запиту)      │
│  2. Retrieval (пошук через pgvector)    │
│  3. SGR (структурування контексту)      │
│  4. Generation (Grok LLM)               │
│  5. Citation (формування джерел)        │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│      PostgreSQL + pgvector              │
│  - documents (метадані)                 │
│  - chunks (тексти + embeddings)         │
└─────────────────────────────────────────┘
```

## 📁 Структура проекту

```
rag-asistent/
├── config/               # Конфігурація
│   └── settings.py
├── src/
│   ├── api/             # FastAPI endpoints
│   │   ├── deps.py
│   │   └── routes/
│   ├── models/          # SQLAlchemy та Pydantic моделі
│   ├── db/              # База даних
│   ├── services/        # Бізнес-логіка
│   ├── rag/             # RAG Engine
│   ├── sgr/             # Schema-Guided Reasoning
│   ├── embeddings/      # Embeddings
│   └── utils/           # Утиліти
├── scripts/             # Допоміжні скрипти
├── data/                # Дані (не в git)
├── main.py              # Точка входу
└── TZ_ARCHITECTURE.txt  # Детальна документація
```

## 🛠️ Технології

- **Backend**: FastAPI, Uvicorn
- **AI/ML**: Pydantic AI, Grok API (LLM), Cohere API (embeddings)
- **Database**: PostgreSQL, pgvector, SQLAlchemy
- **Parsing**: Crawl4AI, BeautifulSoup4, pypdf
- **Other**: tiktoken, python-multipart

## 📖 Детальна документація

Детальне технічне завдання та архітектура описані в файлі `TZ_ARCHITECTURE.txt`.

## 🤝 Внесок

Це MVP-версія проекту. Будь-які покращення вітаються!

## 📝 Ліцензія

MIT License

## 🔗 Корисні посилання

- [Normative SumDU](https://normative.sumdu.edu.ua/)
- [Schema-Guided Reasoning](https://abdullin.com/schema-guided-reasoning/)
- [Crawl4AI](https://github.com/unclecode/crawl4ai)
- [Grok API](https://x.ai/api)
- [Cohere API](https://cohere.com/)
- [pgvector](https://github.com/pgvector/pgvector)
