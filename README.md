# Financial Assistant AI (Google ADK 2.0 + Supabase)

Персональний фінансовий асистент на базі офіційного фреймворку **[Google Agent Development Kit 2.0 (ADK)](https://adk.dev/2.0/)** та **Supabase (PostgreSQL)**, розроблений на Python з використанням менеджера пакетів **`uv`**.

Асистент аналізує виписки та файли обліку фінансів (CSV, XLSX: **Money Manager**, **Monobank**, **ПриватБанк**), зберігає історію з дедуплікацією (SHA-256) та відповідає на запитання щодо витрат за будь-які періоди через офіційний **Google ADK Web UI** або CLI.

---

## 🌟 Архітектура та можливості

- 🤖 **Google ADK 2.0 Core (`src/agent/agent.py`)**:
  - Канонічний `root_agent = Agent(...)` з моделлю Gemini.
  - Нативні інструменти ADK (**Function Calling**):
    - `ingest_financial_file`: Імпорт банківських файлів у сховище.
    - `query_transactions`: Пошук та фільтрація окремих транзакцій.
    - `get_period_summary`: Агрегація витрат, доходів та категорій.
    - `compare_periods`: Порівняння періодів (місяць-до-місяця MoM, рік-до-року YoY).
- 📊 **Універсальний парсер файлів (`src/parser/`)**:
  - Адаптери для **Money Manager**, **Monobank**, **ПриватБанк**.
  - Автоматичне визначення розділювачів та колонок.
  - SHA-256 дедуплікація повторних завантажень.
- 🗄️ **Supabase PostgreSQL (`src/db/`)**:
  - Схема бази даних з індексами часу та категорій (`src/db/schema.sql`).
  - Репозиторій агрегацій з автоматичним in-memory фолбеком для локальної розробки.
- 🖥️ **Офіційний Google ADK Web UI**:
  - Нативний інтерфейс для тестування, трасування стану, перегляду викликів інструментів та діалогу.

---

## 🚀 Швидкий старт

### 1. Встановлення залежностей через `uv`

```bash
uv sync
```

### 2. Налаштування змінних оточення

Створіть файл `.env` із `.env.example`:

```bash
cp .env.example .env
```

Заповніть ключ:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Запуск офіційного Google ADK Web UI

Ви можете запустити офіційний вебінтерфейс ADK будь-яким зі зручних способів:

```bash
# Через команду ADK CLI:
uv run adk web src/agent

# Або через скрипт запуску:
uv run python main.py
```

Після запуску відкрийте у браузері: **`http://localhost:8000`** (або порт, вказаний в терміналі).

### 4. Запуск у консольному режимі (ADK CLI)

```bash
uv run adk run src/agent
```

---

## 🧪 Автоматизовані тести

```bash
uv run pytest
```

---

## 📁 Структура проєкту

```
financial-assistant/
├── data/
│   └── samples/                     # Зразки тестових виписок (2025, 2026, Monobank)
├── src/
│   ├── agent/
│   │   ├── agent.py                 # Офіційний Google ADK 2.0 root_agent
│   │   ├── assistant.py             # ADK Runner та сервіс сесій
│   │   └── tools.py                 # Інструменти імпорту, фільтрації та аналітики
│   ├── db/
│   │   ├── client.py                # Supabase клієнт
│   │   ├── models.py                # Pydantic моделі та SHA-256 хешування
│   │   ├── repository.py            # Репозиторій транзакцій та аналітики
│   │   └── schema.sql               # PostgreSQL схема
│   ├── parser/
│   │   ├── engine.py                # Рушій парсингу CSV/XLSX
│   │   └── adapters/                # Адаптери (Money Manager, Monobank, ПриватБанк)
│   └── config.py                    # Конфігурація оточення
├── tests/                           # Комплект тестів pytest
├── main.py                          # Лаунчер Google ADK Web UI
├── pyproject.toml                   # Залежності проекту (uv)
└── README.md
```
