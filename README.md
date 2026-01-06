# Basidian - Second Brain App

A beautiful second brain application built with Flutter (frontend) and Python/FastAPI (backend).

## Features

- Create and edit daily notes
- Tree-like filesystem for organizing files
- Browse notes by date
- Search across all your notes
- Clean, minimalist interface
- Cross-platform (Android, iOS, Web, Desktop)
- SQLite database for data persistence

## Architecture

- **Frontend**: Flutter with Provider for state management
- **Backend**: Python with FastAPI for REST API
- **Database**: SQLite for data storage

## Getting Started

### Prerequisites

- Flutter SDK (3.32.8+)
- Python (3.12+)
- uv (Python package manager)
- Just (task runner)

### Running the Application

Using just:
```bash
just dev-local-linux   # Run backend + frontend (Linux)
just dev-local-android # Run backend + frontend (Android)
```

Or manually:

1. **Start the Backend**:
   ```bash
   cd backend
   uv sync
   uv run basidian-server serve --http=:8090
   ```

2. **Start the Frontend**:
   ```bash
   cd frontend
   flutter run
   ```

### API Endpoints

**Notes:**
- `GET /api/notes` - Get all notes
- `POST /api/notes` - Create a new note
- `GET /api/notes/{id}` - Get a specific note
- `PUT /api/notes/{id}` - Update a note
- `DELETE /api/notes/{id}` - Delete a note
- `GET /api/notes/date/{date}` - Get notes for a specific date
- `GET /api/search?q={query}` - Search notes

**Filesystem:**
- `GET /api/fs/tree` - Get filesystem tree
- `GET /api/fs/node` - Get node by path
- `POST /api/fs/node` - Create file/folder
- `PUT /api/fs/node/{id}` - Update node
- `DELETE /api/fs/node/{id}` - Delete node

**Daily Notes:**
- `GET /api/daily` - List all daily notes by year
- `GET /api/daily/{date}` - Get/create daily note
- `PUT /api/daily/{date}` - Update daily note
- `DELETE /api/daily/{date}` - Delete daily note

## Project Structure

```
basidian/
├── README.md
├── justfile                # Task runner commands
├── backend/                # Python/FastAPI REST API
│   ├── pyproject.toml
│   ├── src/basidian_server/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models.py
│   │   └── handlers/
│   │       ├── notes.py
│   │       ├── filesystem.py
│   │       └── daily.py
│   └── pb_data/
│       └── data.db
└── frontend/               # Flutter app
    ├── pubspec.yaml
    └── lib/
        ├── main.dart
        ├── models/
        ├── services/
        ├── screens/
        └── widgets/
```

## License

MIT License
