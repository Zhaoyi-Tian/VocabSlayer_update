# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

VocabSlayer (万词斩) is a sophisticated vocabulary learning desktop application built with Python and PyQt5. The application features a modern Fluent Design interface and supports multi-user vocabulary learning with AI integration.

## Architecture

### Technology Stack
- **GUI Framework**: PyQt5 with qfluentwidgets (Fluent Design)
- **Database**: openGauss (PostgreSQL-compatible) via py-opengauss driver
- **Data Processing**: Pandas for data manipulation
- **AI Integration**: OpenAI API, DeepSeek AI
- **Build System**: PyInstaller for standalone executables
- **Visualization**: Matplotlib for charts and statistics

### Client-Server Architecture
```
client/         # PyQt5 GUI application
server/         # Database backend and business logic
├── database_manager.py    # Database abstraction layer
├── my_test.py            # Core vocabulary learning system
└── init_database.sql     # Database schema
```

### Key Components
- **Main Window**: Fluent Design interface with navigation
- **Learning Modes**: Routine Training, Review Training, AI-enhanced learning
- **Database**: 8 core tables with 606 vocabulary entries
- **User System**: Multi-user support with authentication and progress tracking

## Development Commands

### Build Application
```bash
# Build standalone executable
pyinstaller "万词斩.spec"

# The output will be in dist/万词斩.exe
```

### Database Operations
```bash
# Connect to database
gsql -d vocabulary_db -p 5432

# Initialize database
psql -h localhost -p 5432 -U vocabuser -d vocabulary_db -f server/init_database.sql

# Migrate data (if needed)
python server/migrate_opengauss.py
```

### Testing
```bash
# Run basic database connection test
python test.py

# Run optimization tests
python test_optimization.py
```

### Dependencies Management
```bash
# Install all dependencies
pip install -r requirements.txt

# Key dependencies include:
# - PyQt5==5.15.11
# - py-opengauss==1.3.10
# - PyQt-Fluent-Widgets[full]==1.9.1
# - pandas==2.3.3
```

## Database Configuration

The application uses openGauss database. Configuration is stored in `config.json`:

```json
{
    "database_type": "opengauss",
    "database_config": {
        "host": "localhost",
        "port": 5432,
        "database": "vocabulary_db",
        "user": "vocabuser",
        "password": "your_password"
    }
}
```

### Database Schema
- `vocabulary` - 606 vocabulary entries with English, Chinese, Japanese translations
- `users` - User authentication and profiles
- `user_learning_records` - Individual user progress
- `user_review_list` - Words for review with weight system
- `user_bookmarks` - User bookmarked words
- `user_daily_stats` - Daily performance statistics

## Code Structure Guidelines

### Entry Points
- `client/main.py` - Application launcher with login dialog
- `server/my_test.py` - Contains `VocabularyLearningSystem` class

### Database Access Pattern
Always use the `DatabaseFactory` to create database connections:
```python
from server.database_manager import DatabaseFactory
db = DatabaseFactory.from_config_file('config.json')
```

### UI Components
The application uses a modular widget system:
- `Home_Widget.py` - Dashboard
- `routine_training.py` - Standard quiz mode
- `Review_training.py` - Review system
- `ranking_widget.py` - Leaderboard
- `data_view_widget.py` - Statistics visualization

### AI Integration
AI features are implemented in:
- `client/deepseek.py` - DeepSeek AI integration
- OpenAI API for enhanced learning features

## Important Notes

### Database Migration
The project has been migrated from Excel/JSON storage to openGauss database. The `database_manager.py` provides abstraction with:
- `OpenGaussDatabase` - New database backend
- `ExcelDatabase` - Legacy support (deprecated)
- Factory pattern for easy switching

### Build Configuration
- PyInstaller spec file: `万词斩.spec`
- Console mode: Disabled (`console=False`)
- Icon: `client/resource/logo.png`
- Data files: `client/resource` directory included

### Development Environment
- Uses `.venv` virtual environment
- Requires Python 3.x
- Windows-focused (uses win32 specific features)
- VS Code settings included in `.vscode/`

## Common Development Tasks

### Adding New Vocabulary
Use the database migration script or directly manipulate the `vocabulary` table:
```sql
INSERT INTO vocabulary (english, chinese, japanese, level)
VALUES ('new_word', '翻译', '翻訳', 1);
```

### Adding New UI Pages
1. Create new widget class inheriting from PyQt5 widgets
2. Add navigation item in `main_window.py`
3. Register in the `NavigationInterface`

### Modifying Database Schema
1. Update `server/init_database.sql`
2. Run migration script on all environments
3. Update `DatabaseInterface` and implementations

### Testing Database Connection
```python
from server.database_manager import DatabaseFactory
db = DatabaseFactory.from_config_file('config.json')
db.connect()
print(f"Vocabulary count: {len(db.get_vocabulary())}")
db.close()
```