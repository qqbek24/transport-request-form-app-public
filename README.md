# Transport Form App

> **Web application for managing transport requests at the Romanian border**  
> System automatically synchronizes data with SharePoint Excel and sends email notifications.

**Latest Features:**
-  **Async Parallel Upload** - 3x faster attachment processing (3 files simultaneously)
-  **MS Graph Email** - Automatic confirmation emails using same token as SharePoint
-  **Background Tasks** - Non-blocking submission (instant response to user)
-  **Excel API** - Works even when file is open by another user
-  **Token Manager** - Automatic token refresh, no manual copying needed

---

## Quick Start

### Docker (Recommended)

```powershell
# 1. Copy and configure .env
copy .env.example .env
notepad .env  # Set: RPA_BOT_PASSWORD=Your_Password

# 2. Start services
docker compose up --build

# 3. Open in browser
# Frontend: http://localhost:8011
# Backend:  http://localhost:8010/docs
```

### Jenkins Deployment

```
1. Jenkins → "transport-form-app" job
2. Build with Parameters:
   -  USE_TOKEN_MANAGER = true
   -  ACTION = deploy
3. Build
```

---

## Requirements

- **Docker** 20+ & Docker Compose
- **Jenkins** (production) with credentials: `webapp-transport-form-app`
- **Python** 3.11+ (optional - development without Docker)

---

## Token Manager - Automatic Tokens

**No need to manually copy SharePoint tokens anymore!**

Token Manager automatically:
- Fetches token from REST API on first use
- Caches token for 1 hour
- Auto-refreshes after expiration
- Fallback to manual token if API unavailable

**Configuration:** 
- File: `backend/config.yaml`
- Password: `RPA_BOT_PASSWORD` in `.env`
- Token status: http://localhost:8010/api/token/info

---

## Async Parallel Upload - High Performance

**NEW: Attachments upload 3x FASTER!**

Performance Improvements:
-  **Parallel upload**: 3 files simultaneously (ThreadPoolExecutor)
-  **Non-blocking**: User gets immediate response (~100-200ms)
-  **Background processing**: Uploads happen asynchronously
-  **No timeout**: Even with 10+ large attachments
-  **Smart order**: Excel saves FIRST (reliable), then attachments, then email

**Before vs After:**
```
BEFORE (synchronous):
5 files × 3s = 15s → User waits
10 files × 3s = 30s → TIMEOUT

AFTER (async parallel):
5 files / 3 workers = ~5s → User sees success immediately
10 files / 3 workers = ~10s → No timeout
```

**Technical Details:**
- Background task with FastAPI `BackgroundTasks`
- ThreadPoolExecutor with 3 workers
- Upload order: Excel → Attachments (parallel) → Excel update → Email
- Full attachment status tracking in email

---

## Email Confirmations - Automatic Notifications

**After each successful submission, user receives confirmation email!**

Email Features:
- Automatic email to user after successful submit
- Contains all form data (Request ID, delivery note, etc.)
- CC to configurable company address (in config.yaml)
- Professional HTML template with branding
- **Attachment status**: Success/Failed for each file
- Non-blocking: Doesn't fail submission if email fails
- **Uses MS Graph API - same token as SharePoint!** (no extra credentials)

**Configuration:**
- Method: **MS Graph API** (not SMTP)
- Token: Same as SharePoint (from Token Manager)
- Sender: `mail@yourdomain.com`
- CC Email: Configurable in `config.yaml` → `email.cc_email`
- Template: `backend/res/confirmation_email.html`
- **No extra passwords!** Uses existing token

**Required Azure AD permissions:**
- `Mail.Send` - for application/service principal
- Token Manager automatically fetches token with these permissions

**Disable emails:**
```yaml
# config.yaml
email:
  enabled: false  # Set to false to disable
```

---

## Project Structure

```
transport-form-app/
├── backend/              # FastAPI + Clean OOP Architecture
│   ├── fastapi_app.py   # Main application (~1100 lines)
│   ├── token_manager.py # Automatic token management
│   ├── sharepoint_helper.py  # SharePoint/MS Graph API
│   ├── logger_config.py # Structured logging
│   ├── config.yaml      # Configuration
│   ├── utils/           # Clean OOP helpers (~856 lines less!)
│   │   ├── transport_handler.py      # Main orchestrator
│   │   ├── scheduler_manager.py      # Background tasks
│   │   └── helpers/                  # Helper classes
│   │       ├── excel_helper.py       # Excel/SharePoint ops
│   │       ├── json_helper.py        # JSON backup
│   │       ├── email_helper.py       # MS Graph emails
│   │       └── attachment_helper.py  # Parallel uploads
│   ├── data/            # JSON backup
│   ├── logs/            # CSV + JSONL logs
│   └── res/             # Email templates
├── frontend/             # React + Vite
│   └── public/
│       ├── form-labels.json  # i18n-ready labels
│       └── locales/          # TODO: Multi-language support
├── nginx/                # Reverse proxy
├── tests/                # Tests (pytest + integration)
│   ├── test_*.py        # Test files
│   ├── pytest.ini       # pytest config
│   └── run_tests.ps1    # Test runner
├── jenkins/              # CI/CD pipelines
│   ├── jenkins-pipeline-complete.groovy
│   ├── jenkins-shutdown-pipeline.groovy
│   └── shutdown.sh
├── .env                  # MAIN (Docker)
├── docker-compose.yaml
└── TODO_INTERNATIONALIZATION.md  # i18n implementation plan
```

