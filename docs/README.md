# Documentation

## Al-Huda Islamic AI Assistant - Documentation Hub

This directory contains all project documentation.

### Available Guides:
- **[UI/UX Enhancements](../UI_UX_ENHANCEMENTS_SUMMARY.md)** - Complete latest improvements
- **[Response Format Guide](../RESPONSE_FORMAT_GUIDE.md)** - Response formatting standards
- **[API Documentation](./API.md)** - API endpoint documentation
- **[Setup Guide](./SETUP.md)** - Installation and configuration

### Key Resources:
- **Vector Database Note**: The `vector_db.pkl` is automatically generated on first run
- **Database Folder**: Islamic texts are organized in the `DataBase/` directory
- **Uploads**: User profile images stored in `uploads/profiles/`

### Project Structure:
```
Al-Huda/
├── app/                    # Main application
│   ├── main.py            # Entry point
│   ├── api/               # API routes and models
│   ├── services/          # Business logic (AI, Vector DB, etc.)
│   ├── core/              # Configuration and logging
│   ├── static/            # Frontend assets (CSS, JS)
│   └── templates/         # HTML templates
├── docs/                  # Documentation
├── tests/                 # Unit tests (if applicable)
├── DataBase/              # Islamic books and resources
├── uploads/               # User-generated content
└── profiles/              # User profiles
```

### Running the Project:
See main README.md for setup and run instructions.
