# Developer Documentation - Transport Form App

> **Complete technical documentation for developers**

---

## Table of Contents

1. [Architecture](#-architecture)
2. [Environment Setup](#-environment-setup)
3. [Running the Application](#-running-the-application)
4. [Token Manager](#-token-manager)
5. [.env Configuration](#-env-configuration)
6. [SharePoint Integration](#-sharepoint-integration)
7. [API Endpoints](#-api-endpoints)
8. [Testing](#-testing)
9. [Jenkins Deployment](#-jenkins-deployment)
10. [Debugging](#-debugging)
11. [Troubleshooting](#-troubleshooting)

---

## Architecture

### Tech Stack

| Component | Technology | Version |
|-----------|-------------|--------|
| **Backend** | FastAPI | Python 3.11+ |
| **Frontend** | React + Vite | 18.x |
| **SharePoint** | Microsoft Graph API | - |
| **Auth** | Token Manager (REST API) | Custom |
| **Container** | Docker + Docker Compose | 20+ |
| **CI/CD** | Jenkins | - |
| **Proxy** | Nginx | 1.25+ (dev only) |

### Application Structure

```
transport-request-form-app/
│
├── backend/                         # FastAPI Backend
│   ├── fastapi_app.py              # Main application (async background tasks)
│   ├── token_manager.py            # Automatic SharePoint token fetching
│   ├── sharepoint_helper.py        # Microsoft Graph API wrapper
│   ├── logger_config.py            # Structured logging (CSV + JSONL)
│   ├── config.yaml                 # Configuration (SharePoint, Token Manager, Email)
│   ├── requirements.txt            # Python dependencies (main)
│   ├── requirements_fastapi.txt    # FastAPI specific dependencies  
│   ├── requirements_test.txt       # Testing dependencies
│   ├── Dockerfile                  # Backend container
│   │
│   ├── attachments/                # User file uploads
│   ├── data/                       # JSON backup storage
│   │   └── transport_requests.json # Backup before SharePoint sync
│   ├── logs/                       # Application logs
│   │   ├── form_submissions_YYYYMMDD.csv    # Form submissions log
│   │   └── transport_app_YYYYMMDD.jsonl     # Structured JSON logs
│   ├── res/                        # Resources
│   │   └── confirmation_email.html # Email template
│   │
│   ├── utils/                      # Utility modules
│   │   ├── transport_handler.py    # Main transport request handler
│   │   ├── scheduler_manager.py    # Background scheduler for sync
│   │   └── helpers/                # Helper modules
│   │       ├── attachment_helper.py # File attachment operations
│   │       ├── email_helper.py      # Email sending via MS Graph
│   │       ├── excel_helper.py      # Excel/SharePoint operations
│   │       └── json_helper.py       # JSON backup operations
│   │
│   └── test/                       # Tests
│       ├── test_token_manager.py
│       └── test_sharepoint.py
│
├── frontend/                        # React Frontend
│   ├── src/
│   │   ├── App.jsx                 # Main component
│   │   ├── components/
│   │   │   ├── TransportForm.jsx   # Main form
│   │   │   └── StatusMessage.jsx   # Status display
│   │   └── utils/
│   │       └── api.js              # API client
│   ├── public/
│   │   ├── form-labels.json        # i18n-ready labels
│   │   └── locales/                # TODO: Translations
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile                  # Frontend container
│
├── nginx/                           # Reverse Proxy (dev mode only)
│   ├── nginx.conf                  # Production config
│   ├── nginx-dev.conf              # Development config (CORS support)
│   ├── Dockerfile
│   └── certs/                      # SSL certificates
│
├── .env                            # ⚠️ MAIN - Environment (Docker)
├── .env.example                    # Template
├── backend/.env                    # Optional - for Python direct
├── backend/.env.example            # Template
│
├── docker-compose.yaml             # Production compose
├── docker-compose.override.yaml    # Development overrides (nginx)
├── docker-compose.dev.yaml         # Alternative dev config
│
├── jenkins/                      # CI/CD pipelines
│   ├── jenkins-pipeline-complete.groovy # Main CI/CD pipeline
│   ├── jenkins-pipeline-fixed.groovy    # Fixed version
│   ├── jenkins-shutdown-pipeline.groovy
│   └── shutdown.sh
├── tests/                        # Test files
│   ├── test_*.py
│   ├── pytest.ini
│   ├── run_tests.ps1
│   └── run_tests.sh
│
├── README.md                       # User documentation
├── TESTING.md                      # Testing documentation
├── DEBUG_MODE.md                   # Debug mode documentation
├── SHAREPOINT_SETUP.md             # SharePoint setup guide
├── TODO_INTERNATIONALIZATION.md    # i18n implementation plan
└── DEVELOPER.md                    # ⬅️ THIS FILE
```

### Data Flow

```
User Browser
    ↓
Frontend (React) - http://localhost:8002 (production) / http://localhost:80 (dev with nginx)
    ↓ HTTP POST /api/submit (multipart/form-data with Base64 encoding)
Backend (FastAPI) - http://localhost:8010
    ↓
1. Generate Request ID
2. Immediate response to user (200 OK, ~100-200ms)
3. Background Task starts:
   ├─→ Token Manager → REST API → Access Token
   ├─→ Save to Excel (SharePoint) FIRST (data safety)
   ├─→ Upload attachments in PARALLEL (ThreadPoolExecutor, 3 workers)
   ├─→ Update Excel row with attachment status
   └─→ Send confirmation email (MS Graph API)
4. JSON Backup → backend/data/transport_requests.json
    ↓
SharePoint Excel (Your Company)
    ↓
Email Notifications (MS Graph API)
```

**Async Upload Architecture:**
- **Non-blocking**: User gets instant response
- **Parallel I/O**: 3 files upload simultaneously (ThreadPoolExecutor)
- **Safe order**: Excel FIRST (reliable data), then attachments, then email
- **Performance**: 5 files = ~5s (parallel) vs 15s (sequential)
- **Modular Design**: Separate helpers for Excel, Email, Attachments, JSON operations
  - `ExcelHelper` - SharePoint Excel operations (via MS Graph API)
  - `EmailHelper` - Email sending (via MS Graph API)
  - `AttachmentHelper` - File upload to SharePoint (parallel with ThreadPoolExecutor)
  - `JSONHelper` - JSON backup operations
  - `TransportRequestHandler` - Orchestrates all helpers in one place

---

## 💻 Environment Setup

### Requirements

- **Python:** 3.11+
- **Node.js:** 18+
- **Docker:** 20+
- **Git:** 2.0+
- **PowerShell:** 5.1+ (Windows)

### 1. Clone Repository

```powershell
git clone <repo-url> transport-request-form-app
cd transport-request-form-app
```

### 2. Python Virtual Environment

```powershell
# Create venv
python -m venv env

# Activate
.\env\Scripts\Activate.ps1

# Install dependencies
pip install -r backend/requirements.txt
pip install -r backend/requirements_test.txt  # For tests
```

### 3. Frontend Dependencies

```powershell
cd frontend
npm install
cd ..
```

### 4. Configure `.env` Files

**Step 1: Main `.env` (for Docker)**

```powershell
copy .env.example .env
notepad .env
```

```bash
# ========================================
# MAIN .env (for Docker Compose)
# ========================================

# Token Manager (automatic tokens)
RPA_BOT_PASSWORD=Your_Password

# Fallback manual token (optional)
SHAREPOINT_ACCESS_TOKEN=

# Debug mode (optional)
DEBUG_SECRET_KEY=Your_Debug_Password
```

**Step 2: Backend `.env` (for Python direct - optional)**

```powershell
copy backend\.env.example backend\.env
notepad backend\.env
```

```bash
# ========================================
# BACKEND .env (only for: python backend/fastapi_app.py)
# ========================================

# Token Manager
RPA_BOT_PASSWORD=Your_Password

# Fallback manual token
SHAREPOINT_ACCESS_TOKEN=

# Debug mode
DEBUG_SECRET_KEY=Your_Debug_Password
```

**⚠️ Important: Both files MUST have identical structure!**

### 5. SharePoint Configuration

Edit `backend/config.yaml`:

**Structure:** Config file has 4 branches: `dev`, `test`, `prod`, and `default`
- `default` - Always loaded, contains base configuration
- `dev/test/prod` - Environment-specific overrides (controlled by BOT_MODE env variable)
- Configuration is merged: default + environment-specific

**Example default configuration:**

```yaml
default:
  token_manager:
    enabled: true
    api_url: "https://your-token-api.yourdomain.com/getaccesstoken"
    email: "transport-app@yourdomain.com"
    application_name: "your-app-name"
    token_lifetime_hours: 1

  transport:
    sharepoint:
      enabled: true
      use_excel_api: true  # Recommended - works on open files
      
      # SharePoint folder URL (copy from browser)
      folder_url: "https://yourcompany.sharepoint.com/sites/transport/Shared Documents/General/All Documents/transport-app"
      
      # Excel file settings
      excel_file_name: "transport_requests.xlsx"
      worksheet_name: "Transport Requests"
      
      # Column mapping (fuzzy matching - ignores case/spaces/hyphens)
      column_mapping:
        deliveryNoteNumber: "Delivery note number"
        truckLicensePlates: "Truck license plate numbers"
        trailerLicensePlates: "Trailer license plate numbers"
        carrierCountry: "Carrier's country"
        carrierTaxCode: "Carrier's tax code"
        carrierFullName: "Full name of the carrier"
        borderCrossing: "Border crossing point in Romania"
        borderCrossingDate: "Date of crossing border in Romania"
        hasAttachment: "Has Attachment"
```

**Environment-specific overrides (dev/test/prod):**

```yaml
dev:
  # CC recipients for dev mode confirmation emails
  cc_email: "developer@yourdomain.com;your.email@gmail.com"

test:
  cc_email: "developer@yourdomain.com"

prod:
  cc_email: "transport-requests@yourdomain.com"
```

**Note:** Set `BOT_MODE` environment variable to switch between dev/test/prod. Default is `default` (production settings).

---

## 🚀 Running the Application

### Option 1: Docker Compose (Recommended)

#### Development Mode (with nginx proxy + CORS)

```powershell
# Start all containers (backend + frontend + nginx)
docker compose -f docker-compose.yaml -f docker-compose.override.yaml up --build

# Access:
# Nginx (Frontend+Backend):  http://localhost:80 (and https://localhost:443)
# Backend Direct:  http://localhost:8010/docs
# Frontend Direct: http://localhost:8002
```

**Why nginx in dev?**
- ✅ Solves CORS issues
- ✅ Simulates production environment
- ✅ Single entry point for frontend + backend

#### Production Mode (without nginx - direct ports)

```powershell
# Start only backend + frontend
docker compose up --build

# Access:
# Frontend: http://localhost:8002
# Backend:  http://localhost:8010/docs
```

#### Helper Commands

```powershell
# Stop all containers
docker compose down

# Stop + remove volumes (clears data)
docker compose down -v

# Restart single service
docker compose restart backend
docker compose restart frontend

# Real-time logs
docker compose logs -f backend
docker compose logs -f frontend

# Last 100 lines
docker compose logs --tail=100 backend

# Shell in container
docker exec -it transport-request-form-app-backend-1 bash
docker exec -it transport-request-form-app-frontend-1 sh

# Check environment variables
docker exec transport-request-form-app-backend-1 env

# Force rebuild without cache
docker compose build --no-cache
docker compose up --force-recreate
```

### Option 2: Direct Execution (Python + Node)

#### Backend (FastAPI)

```powershell
# Activate venv
.\env\Scripts\Activate.ps1

# Method 1: Python direct
cd backend
python fastapi_app.py
# Server: http://localhost:8000

# Method 2: Uvicorn with hot reload (development)
uvicorn fastapi_app:app --reload --host 0.0.0.0 --port 8000
# Server: http://localhost:8000/docs
```

#### Frontend (React)

```powershell
cd frontend

# Development server (hot reload)
npm run dev
# Server: http://localhost:3000

# Build production
npm run build
# Output: frontend/dist/

# Preview production build
npm run preview
# Server: http://localhost:4173
```

### Option 3: Hybrid (Backend Docker + Frontend Local)

```powershell
# Terminal 1: Backend in Docker
docker compose up backend

# Terminal 2: Frontend locally (hot reload)
cd frontend
npm run dev

# Frontend: http://localhost:3000 → Backend: http://localhost:8010
```

---

## 🔐 Token Manager

### Token Manager Architecture

Token Manager is a singleton class that automatically manages SharePoint tokens:

```python
# backend/token_manager.py

class TokenManager:
    """
    Singleton - one instance for entire application
    
    Features:
    - Automatic token fetching from REST API
    - 1-hour cache (configurable)
    - Automatic refresh when expired
    - Thread-safe
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_token(self) -> str:
        """
        Get SharePoint access token with caching
        
        Flow:
        1. Check cache - if valid and not expired, return cached token
        2. If expired - fetch new token from REST API
        3. Cache new token with timestamp
        4. Return token
        """
        
        # 1. Check cache
        if self._cached_token and not self._is_expired():
            logger.info("Using cached token")
            return self._cached_token
        
        # 2. Fetch new token
        logger.info("Token expired or not cached - fetching new token")
        token = self._fetch_token_from_api()
        
        # 3. Cache
        self._cached_token = token
        self._token_timestamp = datetime.now()
        
        return token
    
    def _fetch_token_from_api(self) -> str:
        """
        Fetch token from Company REST API
        
        API: https://your-token-api.yourdomain.com/getaccesstoken
        Method: POST
        Params:
            - email: transport-app@yourdomain.com
            - password: {RPA_BOT_PASSWORD}
            - application: your-app-name
        """
        
        response = requests.post(
            self.api_url,
            data={
                "email": self.email,
                "password": self.password,
                "application": self.application_name
            },
            verify=False  # SSL verification disabled (internal network)
        )
        
        data = response.json()
        return data.get("access_token")
```

### REST API Endpoint

**URL:** `https://your-token-api.yourdomain.com/getaccesstoken`

**Method:** `POST`

**Content-Type:** `application/x-www-form-urlencoded`

**Parameters:**
```
email: transport-app@yourdomain.com
password: YourPassword
application: your-app-name
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJub25jZSI6..."
}
```

**Token Format:** JWT (JSON Web Token)
**TTL:** ~60-90 minutes (managed by Azure AD)

### Usage in Code

**Universal Token Getter:**

```python
# backend/fastapi_app.py

def get_access_token() -> str:
    """
    Universal token getter - tries Token Manager, fallback to manual token
    
    Priority:
    1. Token Manager (if enabled in config.yaml)
    2. SHAREPOINT_ACCESS_TOKEN from .env (fallback)
    3. Raise error if both fail
    """
    
    # Option 1: Token Manager (automatic)
    if config.get('token_manager', {}).get('enabled', False):
        try:
            token = token_manager.get_token()
            if token:
                logger.info("Using token from Token Manager")
                return token
        except Exception as e:
            logger.warning(f"Token Manager failed: {e}, trying fallback")
    
    # Option 2: Manual token from .env (fallback)
    manual_token = os.getenv('SHAREPOINT_ACCESS_TOKEN', '').strip()
    if manual_token:
        logger.warning("Using manual token from .env (fallback mode)")
        return manual_token
    
    # Option 3: No token available
    raise ValueError("No access token available! Enable Token Manager or set SHAREPOINT_ACCESS_TOKEN")
```

**Usage in SharePoint operations:**

```python
# Before each SharePoint API call
access_token = get_access_token()
sharepoint = SharePointHelper(access_token)
sharepoint.insert_row_to_table(...)
```

### API Endpoints Token Manager

#### GET `/api/token/info`

Check current token status

**Request:**
```bash
curl http://localhost:8010/api/token/info
```

**Response:**
```json
{
  "token_manager": {
    "enabled": true,
    "config": {
      "api_url": "https://your-token-api.yourdomain.com/getaccesstoken",
      "email": "transport-app@yourdomain.com",
      "application_name": "your-app-name"
    }
  },
  "token": {
    "source": "token_manager",
    "expires_at": "2025-11-17T15:30:00",
    "is_valid": true,
    "token_age_minutes": 45,
    "token_preview": "eyJ0eXAiOiJKV1Qi..."
  }
}
```

**Fields:**
- `token_manager.enabled`: Whether Token Manager is active
- `token_manager.config`: Token Manager configuration
- `token.source`: `"token_manager"` or `"environment_variable"`
- `token.expires_at`: Token expiration time (estimate: current + 1h)
- `token.is_valid`: Whether token is valid
- `token.token_age_minutes`: Token age in minutes
- `token.token_preview`: First 50 characters of token

#### POST `/api/token/refresh`

Force fetch new token (ignores cache)

**Request:**
```bash
curl -X POST http://localhost:8010/api/token/refresh
```

**Response:**
```json
{
  "status": "success",
  "message": "Token refreshed successfully",
  "source": "token_manager"
}
```

### Token Manager Configuration

**File:** `backend/config.yaml`

```yaml
default:
  token_manager:
    enabled: true  # Enable/disable Token Manager
    api_url: "https://your-token-api.yourdomain.com/getaccesstoken"
    email: "transport-app@yourdomain.com"
    application_name: "your-app-name"
    token_lifetime_hours: 1  # Cache TTL (1 hour)
```

**Environment Variable:**

```bash
# .env or backend/.env
RPA_BOT_PASSWORD=Your_Password
```

### Testing Token Manager

#### Unit Test

```powershell
pytest backend/test/test_token_manager.py -v
```

#### Manual Test (curl)

```powershell
# Windows PowerShell
curl -X POST https://your-token-api.yourdomain.com/getaccesstoken `
  -d "email=transport-app@yourdomain.com" `
  -d "password=YourPassword" `
  -d "application=your-app-name"
```

#### Test via API endpoint

```powershell
# Check token status
curl http://localhost:8010/api/token/info

# Force refresh
curl -X POST http://localhost:8010/api/token/refresh

# Check if new token works
curl http://localhost:8010/api/sharepoint/status
```

---

## 📋 .env Configuration

### WHICH FILE TO USE?

```
transport-request-form-app/
├── .env                    ← MAIN (Docker Compose) ✅ ALWAYS USE THIS!
├── .env.example           ← Template
├── backend/
│   ├── .env               ← OPTIONAL (only Python without Docker)
│   └── .env.example       ← Template
```

### ✅ `.env` (main folder) - FOR DOCKER

**Location:** `transport-request-form-app/.env`

**When used:**
- ✅ `docker compose up` (production)
- ✅ `docker compose up` z override (development)
- ✅ Jenkins deployment

**Passed to:**
- Backend container (as environment variables)
- Frontend container (via build args - optional)

**Contents:**

```bash
# ========================================
# MAIN .env (for Docker Compose)
# ========================================

# ========================================
# TOKEN MANAGER (Recommended - automatic token refresh)
# ========================================
# RPA bot password for automatic token fetching from REST API
# Token Manager: enabled in backend/config.yaml
RPA_BOT_PASSWORD=YourPassword

# ========================================
# MANUAL TOKEN (Fallback - if Token Manager fails)
# ========================================
# Legacy: Manual SharePoint token (optional backup)
# Leave empty if using Token Manager
SHAREPOINT_ACCESS_TOKEN=

# ========================================
# DEBUG MODE (Optional)
# ========================================
# Secret key for access to debug endpoints (/api/debug/*)
DEBUG_SECRET_KEY=TestPassword
```

### ⚠️ `backend/.env` - OPTIONAL

**Location:** `transport-request-form-app/backend/.env`

**When used:**
- ⚠️ ONLY when running: `python backend/fastapi_app.py`
- ⚠️ ONLY local tests without Docker
- ⚠️ NOT used by Docker Compose!

**NOT used when:**
- ❌ `docker compose up`
- ❌ Jenkins deployment
- ❌ Production

**Contents (IDENTICAL to main .env!):**

```bash
# ========================================
# BACKEND .env (only for: python backend/fastapi_app.py)
# ========================================

# Token Manager
RPA_BOT_PASSWORD=Your_Password

# Fallback manual token
SHAREPOINT_ACCESS_TOKEN=

# Debug mode
DEBUG_SECRET_KEY=Your_Debug_Password
```

### 🔒 Security

**In Git:**
```gitignore
# .gitignore (already configured)
.env
backend/.env
```

**❌ NEVER COMMIT:**
- `.env` - contains passwords
- `backend/.env` - contains passwords
- Files with SharePoint tokens

**✅ COMMIT:**
- `.env.example` - template without passwords
- `backend/.env.example` - template without passwords

### 🔄 .env Synchronization

**Important:** Both files MUST have identical variable structure (only comments can differ)!

**Reason:** Application uses same logic whether running in Docker or locally.

```powershell
# Quick sync (PowerShell)
Copy-Item ".env" -Destination "backend\.env" -Force
```

### 📝 Creating .env from .env.example

```powershell
# Main .env
copy .env.example .env
notepad .env
# Fill in: RPA_BOT_PASSWORD=Your_Password

# Backend .env (optional - only for Python direct)
copy backend\.env.example backend\.env
notepad backend\.env
# Fill in: RPA_BOT_PASSWORD=Your_Password
```

---

## 📊 SharePoint Integration

### Microsoft Graph API

The application uses **Microsoft Graph API** to interact with SharePoint Excel:

**Base URL:** `https://graph.microsoft.com/v1.0`

**Authentication:** Bearer token (JWT) in `Authorization` header

**Endpoints used:**

| Endpoint | Method | Description |
|----------|--------|------|
| `/sites/{site-id}` | GET | Get SharePoint site information |
| `/drives/{drive-id}/root:/path/file.xlsx` | GET | Get Excel file metadata |
| `/drives/{drive-id}/items/{item-id}/workbook/worksheets` | GET | List worksheets in file |
| `/drives/{drive-id}/items/{item-id}/workbook/worksheets/{name}/tables` | GET | List tables in worksheet |
| `/drives/{drive-id}/items/{item-id}/workbook/tables/{table}/rows` | POST | Add row to table |
| `/drives/{drive-id}/items/{item-id}/content` | GET | Download Excel file (binary) |
| `/drives/{drive-id}/items/{item-id}/content` | PUT | Upload Excel file (binary) |

### Excel Write Methods

#### 1. Excel API (Recommended - `use_excel_api: true`)

**Advantages:**
- ✅ Works on open Excel files
- ✅ Fast - direct row insertion
- ✅ No file locking issues (error 423)
- ✅ Thread-safe

**Limitations:**
- ❌ Requires Excel formatted as **Table** (Insert → Table)
- ❌ More API calls (discover table → insert row)

**Implementation:**

```python
# backend/sharepoint_helper.py

def insert_row_to_table(self, worksheet_name: str, table_name: str, values: list):
    """
    Insert row directly into Excel table via Graph API
    
    Args:
        worksheet_name: Name of worksheet (e.g. "UIT generated")
        table_name: Name of Excel table (e.g. "Table1")
        values: List of values for new row
    """
    
    url = f"{self.graph_endpoint}/drives/{drive_id}/items/{item_id}/workbook/worksheets/{worksheet_name}/tables/{table_name}/rows"
    
    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        },
        json={"values": [values]}
    )
    
    if response.status_code == 201:
        logger.info(f"Row inserted successfully to table {table_name}")
    else:
        raise Exception(f"Failed to insert row: {response.text}")
```

**Excel Requirements:**
1. Select data in Excel
2. Insert → Table (or Ctrl+T)
3. Name the table (default "Table1")

#### 2. Download/Upload (Fallback - `use_excel_api: false`)

**Advantages:**
- ✅ Works on any Excel file (doesn't require Table format)
- ✅ Full control over formatting
- ✅ Can use openpyxl/xlwings for advanced operations

**Limitations:**
- ❌ Doesn't work on open files (error 423 Locked)
- ❌ Slower - downloads entire file + upload
- ❌ Race conditions with concurrent access

**Implementation:**

```python
def download_excel_file(self, file_path: str) -> bytes:
    """
    Download Excel file from SharePoint
    
    Retry logic for locked files (423 status)
    """
    max_retries = 3
    retry_multiplier = 5  # seconds
    
    for attempt in range(max_retries):
        try:
            response = self.download_file(file_path)
            return response
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 423:  # Locked
                wait_time = (attempt + 1) * retry_multiplier
                logger.warning(f"File locked, retry {attempt+1}/{max_retries} after {wait_time}s")
                time.sleep(wait_time)
            else:
                raise

def upload_excel_file(self, file_path: str, content: bytes):
    """Upload Excel file to SharePoint"""
    url = f"{self.graph_endpoint}/drives/{drive_id}/root:/{file_path}:/content"
    
    response = requests.put(
        url,
        headers={"Authorization": f"Bearer {self.access_token}"},
        data=content
    )
```

**Usage:**

```python
# Download
excel_bytes = sharepoint.download_excel_file("transport_requests.xlsx")

# Modify with openpyxl
wb = openpyxl.load_workbook(BytesIO(excel_bytes))
ws = wb["Transport Requests"]
ws.append(values)

# Upload back
output = BytesIO()
wb.save(output)
sharepoint.upload_excel_file("transport_requests.xlsx", output.getvalue())
```

### Fuzzy Column Matching

The application automatically matches column names form → Excel (case-insensitive, ignores spaces/hyphens):

```python
def fuzzy_match_columns(form_data: dict, excel_headers: list, mapping: dict) -> dict:
    """
    Fuzzy match form fields to Excel columns
    
    Example:
    - Form field: "deliveryNoteNumber"
    - Mapping: "Delivery note number"
    - Excel header: "delivery-note-number"
    → MATCH ✅
    
    Algorithm:
    1. Normalize: lowercase + remove non-alphanumeric
    2. Compare normalized strings
    """
    
    def normalize(text: str) -> str:
        return re.sub(r"[^a-z0-9]", "", text.lower())
    
    matched = {}
    for form_key, excel_column_name in mapping.items():
        normalized_target = normalize(excel_column_name)
        
        for header in excel_headers:
            if normalize(header) == normalized_target:
                matched[form_key] = header
                break
    
    return matched
```

### JSON Backup Mechanism

**Each submission is saved to JSON BEFORE sending to SharePoint**

**Reason:**
- ✅ Backup if SharePoint is down
- ✅ Ability for later synchronization via SchedulerManager
- ✅ Audit trail of all submissions

**Location:** `backend/data/transport_requests.json`

**Format:**

```json
[
  {
    "request_id": "TR-20251117-001",
    "timestamp": "2025-11-17T14:30:00.123456",
    "synced_to_sharepoint": true,
    "sync_attempts": 1,
    "last_sync_attempt": "2025-11-17T14:30:05",
    "data": {
      "deliveryNoteNumber": "DN123456",
      "truckLicensePlates": "ABC123, XYZ789",
      "trailerLicensePlates": "TR123",
      "carrierCountry": "Romania",
      "carrierTaxCode": "RO12345678",
      "carrierFullName": "Transport Company SRL",
      "borderCrossing": "Nadlac",
      "borderCrossingDate": "2025-11-17",
      "hasAttachment": "No"
    }
  }
]
```

**Note:** JSON backup is saved **immediately** on each submission. Background synchronization to SharePoint happens via scheduled task managed by SchedulerManager.

---

## 📡 API Endpoints

### Main Endpoints

#### POST `/api/submit`

Submit transport request form

**Request Body:**
```json
{
  "deliveryNoteNumber": "DN123456",
  "truckLicensePlates": "ABC123, XYZ789",
  "trailerLicensePlates": "TR123",
  "carrierCountry": "Romania",
  "carrierTaxCode": "RO12345678",
  "carrierFullName": "Transport Company SRL",
  "borderCrossing": "Nadlac",
  "borderCrossingDate": "2025-11-17",
  "email": "user@example.com",
  "phoneNumber": "+40123456789"
}
```

**Special Headers (WAF Bypass):**
```
X-Content-Type: application/json
X-Request-Source: web-form
X-Bypass-SQLI: true
X-Data-Encoding: base64  # Optional - if data is Base64 encoded
```

**Note:** Form data is sent as `multipart/form-data` where:
- `data` field contains JSON (optionally Base64 encoded to bypass WAF)
- `attachments[]` contains file uploads (optional)

**Response Success (200):**
```json
{
  "status": "success",
  "message": "Request submitted successfully",
  "request_id": "TR-20251117-001",
  "synced_to_sharepoint": true,
  "timestamp": "2025-11-17T14:30:00"
}
```

**Response Error (500):**
```json
{
  "status": "error",
  "message": "SharePoint sync failed: 401 Unauthorized",
  "request_id": "TR-20251117-001",
  "saved_to_json": true
}
```

#### GET `/` or `/api/health`

Health check endpoint

**Response (/):**
```json
{
  "message": "Transport backend running",
  "status": "healthy"
}
```

**Response (/api/health):**
```json
{
  "status": "healthy",
  "service": "transport-api",
  "version": "cors-fix-v2"
}
```

#### GET `/api/sharepoint/status`

Check SharePoint connection status

**Response:**
```json
{
  "connected": true,
  "site_name": "tests_priv",
  "file_exists": true,
  "file_path": "Shared Documents/General/All Documents/transport-app/transport_requests.xlsx",
  "worksheet_exists": true,
  "worksheet_name": "Transport Requests",
  "table_name": "Table1",
  "token_source": "token_manager",
  "use_excel_api": true
}
```

#### GET `/api/version`

Get application version and feature flags

**Response:**
```json
{
  "version": "2.1.0-utf8-fix",
  "features": {
    "json_backup": true,
    "debug_mode": true,
    "sharepoint_enabled": true,
    "base64_encoding": true,
    "utf8_support": true,
    "uri_decode": true
  },
  "paths": {
    "backend_dir": "/app",
    "cwd": "/app",
    "excel_file": "./data/transport_requests.xlsx"
  },
  "timestamp": "2025-12-23T14:30:00"
}
```

### Token Manager Endpoints

#### GET `/api/token/info`

Get current token status

**Response:**
```json
{
  "source": "token_manager",
  "expires_at": "2025-11-17T15:30:00",
  "is_valid": true,
  "token_age_minutes": 45,
  "token_preview": "eyJ0eXAiOiJKV1Qi..."
}
```

#### POST `/api/token/refresh`

Force token refresh (ignore cache)

**Response:**
```json
{
  "success": true,
  "message": "Token refreshed successfully",
  "token_preview": "eyJ0eXAiOiJKV1Qi...",
  "token_length": 2048,
  "timestamp": "2025-11-17T15:30:00"
}
```

### Debug Endpoints (require `DEBUG_SECRET_KEY`)

#### GET `/api/debug/enabled`

Check if debug mode is enabled

**Response:**
```json
{
  "debug_enabled": true,
  "has_debug_key": true
}
```

#### GET `/api/debug/logger-status`

Get logger status and configuration

**Response:**
```json
{
  "logger_initialized": true,
  "handlers_count": 2,
  "log_directory": "/app/logs",
  "json_backup_enabled": true
}
```

#### POST `/api/debug/verify`

Verify debug access with token

**Request:**
```json
{
  "token": "your_debug_token"
}
```

**Response:**
```json
{
  "valid": true,
  "message": "Debug access granted"
}
```

### Performance Metrics Endpoints (require debug token)

#### GET `/api/performance/metrics?token={debug_token}`

Get upload and submission performance statistics

**Response:**
```json
{
  "success": true,
  "metrics": {
    "upload_stats": {
      "total_uploads": 150,
      "successful_uploads": 145,
      "failed_uploads": 5,
      "avg_duration_seconds": 2.3,
      "avg_file_size_mb": 1.2,
      "recent_uploads": [
        {
          "timestamp": "2025-12-23T14:30:00",
          "request_id": "REQ-20251223-001",
          "filename": "document.pdf",
          "file_size_bytes": 1048576,
          "duration_seconds": 2.1,
          "success": true
        }
      ]
    },
    "submission_stats": {
      "total_submissions": 50,
      "successful_submissions": 48,
      "failed_submissions": 2,
      "submissions_with_attachments": 30,
      "avg_submission_duration_seconds": 5.2,
      "avg_attachments_per_submission": 2.5
    }
  },
  "timestamp": "2025-12-23T14:30:00"
}
```

#### POST `/api/performance/reset?token={debug_token}`

Reset all performance metrics

**Response:**
```json
{
  "success": true,
  "message": "Performance metrics have been reset",
  "timestamp": "2025-12-23T14:30:00"
}
```

---

## 🧪 Testing

### Unit Tests

```powershell
# All tests
pytest backend/ -v

# Specific module
pytest backend/test/test_token_manager.py -v
pytest backend/test/test_sharepoint.py -v

# With coverage
pytest --cov=backend --cov-report=html backend/
# Report in: htmlcov/index.html

# With output (print statements)
pytest backend/ -v -s
```

### Integration Tests

#### Test 1: API Submit

```powershell
python test_api_submit.py
```

**What it tests:**
- POST /api/submit with sample data
- Verify response status 200
- Check if request_id was generated

#### Test 2: SharePoint Integration

```powershell
python test_local_submit_sharepoint.py
```

**What it tests:**
- Full flow: Form → JSON → SharePoint
- Token Manager fetching
- Excel API insert row
- Fuzzy column matching

#### Test 3: Docker Container

```powershell
python test_docker_submit.py
```

**What it tests:**
- Submit to Docker container (http://localhost:8010)
- Verify backend works in Docker

### Manual API Testing (curl/PowerShell)

```powershell
# Health check
curl http://localhost:8010/health
# or
curl http://localhost:8010/api/health

# Version info
curl http://localhost:8010/api/version

# Token status
curl http://localhost:8010/api/token/info

# Token refresh
curl -X POST http://localhost:8010/api/token/refresh

# SharePoint status
curl http://localhost:8010/api/sharepoint/status

# Submit form (POST with JSON body)
$body = @{
    deliveryNoteNumber = "TEST-DN-001"
    truckLicensePlates = "ABC123"
    trailerLicensePlates = "TR123"
    carrierCountry = "Romania"
    carrierTaxCode = "RO12345678"
    carrierFullName = "Test Company SRL"
    borderCrossing = "Nadlac"
    borderCrossingDate = "2025-11-17"
} | ConvertTo-Json

curl -X POST http://localhost:8010/api/submit `
  -H "Content-Type: application/json" `
  -d $body
```

### Load Testing (optional)

```powershell
# Install locust
pip install locust

# Create locustfile.py
# (sample file in repo)

# Run test
locust -f locustfile.py --host=http://localhost:8010

# Open: http://localhost:8089
# Set: 10 users, 1 spawn rate
```

---

## 🚢 Deployment Jenkins

### Jenkins Pipeline Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ACTION` | Choice | `deploy` | `deploy` / `shutdown` / `restart` |
| `USE_TOKEN_MANAGER` | Boolean | `true` | Use Token Manager (recommended) |
| `MANUAL_SHAREPOINT_TOKEN` | String | - | Manual token (only when USE_TOKEN_MANAGER=false) |
| `DEBUG_SECRET_KEY` | String | - | Debug mode key (optional) |

### Jenkins Credentials Configuration (one-time)

**Step 1: Add credentials in Jenkins**

1. Jenkins Dashboard → Manage Jenkins → Credentials
2. Select domain: **(global)**
3. Add Credentials:
   - **Kind:** Username with password
   - **Scope:** Global
   - **Username:** `transport-app@yourdomain.com`
   - **Password:** `YourPassword123!`
   - **ID:** `webapp-transport-app` ⚠️ IMPORTANT - used in pipeline!
   - **Description:** `Transport WebApp - Token Manager password`

### Pipeline Flow

```groovy
// jenkins/jenkins-pipeline-complete.groovy

pipeline {
    agent any
    
    parameters {
        choice(name: 'ACTION', choices: ['deploy', 'shutdown', 'restart'], description: 'Action')
        booleanParam(name: 'USE_TOKEN_MANAGER', defaultValue: true, description: 'Use Token Manager')
        string(name: 'MANUAL_SHAREPOINT_TOKEN', defaultValue: '', description: 'Manual token (if Token Manager disabled)')
        string(name: 'DEBUG_SECRET_KEY', defaultValue: '', description: 'Debug key (optional)')
    }
    
    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: '<repo-url>'
            }
        }
        
        stage('Run Docker Container') {
            when {
                expression { params.ACTION == 'deploy' }
            }
            steps {
                dir('transport-request-form-app') {
                    script {
                        if (params.USE_TOKEN_MANAGER) {
                            // Token Manager mode - fetch password from Jenkins Credentials
                            withCredentials([usernamePassword(
                                credentialsId: 'webapp-transport-app',
                                usernameVariable: 'RPA_BOT_EMAIL',
                                passwordVariable: 'RPA_BOT_PASSWORD'
                            )]) {
                                // Create .env with password
                                def envContent = "RPA_BOT_PASSWORD=${RPA_BOT_PASSWORD}\n"
                                envContent += "SHAREPOINT_ACCESS_TOKEN=\n"  // Empty - Token Manager will fetch
                                
                                if (params.DEBUG_SECRET_KEY) {
                                    envContent += "DEBUG_SECRET_KEY=${params.DEBUG_SECRET_KEY}\n"
                                }
                                
                                writeFile file: '.env', text: envContent
                                echo '✅ .env created with Token Manager credentials'
                            }
                        } else {
                            // Legacy mode - manual token
                            def token = params.MANUAL_SHAREPOINT_TOKEN?.trim()
                            if (!token) {
                                error('❌ MANUAL_SHAREPOINT_TOKEN required when Token Manager disabled!')
                            }
                            
                            def envContent = "SHAREPOINT_ACCESS_TOKEN=${token}\n"
                            envContent += "RPA_BOT_PASSWORD=\n"
                            
                            writeFile file: '.env', text: envContent
                            echo '⚠️ .env created with manual token (legacy mode)'
                        }
                        
                        // Deploy
                        sh 'docker compose -f docker-compose.yaml up -d --build'
                        
                        // Wait for startup
                        sh 'sleep 10'
                        
                        // Verify
                        sh 'docker compose -f docker-compose.yaml ps'
                        
                        script {
                            if (params.USE_TOKEN_MANAGER) {
                                sh 'docker exec transport-request-backend-1 sh -c "[ -n \\"\\$RPA_BOT_PASSWORD\\" ] && echo \\"✅ RPA_BOT_PASSWORD is set\\" || echo \\"❌ RPA_BOT_PASSWORD not found\\""'
                            }
                        }
                    }
                }
            }
        }
        
        stage('Health Check') {
            when {
                expression { params.ACTION == 'deploy' }
            }
            steps {
                dir('transport-request') {
                    sh '''
                        echo "=== Container Status ==="
                        docker ps --filter name=transport-request-backend-1
                        
                        echo "=== Backend Health ==="
                        curl -f http://localhost:8010/health || exit 1
                        
                        echo "=== Frontend Check ==="
                        curl -f http://localhost:8002 || exit 1
                    '''
                }
            }
        }
        
        stage('Shutdown') {
            when {
                expression { params.ACTION == 'shutdown' }
            }
            steps {
                dir('transport-request') {
                    sh 'docker compose -f docker-compose.yaml down'
                }
            }
        }
    }
    
    post {
        success {
            echo '✅ Pipeline completed successfully'
        }
        failure {
            echo '❌ Pipeline failed'
        }
    }
}
```

### Deployment Steps (Manual)

**Step 1: Jenkins Job Setup**

1. Jenkins → New Item
2. Name: `transport-request`
3. Type: Pipeline
4. Pipeline Definition: Pipeline script from SCM
5. SCM: Git
6. Repository URL: `<repo-url>`
7. Script Path: `jenkins/jenkins-pipeline-complete.groovy`

**Step 2: Run Deployment**

1. Open job: `transport-request`
2. Click: **Build with Parameters**
3. Set parameters:
   - ACTION: `deploy`
   - ✅ USE_TOKEN_MANAGER: `true`
   - MANUAL_SHAREPOINT_TOKEN: (leave empty)
   - DEBUG_SECRET_KEY: (optional)
4. Click: **Build**

**Step 3: Verification**

```bash
# SSH to server
ssh user@jenkins-server

# Check containers
docker ps | grep transport-request-form-app

# Check logs
docker logs transport-request-form-app-backend-1 --tail=50

# Test health
curl http://localhost:8010/health

# Test token
curl http://localhost:8010/api/token/info
```

---

## 🐛 Debugging

### Application Logs

#### Location

```
backend/logs/
├── form_submissions_YYYYMMDD.csv    # Form submissions log (CSV format)
└── transport_app_YYYYMMDD.jsonl     # Structured application logs (JSONL)
```

#### CSV Log Format

**File:** `form_submissions_YYYYMMDD.csv`

**Columns:**
```csv
timestamp,request_id,delivery_note,truck_plates,carrier_country,status,error
2025-11-17T14:30:00,TR-20251117-001,DN123,ABC123,Romania,success,
2025-11-17T14:35:00,TR-20251117-002,DN456,XYZ789,Poland,error,"SharePoint 401"
```

**Usage:**
- Excel analysis
- Quick overview of form submissions
- Error tracking

#### JSONL Log Format

**File:** `transport_app_YYYYMMDD.jsonl`

**Format:** One JSON object per line

```json
{"timestamp": "2025-11-17T14:30:00.123", "level": "INFO", "message": "Form submission received", "request_id": "TR-20251117-001"}
{"timestamp": "2025-11-17T14:30:01.456", "level": "INFO", "message": "Token fetched from Token Manager", "token_age": "45min"}
{"timestamp": "2025-11-17T14:30:02.789", "level": "INFO", "message": "SharePoint sync successful", "request_id": "TR-20251117-001"}
{"timestamp": "2025-11-17T14:35:05.123", "level": "ERROR", "message": "SharePoint API error", "status_code": 401, "error": "Unauthorized"}
```

**Usage:**
- Structured log analysis (jq, grep)
- Detailed debugging
- Performance monitoring

**Examples:**

```powershell
# All errors
Get-Content backend/logs/transport_app_20251117.jsonl | jq 'select(.level=="ERROR")'

# Specific request
Get-Content backend/logs/transport_app_20251117.jsonl | jq 'select(.request_id=="TR-20251117-001")'

# Token Manager events
Get-Content backend/logs/transport_app_20251117.jsonl | jq 'select(.message | contains("token"))'
```

### Docker Logs

```powershell
# Real-time logs (follow)
docker compose logs -f backend
docker compose logs -f frontend

# Last 100 lines
docker compose logs --tail=100 backend

# Since timestamp
docker compose logs --since="2025-11-17T14:30:00" backend

# All services
docker compose logs

# Grep for errors
docker compose logs backend | Select-String "ERROR"
docker compose logs backend | Select-String "401\|403\|500"

# Export to file
docker compose logs backend > backend_logs.txt
```

### Debug Mode Endpoints

**Enable Debug Mode:**

```bash
# .env
DEBUG_SECRET_KEY=Your_Debug_Password
```

**Endpoints:**

```powershell
# Check if debug enabled
curl "http://localhost:8010/api/debug/enabled"

# Get logger status
curl "http://localhost:8010/api/debug/logger-status"

# Verify debug access
curl -X POST "http://localhost:8010/api/debug/verify" -H "Content-Type: application/json" -d '{"token":"Your_Debug_Token"}'
```

### Interactive Debugging

```powershell
# Shell in container
docker exec -it transport-request-backend-1 bash

# Python REPL in container
docker exec -it transport-request-backend-1 python

# Test token fetch
docker exec -it transport-request-backend-1 python -c "
from token_manager import TokenManager
tm = TokenManager()
print(tm.get_token()[:50])
"

# Check env variables
docker exec transport-request-form-app-backend-1 env | grep -E "RPA_BOT_PASSWORD|SHAREPOINT_ACCESS_TOKEN"

# File system check
docker exec transport-request-backend-1 ls -la /app/data/
docker exec transport-request-form-app-backend-1 ls -la /app/logs/
```

---

## 🔧 Troubleshooting

### Problem 1: Token Manager 401 Error

**Symptom:**
```
ERROR: Token Manager API error: 401 Unauthorized
```

**Diagnosis:**

```powershell
# 1. Check password in .env
cat .env | grep RPA_BOT_PASSWORD

# 2. Check password in container
docker exec transport-request-form-app-backend-1 env | grep RPA_BOT_PASSWORD

# 3. Test API manually
curl -X POST https://your-token-api.yourdomain.com/getaccesstoken `
  -d "email=transport-app@yourdomain.com" `
  -d "password=YourPassword123!" `
  -d "application=your-app-name"
```

**Solution:**

- Check if password is correct
- Check if email/application are correct in `config.yaml`
- Check if REST API is accessible (VPN?)

### Problem 2: SharePoint 423 Locked

**Symptom:**
```
ERROR: SharePoint file locked (423)
```

**Cause:**
- Excel file is open in Excel Desktop/Online
- Download/Upload mode (`use_excel_api: false`)

**Solution:**

```yaml
# backend/config.yaml
sharepoint:
  use_excel_api: true  # ← Change to true!
```

Or close Excel file before synchronization.

### Problem 3: SharePoint 401/403

**Symptom:**
```
ERROR: SharePoint API error: 401 Unauthorized
ERROR: SharePoint API error: 403 Forbidden
```

**Diagnosis:**

```powershell
# Check token status
curl http://localhost:8010/api/token/info

# Force refresh
curl -X POST http://localhost:8010/api/token/refresh

# Test SharePoint connection
curl http://localhost:8010/api/sharepoint/status
```

**Solution:**

- **401:** Token expired → Token Manager will automatically refresh on next request
- **403:** Lack of permissions → Check if transport-app@yourdomain.com has access to SharePoint

### Problem 4: Containers not starting

**Symptom:**
```
ERROR: Container exited with code 1
```

**Diagnosis:**

```powershell
# Container logs
docker compose logs backend

# Check if port is occupied
netstat -ano | findstr :8010
netstat -ano | findstr :8002
netstat -ano | findstr :80

# Check .env
cat .env
```

**Solution:**

```powershell
# Stop everything
docker compose down -v

# Rebuild from scratch
docker compose build --no-cache
docker compose up --force-recreate
```

### Problem 5: CORS Errors in Frontend

**Symptom:**
```
Access to XMLHttpRequest blocked by CORS policy
```

**Solution:**

Use development mode with nginx:

```powershell
docker compose -f docker-compose.yaml -f docker-compose.override.yaml up --build
```

Nginx will solve CORS (proxy between frontend and backend).

### Problem 6: JSON Backup not working

**Symptom:**
```
ERROR: Cannot write to data/transport_requests.json
```

**Diagnosis:**

```powershell
# Check permissions
docker exec transport-request-backend-1 ls -la /app/data/

# Check if folder exists
docker exec transport-request-backend-1 test -d /app/data && echo "EXISTS" || echo "NOT EXISTS"

# Check if file exists and is writable
docker exec transport-request-backend-1 test -w /app/data/transport_requests.json && echo "WRITABLE" || echo "NOT WRITABLE"
```

**Solution:**

The `data` folder is mounted as volume in docker-compose.yaml, so it should persist. If it doesn't exist:

```powershell
# Create data folder locally (will be mounted to container)
mkdir backend\data

# Restart container
docker compose restart backend
```

### Problem 7: Jenkins Credentials not working

**Symptom:**
```
ERROR: Credentials 'webapp-transport' not found
```

**Solution:**

1. Check if credentials exist:
   - Jenkins → Credentials → Check ID: `webapp-transport`

2. Check if ID in pipeline is correct:
   ```groovy
   credentialsId: 'webapp-transport'  // ← Must match!
   ```

3. Test credentials in pipeline:
   ```groovy
   withCredentials([usernamePassword(
       credentialsId: 'webapp-transport',
       usernameVariable: 'U',
       passwordVariable: 'P'
   )]) {
       sh 'echo "Username: $U"'
       sh 'echo "Password length: ${#P}"'
   }
   ```

---

## 📚 Additional Resources

### External Documentation

- **Microsoft Graph API:** https://learn.microsoft.com/en-us/graph/api/overview
- **FastAPI:** https://fastapi.tiangolo.com/
- **React:** https://react.dev/
- **Docker Compose:** https://docs.docker.com/compose/
- **Jenkins Pipeline:** https://www.jenkins.io/doc/book/pipeline/
- **Vite:** https://vitejs.dev/
- **Material-UI:** https://mui.com/

### Tools

- **Postman Collection:** `postman_collection.json` (in repo)
- **VS Code Extensions:**
  - Python
  - Docker
  - REST Client
  - YAML
