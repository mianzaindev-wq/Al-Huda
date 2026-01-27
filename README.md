# Al-Huda: Islamic AI Assistant

Al-Huda is an advanced Islamic AI Assistant designed to provide accurate, verified information from the Quran and Hadith. It features a modern, responsive UI and uses a Retrieval-Augmented Generation (RAG) approach to ground its answers in authentic Islamic texts.

![Al-Huda Interface](app/static/img/screenshot.png) *(Note: Add a screenshot here later if available)*

## Features

- **Quran & Hadith Search:** Semantic search over authentic texts.
- **AI-Powered Chat:** Context-aware answers using Gemini AI.
- **Premium UI:** Modern, dark-mode compatible interface with beautiful typography.
- **Verification First:** Prioritizes authentic sources and clearly clearly cites references.

## Installation

### Prerequisites
- Python 3.8+
- [Google Gemini API Key](https://aistudio.google.com/apikey)

### Quick Start (Windows)

1.  Clone the repository:
    ```bash
    git clone https://github.com/yourusername/Al-Huda.git
    cd Al-Huda
    ```

2.  Run the auto-setup script:
    ```cmd
    setup.bat
    ```
    This script will:
    - Create a virtual environment
    - Install dependencies
    - Set up the `.env` file (you will need to paste your API key)
    - Download necessary models

3.  Start the application:
    ```cmd
    run.bat
    ```

### Manual Setup

1.  Create a virtual environment:
    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3.  Configure environment:
    Create a `.env` file in the root directory:
    ```env
    GEMINI_API_KEY=your_api_key_here
    ```

4.  Run the application:
    ```bash
    cd app
    python main.py
    ```

## Project Structure

- `app/`: Core application code (FastAPI/Flask).
- `DataBase/`: Source documents (PDFs, text files) for the knowledge base.
- `vector_db/`: Generated vector embeddings (not included in repo, generated on first run).
- `uploads/`: Temporary folder for user uploads.

## Contributing

1.  Fork the repository
2.  Create your feature branch (`git checkout -b feature/amazing-feature`)
3.  Commit your changes (`git commit -m 'Add some amazing feature'`)
4.  Push to the branch (`git push origin feature/amazing-feature`)
5.  Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
