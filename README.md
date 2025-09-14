# Personal Assistant Bot API

A FastAPI-based personal assistant bot that integrates with Telegram for natural language task management, scheduling, and notifications.

## Project Structure

```
m.a.r.i.a.m/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app creation and configuration
│   ├── api/                       # API layer
│   │   ├── __init__.py
│   │   ├── main.py               # API router aggregation
│   │   ├── deps.py               # Dependency injection
│   │   └── routes/               # API endpoints
│   │       ├── __init__.py
│   │       ├── tasks.py          # Task management endpoints
│   │       ├── health.py         # Health check endpoints
│   │       ├── scheduler.py      # Scheduler management endpoints
│   │       └── test.py           # Testing endpoints
│   ├── core/                     # Core application configuration
│   │   ├── __init__.py
│   │   ├── config.py             # Application settings
│   │   ├── lifecycle.py          # Application startup/shutdown
│   │   └── setup_database.py     # Database setup utilities
│   ├── models/                   # Database models
│   │   ├── __init__.py
│   │   └── models.py             # SQLAlchemy models
│   ├── schemas/                  # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── tasks.py              # Task-related schemas
│   │   └── health.py             # Health check schemas
│   ├── services/                 # Business logic layer
│   │   ├── __init__.py
│   │   ├── telegram_service.py   # Telegram bot service
│   │   ├── openai_service.py     # OpenAI integration
│   │   ├── mnotify_service.py    # SMS/Voice notification service
│   │   └── scheduler_service.py  # Task scheduling service
│   └── utils/                    # Utility functions
│       └── __init__.py
├── tests/                        # Test files
├── docs/                         # Documentation
├── env/                          # Virtual environment
├── main.py                       # Application entry point
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variables template
├── .gitignore                    # Git ignore rules
└── README.md                     # This file
```

## Features

- **Natural Language Processing**: Uses OpenAI to parse natural language task descriptions
- **Telegram Integration**: Interactive bot for task management via Telegram
- **Smart Scheduling**: Automatic reminders via SMS and voice calls
- **RESTful API**: Complete FastAPI-based REST API
- **Database Integration**: SQLAlchemy with PostgreSQL support
- **Background Tasks**: APScheduler for automated task reminders

## Quick Start

### 1. Setup Environment
```bash
cd m.a.r.i.a.m
cp .env.example .env
```

Edit the `.env` file with your configuration:
```env
DATABASE_URL=postgresql://username:password@host:port/dbname
OPENAI_API_KEY=your_openai_api_key
TELEGRAM_BOT_TOKEN=8280809938:AAHqSXsk0pP4h0ZFaWuIxLYlbiEzMM0-JFQ
MNOTIFY_API_KEY=your_mnotify_api_key
YOUR_PHONE_NUMBER=0557782728
```

### 2. Install Dependencies
```bash
# Activate virtual environment (if exists)
source env/bin/activate  # Linux/Mac
# or
env\Scripts\activate.bat  # Windows

# Install requirements
pip install -r requirements.txt
```

### 3. Run the Application

**Option A: Using the startup script**
```bash
python start_bot.py
```

**Option B: Windows batch file**
```cmd
start_bot.bat
```

**Option C: Direct run**
```bash
python main.py
```

### 4. Test the Bot

**Telegram**: Message your bot at `t.me/Effe_ken_bot`

**API Documentation**: 
- OpenAPI docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

**Test SMS**: 
```bash
python test_sms.py
```

## Environment Variables

See `.env.example` for required configuration variables including:
- Database connection
- OpenAI API key
- Telegram bot token
- Mnotify SMS service credentials

## API Endpoints

- `GET /` - Root endpoint with API information
- `GET /health` - Health check with service status
- `GET /tasks` - Get user tasks
- `POST /tasks/create` - Create new task from natural language
- `POST /tasks/query` - Query tasks with natural language
- `PUT /tasks/{id}/complete` - Mark task as completed
- `DELETE /tasks/{id}` - Delete task
- `GET /scheduler/jobs` - Get scheduled jobs
- `POST /test/sms` - Test SMS functionality
- `POST /test/call` - Test voice call functionality

## Architecture

This project follows a clean architecture pattern with clear separation of concerns:

- **API Layer**: FastAPI routers and dependencies
- **Business Logic**: Service classes for external integrations
- **Data Layer**: SQLAlchemy models and database operations
- **Configuration**: Centralized settings management
- **Schemas**: Pydantic models for request/response validation