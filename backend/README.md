# Transport Request System - Backend Configuration

## Code Structure

Backend uses **clean OOP architecture** with helper classes:

### Main Application
- **fastapi_app.py** (~1100 lines) - FastAPI application with API endpoints
- **sharepoint_helper.py** - SharePoint/MS Graph API integration
- **token_manager.py** - Access token management
- **logger_config.py** - Structured logging configuration

### Utils Package (`backend/utils/`) - Clean OOP
**All logic encapsulated in classes - no procedural functions!**

#### Main Orchestrators:
- **transport_handler.py** - `TransportRequestHandler` - Main orchestrator for submissions
- **scheduler_manager.py** - `SchedulerManager` - Background tasks (sync, cleanup)

#### Helper Classes (`backend/utils/helpers/`):
- **excel_helper.py** - `ExcelHelper` - Excel/SharePoint operations
- **json_helper.py** - `JSONHelper` - JSON backup management
- **email_helper.py** - `EmailHelper` - Email sending via MS Graph API
- **attachment_helper.py** - `AttachmentHelper` - Parallel attachment uploads

**Benefits:**
- Single initialization - All helpers created once at startup
- No parameter passing - Helpers have config/logger/token access
- ~856 lines less code - Old handler files deleted
- Easy testing - Mock entire handler or individual helpers

See [utils/README.md](utils/README.md) for detailed documentation.

## Configuration Overview

Backend uses `config.yaml` file for path and settings configuration:

### **Local paths (Development):**
- **Attachments:** `./backend/attachments/`
- **Data:** `./backend/data/transport_requests.json` (JSON backup)

### **SharePoint paths (Production):**
- **Attachments:** `/Shared Documents/Attachments`
- **Excel:** `/Shared Documents/uit_generated_bot_follow_up.xlsx`

## **Data structure in Excel/JSON:**

```json
{
  "Request_ID": "REQ-20251021-201256-890",
  "Timestamp": "2025-10-21T20:12:56.890",
  "Delivery_Note_Number": "54455424",
  "Truck_License_Plates": "EL2222gggg", 
  "Trailer_License_Plates": "14554e1gdggf2333",
  "Carrier_Country": "Albania",
  "Carrier_Tax_Code": "sdfds4353535",
  "Carrier_Full_Name": "Transport_testy54454",
  "Border_Crossing": "Ostrov",
  "Border_Crossing_Date": "2025-10-22",
  "Has_Attachment": "Yes",
  "Attachment_Status": "Uploaded (3/3)"
}
```

## **Workflow (Async Parallel Upload):**

1. **Form submits data** → FastAPI endpoint `/api/submit`
2. **Backend generates Request ID** (format: `REQ-YYYYMMDD-HHMMSS-XXX`)
3. **Immediate response to user** (200 OK, ~100-200ms)
4. **Background task starts:**
   - Save to Excel (SharePoint) FIRST (data safety)
   - Upload attachments in PARALLEL (3 simultaneously via ThreadPoolExecutor)
   - Update Excel row with attachment status
   - Send confirmation email with MS Graph API
5. **JSON backup** → `backend/data/transport_requests.json`

**Performance:**
- 3 files: ~5s (parallel upload with 3 workers)
- 10 files: ~10s (no timeout!)
- User never waits - instant response

## **Configuration in config.yaml:**

```yaml
sharepoint:
  enabled: true
  folder_url: "https://yourcompany.sharepoint.com/sites/.../Shared Documents/..."
  excel_file_name: "uit_generated_bot_follow_up.xlsx"
  worksheet_name: "UIT generated"
  use_excel_api: true  # Recommended - works on open files

email:
  enabled: true
  sender_email: "transport-app@yourdomain.com"
  cc_email: "your.email@yourdomain.com"
  # Uses MS Graph API with same token as SharePoint
```

## **Latest Features:**

- **Async Parallel Upload** - 3x faster (ThreadPoolExecutor, max_workers=3)
- **Background Tasks** - Non-blocking (user gets instant response)
- **MS Graph Email** - Automatic confirmations with attachment status
- **Excel API** - Works even when file is open
- **Token Manager** - Automatic token refresh

## **Related Documentation:**

- **[Main README](../README.md)** - User documentation and quick start
- **[DEVELOPER.md](../DEVELOPER.md)** - Complete technical documentation
- **[DEBUG_MODE.md](../DEBUG_MODE.md)** - Debug mode configuration guide
```
