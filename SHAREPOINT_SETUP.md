# SharePoint Integration Setup Guide

> **Complete guide for configuring SharePoint Excel synchronization and MS Graph API integration**

---

## Overview

This application integrates with SharePoint using **Microsoft Graph API** for:
- ✅ **Excel synchronization** - Automatic data insertion to SharePoint Excel
- ✅ **File uploads** - Attachment storage in SharePoint folders
- ✅ **Email notifications** - MS Graph API for confirmation emails
- ✅ **Token Manager** - Automatic token refresh (no manual copying needed!)

---

## Authentication Methods

### Method 1: Token Manager (Recommended - v2.0+)

**Automatic token fetching from REST API - No manual token copying!**

Token Manager automatically:
- ✅ Fetches token from REST API on first use
- ✅ Caches token for 1 hour
- ✅ Auto-refreshes after expiration
- ✅ Fallback to manual token if API unavailable

**Setup:**

#### Locally (Windows):
```powershell
# Create backend/.env file
cd backend
copy .env.example .env
notepad .env
```

**.env contents:**
```bash
# Token Manager (recommended)
RPA_BOT_PASSWORD=YourPassword123!

# Fallback manual token (optional)
SHAREPOINT_ACCESS_TOKEN=

# Debug mode (optional)
DEBUG_SECRET_KEY=TestPassword123!
```

#### On VM (Linux/Docker):
```bash
# Create .env in project root
cd /path/to/transport-request-app
nano .env
```

**.env contents:**
```bash
# Token Manager
RPA_BOT_PASSWORD=Your_Password

# Fallback manual token (optional)
SHAREPOINT_ACCESS_TOKEN=

# Debug mode (optional)
DEBUG_SECRET_KEY=your_debug_key
```

Docker Compose will automatically load variables from `.env`.

**Token Manager Configuration** in `backend/config.yaml`:
```yaml
token_manager:
  enabled: true  # Enable automatic token fetching
  api_url: "https://your-token-api.yourdomain.com/getaccesstoken"
  email: "transport-app@yourdomain.com"
  application_name: "your-app-name"
  token_lifetime_hours: 1  # Cache duration
```

**Test Token Manager:**
```bash
# Check token status
curl http://localhost:8010/api/token/info

# Force refresh
curl -X POST http://localhost:8010/api/token/refresh
```

---

### Method 2: Manual Token (Legacy - Fallback)

**Manual token from Azure Portal - for emergency use only**

If Token Manager is unavailable, you can use manual token:

#### Get Token from Azure Portal:
1. Open Azure Portal → Azure Active Directory
2. App Registrations → Find "your-app-name"
3. API Permissions → Ensure permissions: `Sites.ReadWrite.All`, `Files.ReadWrite.All`, `Mail.Send`
4. Certificates & Secrets → Generate new client secret
5. Copy access token

#### Set Manual Token:
```bash
# .env
RPA_BOT_PASSWORD=  # Leave empty
SHAREPOINT_ACCESS_TOKEN=eyJ0eXAiOiJK0000025jZSI6...  # Paste token here
```

**Note:** Manual tokens expire after ~60-90 minutes and must be regenerated manually.

---

## SharePoint Configuration

### 1. Excel API Method (Recommended - v2.0+)

**Works even when Excel file is open!**

Edit `backend/config.yaml`:

```yaml
default:
  transport:
    sharepoint:
      enabled: true  # Enable/disable integration
      use_excel_api: true  # Use Excel API (works on open files)
      
      # SharePoint folder URL (copy from browser)
      # Production path:
      folder_url: "https://yourtenant.sharepoint.com/sites/yoursite/Shared Documents/YourFolder"
      
      # Excel file name in folder
      excel_file_name: "transport_requests.xlsx"
      
      # Worksheet name in Excel file
      worksheet_name: "Transport Requests"
      
      # Form field → Excel column mapping
      # Fuzzy matching: case-insensitive, ignores spaces/hyphens/apostrophes
      column_mapping:
        deliveryNoteNumber: "Delivery note number"
        truckLicensePlates: "Truck license plate numbers"
        trailerLicensePlates: "Trailer license plate numbers"
        carrierCountry: "Carrier's country"
        carrierTaxCode: "Carrier's tax code"
        carrierFullName: "Full name of the carrier"
        borderCrossing: "Border crossing point in Romania"
        borderCrossingDate: "Date of crossing border in Romania"
        email: "Email"
        phoneNumber: "Phone Number"
        hasAttachment: "Has Attachment"
        attachmentStatus: "Attachment Status"
        attachmentError: "Attachment Error"
      
      # Automatic columns (added by system)
      auto_columns:
        request_id: "Request ID"
        # timestamp: "Time Spent"
        # processing_date: "Dispatch note date"
```