---

## Configuration

### 1. Environment Variables (`.env`)

```bash
# Token Manager (automatic tokens)
RPA_BOT_PASSWORD=Your_Password

# Fallback manual token (optional)
SHAREPOINT_ACCESS_TOKEN=

# Debug mode (optional)
DEBUG_SECRET_KEY=your-pass-secret-token
```

### 2. SharePoint & Email (`backend/config.yaml`)

```yaml
sharepoint:
  enabled: true
  folder_url: "https://your-url-address.sharepoint.com/sites/.../Shared Documents/..."
  excel_file_name: "transport_requests.xlsx"
  worksheet_name: "Transport Requests"
  use_excel_api: true  # Recommended - works on open files

email:
  enabled: true
  sender_email: "transport-app@yourdomain.com"  # From address (MS Graph)
  cc_email: "transport-requests@yourdomain.com"  # Configurable CC
  subject_template: "Transport Request Confirmation - {request_id}"
  # Uses MS Graph API with same token as SharePoint

paths:
  json_backup_file: "/tmp/transport_requests.json"  # Container filesystem (persistent)
  logs_dir: "/tmp/logs"  # Log directory in container
  attachments_dir: "./attachments"  # Local attachments folder
```

### 3. Jenkins Credentials (one-time setup)

```
ID: webapp-transport-form-app
Type: Username with password
Username: transport-form-app@yourdomain.com
Password: Your_Password
```

---

## Testing

```powershell
# Unit tests
pytest backend/ -v

# API test
python test_api_submit.py

# SharePoint test
python test_local_submit_sharepoint.py

# Coverage
pytest --cov=backend --cov-report=html

# Integration test (with attachments)
pytest tests/test_integration.py -v
```

---

## Monitoring

| Endpoint | Description |
|----------|-------------|
| `http://localhost:8010/health` | Health check |
| `http://localhost:8010/api/token/info` | SharePoint token status |
| `http://localhost:8010/api/sharepoint/status` | SharePoint connection status |
| `http://localhost:8010/docs` | API documentation (Swagger) |

**Application logs:**
```
backend/logs/
├── form_submissions_YYYYMMDD.csv   # Form submissions
└── transport_app_YYYYMMDD.jsonl    # Detailed logs
```

**JSON backup:**
```
/tmp/transport_requests.json  # Container filesystem
                               # Persistent across restarts via volume mount
```

---

## Troubleshooting

### Problem: Token Manager not working (401 error)

```powershell
# Check password in container
docker exec transport-form-app-request-backend-1 env | grep RPA_BOT_PASSWORD

# Test API manually
curl -X POST https://your-token-api.yourdomain.com/getaccesstoken `
  -d "email=transport-app@yourdomain.com" `
  -d "password=YourPassword123!" `
  -d "application=your-app-name"
```

### Problem: SharePoint error 423 (Locked)

Excel file is open - close it or use `use_excel_api: true` in `config.yaml`

### Problem: Timeout with many attachments

**FIXED** in latest version with async parallel upload! If still occurs:
- Check `max_workers=3` in `upload_single_attachment_sync()`
- Verify background task is not blocking
- Check logs for upload errors

### Problem: Duplicate JSON records

**FIXED**: JSON now saved only once in main endpoint, not in `save_to_excel()`

### Problem: Containers not starting

```powershell
docker compose down -v
docker compose up --build --force-recreate
```

---

## Internationalization (i18n)

**Current Status:** Partially implemented (form labels only)

- Form labels externalized: `frontend/public/form-labels.json`
- UI messages still hardcoded
- Email template in English only
- No language selector

**Roadmap:** See [TODO_INTERNATIONALIZATION.md](./TODO_INTERNATIONALIZATION.md) for:
- Complete i18n analysis (~360 texts)
- Implementation plan (3 phases)
- Locale file structure
- Library recommendations (react-i18next)
- Estimated effort: 5-6 hours

**Quick Preview:**
```json
// frontend/public/locales/en.json
{
  "app": {
    "title": "Transport Form App",
    "subtitle": "Please fill out the form below..."
  },
  "form": {
    "messages": {
      "submitSuccess": "Form submitted successfully! Request ID: {{requestId}}"
    }
  }
}
```

---

## Documentation

| File | Description |
|------|-------------|
| **[DEVELOPER.md](./DEVELOPER.md)** | Complete technical documentation for developers |
| **[TODO_INTERNATIONALIZATION.md](./TODO_INTERNATIONALIZATION.md)** | i18n implementation plan |
| `backend/config.yaml` | SharePoint, Email, Token Manager configuration |
| `.env.example` | Environment variables template |
| `TESTING.md` | Testing guide |
