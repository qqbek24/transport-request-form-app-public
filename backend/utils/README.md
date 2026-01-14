# Utils Package

This package contains helper classes and managers for the Transport Request API using clean OOP architecture.

## Structure

```
backend/utils/
├── __init__.py                    # Package initialization
├── transport_handler.py           # Main orchestrator (TransportRequestHandler)
├── scheduler_manager.py           # Background scheduler (SchedulerManager)
└── helpers/                       # Helper classes (OOP)
    ├── __init__.py
    ├── excel_helper.py            # ExcelHelper - Excel/SharePoint operations
    ├── json_helper.py             # JSONHelper - JSON backup management
    ├── email_helper.py            # EmailHelper - Email sending via MS Graph
    └── attachment_helper.py       # AttachmentHelper - Attachment uploads
```

## Architecture - Clean OOP

**All logic is encapsulated in classes - no procedural functions!**

### TransportRequestHandler (Main Orchestrator)
Single entry point for all transport request operations.

**Key Methods:**
- `handle_submission()` - Process entire submission (Excel → Attachments → Email)
- `handle_attachments_background()` - Background attachment processing
- Automatically initializes ALL helper classes (Excel, JSON, Email, Attachments)

### SchedulerManager (Background Tasks)
Manages periodic background tasks using APScheduler.

**Key Methods:**
- `sync_json_to_sharepoint()` - Periodic sync of JSON backup to SharePoint
- `cleanup_old_attachments()` - Cleanup old attachments from SharePoint
- Full implementations (no delegation to old handler files)

### Helper Classes (OOP)

#### ExcelHelper
Handles Excel/SharePoint operations.
- `save_to_excel()` - Save request data to SharePoint Excel
- `update_attachment_status()` - Update attachment status in Excel
- `_save_via_excel_api()` - Excel API method (works with open files)
- `_save_via_traditional()` - Download/upload method with retry logic

#### JSONHelper
Manages JSON backup file operations.
- `save_initial_record()` - Save initial record with "Processing" status
- `update_attachment_status()` - Update attachment status in JSON
- `update_sync_status()` - Update SharePoint sync status
- `debug_info()` - Debug JSON backup file location

#### EmailHelper
Handles email operations via MS Graph API.
- `send_confirmation_email()` - Send confirmation email
- `parse_email_list()` - Parse semicolon-separated emails

#### AttachmentHelper
Manages attachment uploads to SharePoint.
- `upload_attachments_parallel()` - Parallel upload with ThreadPoolExecutor
- `upload_single_attachment()` - Single file upload

## Usage

**Single instance initialization in `fastapi_app.py`:**

```python
from utils.transport_handler import TransportRequestHandler
from utils.scheduler_manager import SchedulerManager

# Initialize ONCE at startup
transport_handler = TransportRequestHandler(
    config=config,
    logger_instance=logger,
    app_logger_instance=app_logger,
    performance_metrics_instance=performance_metrics,
    get_access_token_func=get_access_token
)

scheduler_manager = SchedulerManager(
    config=config,
    transport_config=transport_config,
    get_access_token_func=get_access_token,
    app_logger_instance=app_logger
)

# Use throughout the app
@app.post("/api/submit")
def submit(request: SubmitRequest, background_tasks: BackgroundTasks):
    result = transport_handler.handle_submission(
        data=request.dict(),
        background_tasks=background_tasks
    )
    return result
```

**Benefits:**
- ✅ **Single initialization** - All helpers created once, reused everywhere
- ✅ **No parameter passing** - Helpers have access to config/logger/token
- ✅ **Clean OOP** - No global variables, no procedural functions
- ✅ **Easy testing** - Mock entire handler or individual helpers
- ✅ **~856 lines less code** - Old handler files deleted

## Configuration

All classes are initialized with configuration at startup:
- `config` - Full configuration dict (dev/test/prod sections)
- `transport_config` - Transport-specific config from config.yaml
- `get_access_token_func` - Function to retrieve access token
- `logger` / `app_logger` - Logger instances
- `performance_metrics` - Performance tracking instance

## Testing

**Mock entire handler or individual helpers:**

```python
from unittest.mock import Mock, patch
from utils.transport_handler import TransportRequestHandler

def test_submission():
    # Mock dependencies
    mock_config = {...}
    mock_logger = Mock()
    mock_app_logger = Mock()
    mock_get_token = Mock(return_value="test_token")
    
    # Initialize handler
    handler = TransportRequestHandler(
        config=mock_config,
        logger_instance=mock_logger,
        app_logger_instance=mock_app_logger,
        get_access_token_func=mock_get_token
    )
    
    # Mock helper method
    with patch.object(handler.excel, 'save_to_excel'):
        result = handler.handle_submission(
            data={"deliveryNoteNumber": "TEST123", ...},
            background_tasks=Mock()
        )
        assert result["success"] == True
```

## Migration Notes

**Removed files (~856 lines):**
- ❌ `excel_handler.py` (488 lines) - Logic moved to `ExcelHelper` + `SchedulerManager`
- ❌ `json_handler.py` (78 lines) - Logic moved to `JSONHelper`
- ❌ `background_tasks.py` (290 lines) - Logic moved to `SchedulerManager`

**All logic is now in OOP classes - zero delegation to old handler files!**
```

## Refactoring Notes

This utils package was created to refactor the original `fastapi_app.py` which was over 2600 lines.

**Benefits:**
- ✅ Improved code organization (main file reduced to ~1000 lines)
- ✅ Separation of concerns
- ✅ Easier testing of individual modules
- ✅ Better maintainability
- ✅ Reusable utility functions

**Migration:**
All existing function calls in `fastapi_app.py` were updated to use utils modules while maintaining backward compatibility.
