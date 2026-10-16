
# Sandhu Drive ☁️

A modern, responsive file-management web application built with Python and Flask. Sandhu Drive provides a simple interface for uploading, browsing, searching, previewing, downloading, renaming, and deleting files.

## ✨ Features

- Responsive interface for desktop, tablet, and mobile
- Multi-file upload
- Configured upload limit of up to 500 MB per file
- File categorization: images, documents, audio, video, and other files
- Search and category filtering
- File preview and download
- Rename and delete operations
- Storage usage and file-count statistics
- Duplicate filename handling
- Dark mode and interactive UI, when implemented in the frontend
- Automated tests with pytest
- Health-check endpoint for deployment monitoring

## 🛠️ Technology Stack

- Python
- Flask
- HTML
- CSS
- JavaScript
- pytest
- Gunicorn

## 📁 Project Structure

    SANDHU-DRIVE/
    ├── app.py
    ├── file_service.py
    ├── requirements.txt
    ├── pytest.ini
    ├── README.md
    ├── tests/
    │   ├── __init__.py
    │   ├── test_app.py
    │   └── test_file_service.py
    ├── templates/
    │   └── index.html
    └── storage/

## 🚀 Run Locally

### 1. Clone the repository

    git clone YOUR_GITHUB_REPOSITORY_URL
    cd SANDHU-DRIVE

Replace `YOUR_GITHUB_REPOSITORY_URL` with your actual repository URL.

### 2. Create a virtual environment

    python -m venv .venv

Activate it on Windows:

    .venv\Scripts\activate

### 3. Install dependencies

    pip install -r requirements.txt

### 4. Start the application

    python app.py

Open this address in your browser:

    http://127.0.0.1:5000

## 🧪 Run Tests

Run the complete automated test suite:

    pytest -v

Run only backend service tests:

    pytest tests/test_file_service.py -v

Run only Flask route tests:

    pytest tests/test_app.py -v

## 🔌 Available Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | File dashboard |
| POST | `/upload` | Upload files |
| GET | `/download/<name>` | Download a file |
| GET | `/preview/<name>` | Preview or safely download a file |
| POST | `/rename` | Rename a file |
| POST | `/delete` | Delete a file |
| POST | `/clear` | Clear workspace files |
| GET | `/api/stats` | Storage statistics |
| GET | `/health` | Health check |

## 💳 Membership Concept

The website can display three proposed plans:

- **Free:** 500 MB storage
- **Plus:** A proposed paid storage plan
- **Pro:** A proposed higher-capacity plan

Prices, storage quotas, payment processing, and membership enforcement must be configured before these plans are offered as real services. Displayed plans alone do not provide paid storage or payment functionality.

## 🔐 Privacy and Security

Sandhu Drive currently uses a local storage directory and does not implement user accounts or per-user access isolation.

Before public deployment, implement:

- Authentication and authorization
- Separate storage for each user
- CSRF protection for state-changing forms
- Secure session configuration
- Rate limiting and upload abuse controls
- Cloud or persistent storage with access controls
- Backup and recovery procedures
- Payment verification before activating paid plans

Do not store confidential files in a public deployment until these protections are implemented and tested.

The 500 MB application upload limit may also be restricted by the hosting provider, reverse proxy, or available memory and disk space.

## ☁️ Deployment

A production WSGI server can start the application with:

    gunicorn app:app

Configure the following environment variables where supported:

- `SECRET_KEY` — a long, random secret value
- `FILEFLOW_DATA_DIR` — persistent storage directory

For cloud deployment, configure persistent storage separately. Files saved to an ordinary container filesystem may be lost when the service restarts or redeploys.

## 👨‍💻 Developer

**Sandhu Drive**  
A Python and Flask file-management project.

- GitHub: Add your repository URL
- LinkedIn: Add your profile URL

## 📄 License

Choose and add a suitable open-source license before distributing this project.