**Excel Requirements for Excel API:**
1. Open Excel file in SharePoint
2. Select data range
3. Insert → Table (or Ctrl+T)
4. Name the table (default: "Table1")
5. Save file

---

### 2. Download/Upload Method (Fallback)

**Legacy method - doesn't work on open files**

If Excel API is not available:

```yaml
sharepoint:
  use_excel_api: false  # Disable Excel API
  
  # Retry settings for locked files
  max_retries: 5  # Number of attempts if file is locked
  retry_wait_multiplier: 2  # Wait time: attempt × multiplier = seconds
```

**Limitations:**
- ❌ Doesn't work on open Excel files (error 423 Locked)
- ❌ Slower - downloads entire file, modifies, uploads back
- ❌ Race conditions with concurrent access

---

## Email Configuration

**Automatic confirmation emails using MS Graph API**

Edit `backend/config.yaml`:

```yaml
email:
  enabled: true  # Enable/disable emails
  sender_email: "transport-app@yourdomain.com"  # From address
  sender_name: "Transport System"
  cc_email: "transport-requests@yourdomain.com"  # CC address (configurable)
  subject_template: "Transport Request Confirmation - {request_id}"
  # Note: Uses same token as SharePoint (no additional password needed!)
```

**Required Azure AD Permissions:**
- `Mail.Send` - for sending emails
- `Sites.ReadWrite.All` - for SharePoint access
- `Files.ReadWrite.All` - for file uploads

**Email Template:**
Located at: `backend/res/confirmation_email.html`

**Disable emails:**
```yaml
email:
  enabled: false
```

---

## How It Works

### Complete Workflow (v2.1 - Async Parallel Upload):

1. **Form submission** → Frontend sends data to `/api/submit`
2. **Immediate response** → User receives 200 OK (~100-200ms)
3. **Background task starts:**
   - **Step 1:** Generate Request ID
   - **Step 2:** Save to Excel (SharePoint) FIRST (data safety)
   - **Step 3:** Upload attachments in PARALLEL (3 simultaneously via ThreadPoolExecutor)
   - **Step 4:** Update Excel row with attachment status
   - **Step 5:** Send confirmation email via MS Graph API
4. **JSON backup** → `backend/data/transport_requests.json`

**Performance:**
- 3 files: ~5s (parallel upload with 3 workers)
- 10 files: ~10s (no timeout!)
- User never waits - instant response

**Technical Details:**
- Background processing with FastAPI `BackgroundTasks`
- ThreadPoolExecutor with `max_workers=3`
- Upload order: Excel → Attachments (parallel) → Excel update → Email
- Full error handling and retry logic

---

## Testing

### Test 1: Token Manager Connection
```powershell
# Check token status
curl http://localhost:8010/api/token/info

# Expected response:
# {
#   "source": "token_manager",
#   "is_valid": true,
#   "token_age_minutes": 12
# }
```

### Test 2: SharePoint Connection
```powershell
# Test SharePoint connection
curl http://localhost:8010/api/sharepoint/status

# Expected response:
# {
#   "connected": true,
#   "site_name": "TRANSPORT",
#   "file_exists": true,
#   "worksheet_exists": true,
#   "use_excel_api": true
# }
```

### Test 3: Backend Unit Test
```powershell
cd backend
python test_sharepoint.py
```

### Test 4: Full Integration Test
```powershell
# Start application
docker compose up -d

# Open browser
# http://localhost:8011

# Fill form and submit
# Check Excel in SharePoint - should have new row
```

### Test 5: Email Test
```powershell
# Submit form with email address
# Check inbox for confirmation email
# Email should contain:
# - Request ID
# - Form data summary
# - Attachment status (if files uploaded)
```

---

## Monitoring

### Health Endpoints

```powershell
# Application health
curl http://localhost:8010/health

# Token status
curl http://localhost:8010/api/token/info

# SharePoint status
curl http://localhost:8010/api/sharepoint/status

# API documentation
# http://localhost:8010/docs
```

### Application Logs

**Location:**
```
backend/logs/
├── form_submissions_YYYYMMDD.csv   # Form submissions (CSV)
└── transport_app_YYYYMMDD.jsonl    # Detailed logs (JSONL)
```

**View logs:**
```powershell
# Locally
cat backend/logs/transport_app_20251205.jsonl

# In Docker
docker logs transport-request-form-app-backend-1 --tail=50

# Real-time logs
docker logs -f transport-request-form-app-backend-1
```

