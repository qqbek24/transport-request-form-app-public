# 🔐 Debug Mode - Admin Guide

## What is Debug Mode?

Debug Mode provides access to:
- 📋 **Logs Viewer** - real-time application log viewing (JSONL format)
- 📄 **JSON Data Viewer** - view and manage `transport_requests.json` records
- 🔗 **SharePoint Status** - connection diagnostics and token validation
- 🧹 **Attachment Cleanup** - manual cleanup of old SharePoint files (90+ days)

**⚠️ IMPORTANT:** Debug features are hidden from regular users. Access requires knowledge of the secret key.

---

## How to Enable Debug Mode?

### 1. Generate Secret Key

On your local computer, run (in PowerShell or Python):

```powershell
# PowerShell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Example output:**
```
xK9vZmR3pL8qYnJ2tA50000000cE4fU7gT9hV3iD2j
```

**💾 SAVE THIS KEY** - you'll need it for every deploy!

---

### 2. Paste Key During Jenkins Build

When running Jenkins pipeline:

1. Find parameter **🔐 DEBUG_SECRET_KEY**
2. Paste your generated key there
3. **DO NOT SHARE THIS KEY WITH ANYONE!**

**If you leave the field empty → Debug mode will be disabled (production)**

---

### 3. Use Debug Mode

After application deployment:

1. Open application in browser
2. Add `?debug=true` to URL:
   ```
   https://localhost:8010/?debug=true
   ```

3. A popup will appear requesting the key:
   ```
   🔐 Debug Access
   Enter debug secret key to access logs and diagnostic tools:
   [●●●●●●●●●●●●●●●●●●●●]
   ✓ OK    ✖ Cancel
   ```

4. Enter your key (same as in Jenkins)

5. If correct → you'll see **📋 Logs** button in upper right corner

---

## 📋 Debug Features

### Logs Viewer
- **CSV Logs** - form submission history
- **JSONL Logs** - structured application logs with full context
- **Real-time filtering** - filter by date, request ID, error level
- **Download** - export logs for offline analysis
- **Multiple log files** - select and view historical logs by date

### JSON Data Viewer
- View all submissions stored in backup JSON
- Check synchronization status (`SharePoint_Synced`)
- Monitor failed sync attempts
- Verify data integrity
- **Delete records** - select and delete individual or multiple records
- **Total records count** - see how many submissions are stored

### SharePoint Status
- Connection test to SharePoint folder
- Token validation (Token Manager or certificate-based)
- Excel file accessibility check
- Table structure verification
- Access token format validation (JWT)
- Token expiration check

### Attachment Cleanup (NEW in v2.1)
- **Manual trigger** - cleanup old SharePoint attachments on demand
- **Retention period** - default 90 days (3 months), configurable in `config.yaml`
- **Safe deletion** - confirmation required before cleanup
- **Activity logs** - all cleanup operations logged with deleted file details
- **Config key:** `sharepoint_integration.attachment_retention_days`

---

## 🔒 Security

✅ **Key NOT visible in URL** (only `?debug=true`)  
✅ **Key NOT saved in browser history**  
✅ **Session token expires on tab close**  
✅ **Backend logs all access attempts**  
✅ **Without key → 403 Forbidden on all debug endpoints**  

---

## 🛠️ How to Disable Debug Mode?

In Jenkins **leave DEBUG_SECRET_KEY field empty** → debug features will be unavailable for everyone.

---

## 📌 Usage Examples

### ✅ Debug Mode Enabled (maintenance)
```bash
Jenkins parameters:
  USE_TOKEN_MANAGER: true
  RPA_BOT_PASSWORD: Your_Password
  DEBUG_SECRET_KEY: xK9vZmR3pL8qYnJ00000000B0cE4fU7gT9hV3iD2j  ← Your key
```

**Result:**
- You: Access `?debug=true` → popup → enter key → see Logs
- Other users: Don't see `?debug=true` in URL → normal application

---

### ❌ Debug Mode Disabled (production)
```bash
Jenkins parameters:
  USE_TOKEN_MANAGER: true
  RPA_BOT_PASSWORD: Your_Password
  DEBUG_SECRET_KEY:                                          ← Empty field
```

**Result:**
- Everyone (including you): No access to debug features, even with `?debug=true`

---

## 🔍 Troubleshooting

### Can't login to debug mode
- Check if key in Jenkins is identical to what you're entering
- Check DevTools Console (F12) for errors
- Backend logs will show authorization attempts: `🔒 Debug access denied (invalid key)`

### Logs button doesn't appear after entering key
- Refresh page (F5) and try again
- Check if `sessionStorage` works (private tab might block)
- Check in Console if token exists: `sessionStorage.getItem('debug_token')`

### Backend returns 403 Forbidden on /api/logs
- Session token invalid or expired
- Logout (close tab) and login again with `?debug=true`

### Can't see recent logs
- Logs are generated daily (filename contains date)
- Select correct date in Logs Viewer
- Check if container has write permissions to `/app/logs/`

---

## 📝 Access Logs

Backend logs all debug mode access attempts:

```json
{"level": "INFO", "message": "🔓 Debug access granted", "token": "a1b2c3d4..."}
{"level": "WARNING", "message": "🔒 Debug access denied (invalid key)"}
```

Check logs in **Logs Viewer** or directly in container:
```bash
docker exec transport-form-app-backend-1 tail -f /app/logs/transport_app_YYYYMMDD.jsonl
```

---

## 🔑 Environment Variable

Debug mode is controlled by environment variable:

```bash
# .env file
DEBUG_SECRET_KEY=xK9vZmR3pL8qY00000000B0cE4fU7gT9hV3iD2j
```

**Docker:**
```yaml
# docker-compose.yaml
environment:
  - DEBUG_SECRET_KEY=${DEBUG_SECRET_KEY}
```

**Verify in container:**
```powershell
docker exec transport-form-app-backend-1 env | grep DEBUG_SECRET_KEY
```

---

## 🧹 Attachment Cleanup Configuration

Configure retention period in `backend/config.yaml`:

```yaml
sharepoint_integration:
  enabled: true
  attachment_retention_days: 90  # Default: 3 months
```

**How it works:**
1. Manual trigger from Debug Mode (Logs Viewer toolbar)
2. Backend scans SharePoint `Attachments/` folder
3. Deletes files older than `retention_days`
4. All deletions logged to JSONL with file details

**Check cleanup logs:**
```powershell
# Search for cleanup events in logs
docker exec transport-form-app-backend-1 grep "Attachment cleanup" /app/logs/transport_app_*.jsonl
```

---

## 🎯 Summary

1. **Generate key** once (save it securely)
2. **Paste to Jenkins** on every deploy (only when you need debug)
3. **Use `?debug=true`** in browser + enter key
4. **Done** - you have access to all debug features!

**Remember:** Keep the key secret. Without it, no one has access to logs.

---

## 📚 Related Documentation

- **[DEVELOPER.md](./DEVELOPER.md)** - Full technical documentation
- **[README.md](./README.md)** - User documentation
- **Backend logs location:** `backend/logs/`
- **JSON backup location:** `backend/data/transport_requests.json`