**Filter logs:**
```powershell
# All errors
Get-Content backend/logs/transport_app_20251205.jsonl | jq 'select(.level=="ERROR")'

# Token Manager events
Get-Content backend/logs/transport_app_20251205.jsonl | jq 'select(.message | contains("token"))'

# Specific request
Get-Content backend/logs/transport_app_20251205.jsonl | jq 'select(.request_id=="REQ-20251205-001")'
```

---

## Troubleshooting

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
- Verify password is correct
- Check if email/application are correct in `config.yaml`
- Verify REST API is accessible (VPN required?)
- Check if bot account is active in Azure AD

---

### Problem 2: Token Expired (401)

**Symptom:**
```
InvalidAuthenticationToken: Lifetime validation failed, the token is expired
```

**Solution with Token Manager:**
- Token Manager automatically refreshes on next request
- No manual action needed!

**Solution with Manual Token:**
- Generate new token in Azure Portal
- Update `.env` file
- Restart application: `docker compose restart backend`

---

### Problem 3: SharePoint 423 Locked

**Symptom:**
```
ERROR: SharePoint file locked (423)
```

**Cause:**
- Excel file is open in Excel Desktop/Online
- Using Download/Upload mode (`use_excel_api: false`)

**Solution:**
```yaml
# backend/config.yaml
sharepoint:
  use_excel_api: true  # ← Change to true!
```

Or close Excel file before synchronization.

---

### Problem 4: No Permissions (403 Forbidden)

**Symptom:**
```
ERROR: SharePoint API error: 403 Forbidden
```

**Solution:**
- Check if bot user (your-email@yourdomain.com) has edit permissions to SharePoint site
- Verify in SharePoint: Site Settings → Permissions → Check user access
- Required permissions: Contribute or Full Control
- Check Azure AD app permissions: `Sites.ReadWrite.All`, `Files.ReadWrite.All`

---

### Problem 5: Excel Table Not Found

**Symptom:**
```
ERROR: Table not found in worksheet
```

**Solution:**
1. Open Excel file in SharePoint
2. Select data range (including headers)
3. Insert → Table (or Ctrl+T)
4. Ensure "My table has headers" is checked
5. Name the table (right-click → Table → Table Name)
6. Update `config.yaml` if table name is not "Table1"

---

### Problem 6: Column Mapping Mismatch

**Symptom:**
```
WARNING: Column not found: "Delivery Note Number"
```

**Solution:**
- Check Excel column headers match `column_mapping` in `config.yaml`
- Fuzzy matching is case-insensitive and ignores spaces/hyphens
- Example: "Delivery note number" = "Delivery-Note-Number" = "DELIVERY NOTE NUMBER"
- Verify spelling and special characters

---

### Problem 7: Attachments Not Uploading

**Symptom:**
```
ERROR: Failed to upload attachment
```

**Diagnosis:**
```powershell
# Check attachment status in email or logs
docker logs transport-request-form-app-backend-1 | grep "attachment"
```

**Solution:**
- Check if attachments folder exists in SharePoint: `/TRANSPORT/attachments/`
- Verify bot has write permissions to folder
- Check file size limits (max 10MB per file)
- Review attachment error details in Excel column "Attachment Error"

---

### Problem 8: Email Not Sending

**Symptom:**
```
WARNING: Email send failed
```

**Solution:**
- Check if email is enabled: `email.enabled: true` in `config.yaml`
- Verify Azure AD app has `Mail.Send` permission
- Check sender email exists: `transport-app@yourdomain.com`
- Verify token has mail permissions (same token as SharePoint)
- Review logs for detailed error: `docker logs transport-request-form-app-backend-1 | grep "email"`

---

## 🛑 Disabling SharePoint

To temporarily disable integration while keeping application running:

```yaml
# backend/config.yaml
sharepoint:
  enabled: false  # Disable SharePoint
```

Application will work normally, saving only to local JSON backup:
- ✅ Form submission works
- ✅ JSON backup saved to `/tmp/transport_requests.json`
- ❌ No SharePoint sync
- ❌ No emails sent

**Re-enable:**
```yaml
sharepoint:
  enabled: true
```

---

## Related Documentation

- **[README.md](./README.md)** - User documentation and quick start
- **[DEVELOPER.md](./DEVELOPER.md)** - Complete technical documentation
- **[DEBUG_MODE.md](./DEBUG_MODE.md)** - Debug mode configuration
- **[TODO_INTERNATIONALIZATION.md](./TODO_INTERNATIONALIZATION.md)** - i18n implementation plan

---

## Useful Links

- **Microsoft Graph API Documentation:** https://docs.microsoft.com/graph/api/overview
- **SharePoint REST API:** https://docs.microsoft.com/sharepoint/dev/sp-add-ins/working-with-folders-and-files-with-rest
- **Azure AD App Registration:** https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps
