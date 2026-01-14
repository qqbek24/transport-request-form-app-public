import React, { useState } from 'react';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import SyncOutlinedIcon from '@mui/icons-material/SyncOutlined';
import FileDownloadOutlinedIcon from '@mui/icons-material/FileDownloadOutlined';
import CloseOutlinedIcon from '@mui/icons-material/CloseOutlined';
import DeleteSweepOutlinedIcon from '@mui/icons-material/DeleteSweepOutlined';
import CleaningServicesOutlinedIcon from '@mui/icons-material/CleaningServicesOutlined';
import StorageOutlinedIcon from '@mui/icons-material/StorageOutlined';
import CloudQueueIcon from '@mui/icons-material/CloudQueue';
import LogoDevOutlinedIcon from '@mui/icons-material/LogoDevOutlined';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CancelIcon from '@mui/icons-material/Cancel';
import AttachFileIcon from '@mui/icons-material/AttachFile';
import PendingIcon from '@mui/icons-material/Pending';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
import DescriptionOutlinedIcon from '@mui/icons-material/DescriptionOutlined';
import SpeedOutlinedIcon from '@mui/icons-material/SpeedOutlined';
import MenuIcon from '@mui/icons-material/Menu';
import './LogsViewer.css';

const LogsViewer = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isOpen, setIsOpen] = useState(false);
  const [logInfo, setLogInfo] = useState(null);
  const [expandedRows, setExpandedRows] = useState(new Set());
  const [sharepointStatus, setSharepointStatus] = useState(null);
  const [statusLoading, setStatusLoading] = useState(false);
  const [statusExpanded, setStatusExpanded] = useState(true);
  const [debugEnabled, setDebugEnabled] = useState(false);
  const [jsonData, setJsonData] = useState(null);
  const [jsonLoading, setJsonLoading] = useState(false);
  const [jsonExpanded, setJsonExpanded] = useState(true);
  const [showPasswordDialog, setShowPasswordDialog] = useState(false);
  const [secretKey, setSecretKey] = useState('');
  const [authError, setAuthError] = useState(null);
  const [debugToken, setDebugToken] = useState(null);
  const [clearLoading, setClearLoading] = useState(false);
  const [showSharePointBox, setShowSharePointBox] = useState(false);
  const [showJsonBox, setShowJsonBox] = useState(false);
  const [selectedRecords, setSelectedRecords] = useState(new Set());
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [logFiles, setLogFiles] = useState([]);
  const [selectedLogFile, setSelectedLogFile] = useState(null);
  const [cleanupLoading, setCleanupLoading] = useState(false);
  const [performanceMetrics, setPerformanceMetrics] = useState(null);
  const [metricsLoading, setMetricsLoading] = useState(false);
  const [metricsExpanded, setMetricsExpanded] = useState(true);
  const [showMetricsBox, setShowMetricsBox] = useState(false);
  const [resetLoading, setResetLoading] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Check URL params and session storage for debug mode on mount
  React.useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const debugParam = urlParams.get('debug');
    
    // Check if already authenticated in this session
    const storedToken = sessionStorage.getItem('debug_token');
    if (storedToken) {
      setDebugToken(storedToken);
      setDebugEnabled(true);
      console.log('%c✓ Debug mode: AUTHORIZED (session token found)', 'color: #28a745; font-weight: bold');
      return;
    }
    
    // If ?debug=true in URL, show password dialog
    if (debugParam === 'true') {
      setShowPasswordDialog(true);
      console.log('%cℹ Debug mode: Authentication required', 'color: #17a2b8; font-weight: bold');
    }
  }, []);

  const handleDebugAuth = async () => {
    setAuthError(null);
    
    try {
      const apiBaseUrl = getApiBaseUrl();
      const response = await fetch(`${apiBaseUrl}/api/debug/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ secret_key: secretKey })
      });
      
      if (response.ok) {
        const data = await response.json();
        sessionStorage.setItem('debug_token', data.token);
        setDebugToken(data.token);
        setDebugEnabled(true);
        setShowPasswordDialog(false);
        setSecretKey('');
        console.log('%c✓ Debug access granted', 'color: #28a745; font-weight: bold');
      } else {
        const error = await response.json();
        setAuthError(error.detail || 'Invalid secret key');
      }
    } catch (err) {
      setAuthError(`Network error: ${err.message}`);
    }
  };

  const handleCancelAuth = () => {
    setShowPasswordDialog(false);
    setSecretKey('');
    setAuthError(null);
  };

  const toggleRow = (index) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedRows(newExpanded);
  };

  const parseLogLine = (line) => {
    try {
      const parsed = JSON.parse(line);
      // Clean ANSI escape codes from message and other string fields
      // eslint-disable-next-line no-control-regex
      const ansiRegex = /\x1b\[\d+m/g;
      if (parsed.message) {
        parsed.message = parsed.message.replace(ansiRegex, '');
      }
      if (parsed.msg) {
        parsed.msg = parsed.msg.replace(ansiRegex, '');
      }
      return parsed;
    } catch {
      return null;
    }
  };

  const getApiBaseUrl = () => {
    let apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '';
    
    if (!apiBaseUrl) {
      // Check if running locally (Docker Desktop)
      if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        apiBaseUrl = 'http://localhost:8010';
      } else if (window.location.hostname.includes('yourdomain.com')) {
        apiBaseUrl = `${window.location.protocol}//${window.location.hostname}`;
      } else {
        apiBaseUrl = 'https://transport-app.yourdomain.com';
      }
    }
    
    return apiBaseUrl;
  };

  const fetchSharePointStatus = async () => {
    setStatusLoading(true);
    
    try {
      const apiBaseUrl = getApiBaseUrl();
      const response = await fetch(`${apiBaseUrl}/api/sharepoint/status`);
      const data = await response.json();
      
      console.log('%cℹ SharePoint Status:', 'color: #17a2b8; font-weight: bold', data);
      setSharepointStatus(data);
      setShowSharePointBox(true);
      setShowJsonBox(false); // Close JSON box when SharePoint opens
      setStatusExpanded(true);
      
      // Auto-close status after 30 seconds
      // setTimeout(() => setShowSharePointBox(false), 30000);
    } catch (err) {
      console.error('%c✗ SharePoint status check failed:', 'color: #dc3545; font-weight: bold', err);
      setSharepointStatus({
        error: `Network error: ${err.message}`,
        last_check: new Date().toISOString()
      });
      setShowSharePointBox(true);
    } finally {
      setStatusLoading(false);
    }
  };

  const fetchPerformanceMetrics = async () => {
    setMetricsLoading(true);
    
    try {
      const apiBaseUrl = getApiBaseUrl();
      const response = await fetch(`${apiBaseUrl}/api/performance/metrics?token=${debugToken}`);
      const data = await response.json();
      
      console.log('%cℹ Performance Metrics:', 'color: #17a2b8; font-weight: bold', data);
      setPerformanceMetrics(data);
      setShowMetricsBox(true);
      setShowSharePointBox(false); // Close SharePoint box
      setShowJsonBox(false); // Close JSON box
      setMetricsExpanded(true);
      
      // Auto-close after 30 seconds
      // setTimeout(() => setShowMetricsBox(false), 30000);
    } catch (err) {
      console.error('%c✗ Performance metrics fetch failed:', 'color: #dc3545; font-weight: bold', err);
      setPerformanceMetrics({
        success: false,
        error: `Network error: ${err.message}`,
        metrics: null
      });
      setShowMetricsBox(true);
    } finally {
      setMetricsLoading(false);
    }
  };

  const resetMetrics = async () => {
    if (!window.confirm('Are you sure you want to reset all performance metrics?')) {
      return;
    }
    
    setResetLoading(true);
    
    try {
      const apiBaseUrl = getApiBaseUrl();
      const response = await fetch(`${apiBaseUrl}/api/performance/reset?token=${debugToken}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      const data = await response.json();
      
      console.log('%c✓ Metrics Reset:', 'color: #28a745; font-weight: bold', data);
      
      if (data.success) {
        // Refresh metrics after reset
        await fetchPerformanceMetrics();
      } else {
        alert(`Failed to reset metrics: ${data.error || 'Unknown error'}`);
      }
    } catch (err) {
      console.error('%c✗ Metrics reset failed:', 'color: #dc3545; font-weight: bold', err);
      alert(`Network error: ${err.message}`);
    } finally {
      setResetLoading(false);
    }
  };

  const handleCleanupAttachments = async () => {
    if (!confirm('⚠ Are you sure you want to cleanup old SharePoint attachments?\n\nThis will delete all attachments older than the configured retention period (default: 3 months).\n\nThis action cannot be undone!')) {
      return;
    }
    
    setCleanupLoading(true);
    
    try {
      const apiBaseUrl = getApiBaseUrl();
      const response = await fetch(`${apiBaseUrl}/api/cleanup/trigger`);
      const data = await response.json();
      
      if (data.success) {
        console.log('%c✓ Attachment cleanup triggered successfully', 'color: #28a745; font-weight: bold');
        alert('✓ Attachment cleanup completed successfully!\n\nCheck the logs for details about deleted files.');
        // Refresh logs to see cleanup activity
        fetchLogs(100);
      } else {
        console.error('%c✗ Cleanup failed:', 'color: #dc3545; font-weight: bold', data.error);
        alert(`✗ Cleanup failed: ${data.error || 'Unknown error'}`);
      }
    } catch (err) {
      console.error('%c✗ Cleanup request failed:', 'color: #dc3545; font-weight: bold', err);
      alert(`✗ Network error during cleanup: ${err.message}`);
    } finally {
      setCleanupLoading(false);
    }
  };

  const handleDeleteSelected = async () => {
    if (selectedRecords.size === 0) {
      alert('No records selected');
      return;
    }

    const confirmMsg = `Are you sure you want to delete ${selectedRecords.size} selected record(s)?\nThis action cannot be undone.`;
    if (!window.confirm(confirmMsg)) return;

    setDeleteLoading(true);
    try {
      const apiBaseUrl = getApiBaseUrl();
      const requestIds = Array.from(selectedRecords);
      
      const response = await fetch(`${apiBaseUrl}/api/data/json/delete?token=${debugToken}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ request_ids: requestIds })
      });
      
      const result = await response.json();
      
      if (result.success) {
        console.log(`%c✓ Deleted ${result.deleted_count} records`, 'color: #28a745; font-weight: bold');
        setSelectedRecords(new Set());
        // Refresh JSON data
        await fetchJsonData();
      } else {
        alert(`Delete failed: ${result.error}`);
      }
    } catch (err) {
      console.error('%c✗ Delete failed:', 'color: #dc3545; font-weight: bold', err);
      alert(`Delete failed: ${err.message}`);
    } finally {
      setDeleteLoading(false);
    }
  };

  const handleSelectAll = (checked) => {
    if (checked && jsonData?.records) {
      const allIds = new Set(jsonData.records.map(r => r.Request_ID).filter(id => id));
      setSelectedRecords(allIds);
    } else {
      setSelectedRecords(new Set());
    }
  };

  const handleSelectRecord = (requestId, checked) => {
    const newSelected = new Set(selectedRecords);
    if (checked) {
      newSelected.add(requestId);
    } else {
      newSelected.delete(requestId);
    }
    setSelectedRecords(newSelected);
  };

  const fetchJsonData = async () => {
    setJsonLoading(true);
    
    try {
      const apiBaseUrl = getApiBaseUrl();
      const response = await fetch(`${apiBaseUrl}/api/data/json?token=${debugToken}`);
      const data = await response.json();
      
      console.log('%cℹ JSON Data:', 'color: #17a2b8; font-weight: bold', data);
      setJsonData(data);
      setShowJsonBox(true);
      setShowSharePointBox(false); // Close SharePoint box when JSON opens
      setJsonExpanded(true);
      
      // Auto-close after 30 seconds
      // setTimeout(() => setShowJsonBox(false), 30000);
    } catch (err) {
      console.error('%c✗ JSON data fetch failed:', 'color: #dc3545; font-weight: bold', err);
      setJsonData({
        success: false,
        error: `Network error: ${err.message}`
      });
      setShowJsonBox(true);
    } finally {
      setJsonLoading(false);
    }
  };

  const fetchLogs = async (lines = 100, fileToLoad = null) => {
    setLoading(true);
    setError(null);
    
    try {
      const apiBaseUrl = getApiBaseUrl();
      const targetFile = fileToLoad !== null ? fileToLoad : selectedLogFile;
      const url = targetFile 
        ? `${apiBaseUrl}/api/logs?lines=${lines}&token=${debugToken}&filename=${encodeURIComponent(targetFile)}`
        : `${apiBaseUrl}/api/logs?lines=${lines}&token=${debugToken}`;
      const response = await fetch(url);
      const data = await response.json();
      
      console.log('%cℹ Logs API Response:', 'color: #17a2b8; font-weight: bold', data);
      
      if (data.success) {
        // Parse JSONL format (one JSON per line)
        const logLines = data.logs.split('\n').filter(line => line.trim());
        console.log('%cℹ Log lines:', 'color: #17a2b8; font-weight: bold', logLines.length);
        const parsedLogs = logLines.map(line => parseLogLine(line)).filter(log => log !== null);
        console.log('%c✓ Parsed logs:', 'color: #28a745; font-weight: bold', parsedLogs.length, parsedLogs);
        setLogs(parsedLogs);
        setLogInfo({
          lines_returned: data.lines_returned,
          total_lines: data.total_lines,
          log_file: data.log_file
        });
      } else {
        setError(data.message || data.error || 'Failed to fetch logs');
        setLogs([]);
      }
    } catch (err) {
      setError(`Network error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const fetchLogFiles = async () => {
    try {
      const apiBaseUrl = getApiBaseUrl();
      const response = await fetch(`${apiBaseUrl}/api/logs/files?token=${debugToken}`);
      const data = await response.json();
      
      console.log('%cℹ Log Files:', 'color: #17a2b8; font-weight: bold', data);
      
      if (data.success && data.files.length > 0) {
        setLogFiles(data.files);
      }
    } catch (err) {
      console.error('%c✗ Failed to fetch log files:', 'color: #dc3545; font-weight: bold', err);
    }
  };

  const handleOpen = () => {
    setIsOpen(true);
    fetchLogFiles();
    fetchLogs(100);
  };

  const handleClose = () => {
    setIsOpen(false);
    setLogs([]);
    setError(null);
    setLogInfo(null);
    setExpandedRows(new Set());
  };

  const handleRefresh = () => {
    fetchLogs(100);
  };

  const handleDownload = () => {
    const logsText = logs.map(log => JSON.stringify(log)).join('\n');
    const blob = new Blob([logsText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `app_logs_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.jsonl`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleClearLogs = async () => {
    if (!confirm('⚠ Are you sure you want to clear all application logs? This action cannot be undone!')) {
      return;
    }
    
    setClearLoading(true);
    
    try {
      const apiBaseUrl = getApiBaseUrl();
      const response = await fetch(`${apiBaseUrl}/api/logs/clear?token=${debugToken}`, {
        method: 'DELETE'
      });
      const data = await response.json();
      
      console.log('%cℹ Clear Logs Response:', 'color: #17a2b8; font-weight: bold', data);
      
      if (data.success) {
        alert(`✓ ${data.message}\n\nCleared files:\n${data.cleared_files.join('\n')}`);
        setLogs([]);
        setLogInfo(null);
      } else {
        alert(`✗ Failed to clear logs: ${data.error || data.message}`);
      }
    } catch (err) {
      console.error('%c✗ Clear logs failed:', 'color: #dc3545; font-weight: bold', err);
      alert(`✗ Network error: ${err.message}`);
    } finally {
      setClearLoading(false);
    }
  };

  const getLevelColor = (level) => {
    switch(level?.toLowerCase()) {
      case 'error': return '#ff4444';
      case 'warning': return '#ffaa00';
      case 'success': return '#28a745';
      case 'info': return '#00aaff';
      case 'debug': return '#888888';
      default: return '#ffffff';
    }
  };

  const renderExpandedContent = (log) => {
    const formData = log.form_data;
    
    if (formData) {
      return (
        <div className="expanded-form-data">
          <h4><DescriptionOutlinedIcon fontSize="small" sx={{verticalAlign: 'middle', mr: 0.5}} /> Form Submission Details</h4>
          <div className="form-data-grid">
            <div className="form-field">
              <label>Request ID:</label>
              <span>{log.request_id || 'N/A'}</span>
            </div>
            <div className="form-field">
              <label>Delivery Note:</label>
              <span>{formData.delivery_note || formData.deliveryNoteNumber || 'N/A'}</span>
            </div>
            <div className="form-field">
              <label>Truck Plates:</label>
              <span>{formData.truck_plates || formData.truckLicensePlates || 'N/A'}</span>
            </div>
            <div className="form-field">
              <label>Trailer Plates:</label>
              <span>{formData.trailer_plates || formData.trailerLicensePlates || 'N/A'}</span>
            </div>
            <div className="form-field">
              <label>Carrier Country:</label>
              <span>{formData.carrier_country || formData.carrierCountry || 'N/A'}</span>
            </div>
            <div className="form-field">
              <label>Carrier Tax Code:</label>
              <span>{formData.carrier_tax_code || formData.carrierTaxCode || 'N/A'}</span>
            </div>
            <div className="form-field">
              <label>Carrier Name:</label>
              <span>{formData.carrier_name || formData.carrierFullName || 'N/A'}</span>
            </div>
            <div className="form-field">
              <label>Border Crossing:</label>
              <span>{formData.border_crossing || formData.borderCrossing || 'N/A'}</span>
            </div>
            <div className="form-field">
              <label>Crossing Date:</label>
              <span>{formData.crossing_date || formData.borderCrossingDate || 'N/A'}</span>
            </div>
            <div className="form-field">
              <label>Email:</label>
              <span>{formData.email || 'N/A'}</span>
            </div>
            <div className="form-field">
              <label>Phone Number:</label>
              <span>{formData.phone_number || formData.phoneNumber || 'N/A'}</span>
            </div>
            <div className="form-field">
              <label>Has Attachment:</label>
              <span className={log.attachment?.has_attachment ? 'badge-yes' : 'badge-no'}>
                {log.attachment?.has_attachment ? (
                  <><CheckCircleIcon fontSize="small" sx={{verticalAlign: 'middle', mr: 0.5}} /> Yes</>
                ) : (
                  <><CancelIcon fontSize="small" sx={{verticalAlign: 'middle', mr: 0.5}} /> No</>
                )}
              </span>
            </div>
            <div className="form-field">
              <label>SharePoint Saved:</label>
              <span className={log.sharepoint?.saved ? 'badge-yes' : 'badge-no'}>
                {log.sharepoint?.saved ? (
                  <><CheckCircleIcon fontSize="small" sx={{verticalAlign: 'middle', mr: 0.5}} /> Yes</>
                ) : (
                  <><CancelIcon fontSize="small" sx={{verticalAlign: 'middle', mr: 0.5}} /> No</>
                )}
              </span>
            </div>
            {log.sharepoint?.error && (
              <div className="form-field full-width">
                <label>SharePoint Error:</label>
                <span className="error-text">{log.sharepoint.error}</span>
              </div>
            )}
            {log.attachment?.filename && (
              <div className="form-field full-width">
                <label>Attachment:</label>
                <span className="filename">{log.attachment?.filename}</span>
              </div>
            )}
          </div>
        </div>
      );
    }
    
    // Fallback - show raw log data
    return (
      <div className="expanded-raw-data">
        <pre>{JSON.stringify(log, null, 2)}</pre>
      </div>
    );
  };

  return (
    <>
      {showPasswordDialog && (
        <div className="debug-auth-overlay" onClick={handleCancelAuth}>
          <div className="debug-auth-dialog" onClick={(e) => e.stopPropagation()}>
            <h3><LockOutlinedIcon fontSize="small" sx={{verticalAlign: 'middle', mr: 0.5}} /> Debug Access</h3>
            <p>Enter debug secret key to access logs and diagnostic tools:</p>
            <input
              type="password"
              value={secretKey}
              onChange={(e) => setSecretKey(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleDebugAuth()}
              placeholder="Enter secret key..."
              className="debug-password-input"
              autoFocus
            />
            {authError && (
              <div className="debug-auth-error">
                ✗ {authError}
              </div>
            )}
            <div className="debug-auth-buttons">
              <button onClick={handleDebugAuth} className="debug-auth-ok">
                ✓ OK
              </button>
              <button onClick={handleCancelAuth} className="debug-auth-cancel">
                ✗ Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {debugEnabled && (
        <Tooltip title="View Application Logs" arrow placement="left">
          <IconButton 
            className="logs-viewer-button" 
            onClick={handleOpen}
            sx={{ 
              position: 'fixed',
              bottom: '20px',
              right: '20px',
              left: 'auto',
              '@media (min-width: 1200px)': {
                left: 'calc(50% + 450px)',
                right: 'auto',
              },
              backgroundColor: 'rgba(255, 255, 255, 0.25)',
              backdropFilter: 'blur(8px)',
              color: '#2d1b69',
              width: '56px',
              height: '56px',
              borderRadius: '12px',
              border: '2px solid rgba(45, 27, 105, 0.4)',
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)',
              '&:hover': {
                backgroundColor: 'rgba(255, 255, 255, 0.35)',
                borderColor: 'rgba(45, 27, 105, 0.6)',
                transform: 'scale(1.05)',
              },
              transition: 'all 0.2s ease',
              zIndex: 999
            }}
          >
            <LogoDevOutlinedIcon sx={{ fontSize: 36 }} />
          </IconButton>
        </Tooltip>
      )}

      {isOpen && (
        <div className="logs-viewer-overlay" onClick={handleClose}>
          <div className="logs-viewer-modal" onClick={(e) => { e.stopPropagation(); setMobileMenuOpen(false); }}>
            <div className="logs-viewer-header" onClick={(e) => e.stopPropagation()}>
              <h2>Application Logs</h2>
              
              {/* Hamburger menu button - visible only on mobile */}
              <IconButton 
                className="hamburger-menu-button"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                sx={{ 
                  display: 'none',
                  '@media (max-width: 768px)': {
                    display: 'flex'
                  },
                  color: '#333'
                }}
              >
                <MenuIcon />
              </IconButton>

              <div className={`logs-viewer-controls ${mobileMenuOpen ? 'mobile-menu-open' : ''}`}>
                <Tooltip title="View JSON data file" arrow>
                  <IconButton 
                    onClick={() => { fetchJsonData(); setMobileMenuOpen(false); }}
                    disabled={jsonLoading}
                    className="icon-button json-data-button"
                    color="warning"
                  >
                    <StorageOutlinedIcon />
                    <span className="mobile-menu-label">JSON Data</span>
                  </IconButton>
                </Tooltip>
                
                <Tooltip title="Check SharePoint connection status" arrow>
                  <IconButton 
                    onClick={() => { fetchSharePointStatus(); setMobileMenuOpen(false); }} 
                    disabled={statusLoading} 
                    className="icon-button sharepoint-button"
                    sx={{ color: '#6f42c1' }}
                  >
                    <CloudQueueIcon />
                    <span className="mobile-menu-label">SharePoint Status</span>
                  </IconButton>
                </Tooltip>
                
                <Tooltip title="Cleanup old SharePoint attachments (requires confirmation)" arrow>
                  <IconButton 
                    onClick={() => { handleCleanupAttachments(); setMobileMenuOpen(false); }} 
                    disabled={cleanupLoading} 
                    className="icon-button cleanup-button"
                    sx={{ color: '#fd7e14' }}
                  >
                    <CleaningServicesOutlinedIcon />
                    <span className="mobile-menu-label">Cleanup Attachments</span>
                  </IconButton>
                </Tooltip>
                
                <Tooltip title="View performance metrics" arrow>
                  <IconButton 
                    onClick={() => { fetchPerformanceMetrics(); setMobileMenuOpen(false); }}
                    disabled={metricsLoading}
                    className="icon-button metrics-button"
                    sx={{ color: '#28a745' }}
                  >
                    <SpeedOutlinedIcon />
                    <span className="mobile-menu-label">Performance Metrics</span>
                  </IconButton>
                </Tooltip>
                
                <Tooltip title="Refresh logs" arrow>
                  <IconButton 
                    onClick={() => { handleRefresh(); setMobileMenuOpen(false); }} 
                    disabled={loading} 
                    className="icon-button refresh-button"
                    color="success"
                  >
                    <SyncOutlinedIcon />
                    <span className="mobile-menu-label">Refresh</span>
                  </IconButton>
                </Tooltip>
                
                <Tooltip title="Download logs" arrow>
                  <IconButton 
                    onClick={() => { handleDownload(); setMobileMenuOpen(false); }} 
                    disabled={!logs || loading} 
                    className="icon-button download-button"
                    color="info"
                  >
                    <FileDownloadOutlinedIcon />
                    <span className="mobile-menu-label">Download</span>
                  </IconButton>
                </Tooltip>
                
                <Tooltip title="Clear all log files (requires confirmation)" arrow>
                  <IconButton 
                    onClick={() => { handleClearLogs(); setMobileMenuOpen(false); }} 
                    disabled={clearLoading || loading} 
                    className="icon-button clear-logs-button"
                    sx={{ color: '#ff6b35' }}
                  >
                    <DeleteSweepOutlinedIcon />
                    <span className="mobile-menu-label">Clear Logs</span>
                  </IconButton>
                </Tooltip>
                
                <Tooltip title="Close" arrow>
                  <IconButton 
                    onClick={() => { handleClose(); setMobileMenuOpen(false); }} 
                    className="icon-button close-button"
                    sx={{ 
                      color: '#dc3545',
                      '&:hover': { backgroundColor: 'rgba(220, 53, 69, 0.1)' }
                    }}
                  >
                    <CloseOutlinedIcon />
                    <span className="mobile-menu-label">Close</span>
                  </IconButton>
                </Tooltip>
              </div>
            </div>
            
            {sharepointStatus && showSharePointBox && (
              <div className={`sharepoint-status-box ${sharepointStatus.error ? 'status-error' : 'status-success'}`}>
                <div className="status-header" onClick={() => setStatusExpanded(!statusExpanded)}>
                  <h3><CloudQueueIcon fontSize="small" sx={{verticalAlign: 'middle', mr: 0.5}} /> SharePoint Integration Status</h3>
                  <div className="header-buttons">
                    <Tooltip title="Close" arrow>
                      <IconButton 
                        size="small"
                        className="status-close-icon-btn" 
                        onClick={(e) => { e.stopPropagation(); setShowSharePointBox(false); }}
                        sx={{ 
                          color: '#dc3545',
                          '&:hover': { backgroundColor: 'rgba(255, 255, 255, 0.6)' }
                        }}
                      >
                        <CloseOutlinedIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <button className="status-toggle-btn" title={statusExpanded ? 'Collapse' : 'Expand'}>
                      {statusExpanded ? '▼' : '▶'}
                    </button>
                  </div>
                </div>
                {statusExpanded && (
                  <div className="status-scrollable-content">
                  {sharepointStatus.error ? (
                    <div className="status-error-msg">
                      ✗ Error: {sharepointStatus.error}
                    </div>
                  ) : (
                    <>
                    <div className="status-section">
                      <h4>Configuration</h4>
                      <div className="status-grid">
                        <div className="status-item">
                          <label>Enabled:</label>
                          <span className={sharepointStatus.sharepoint_integration?.enabled ? 'badge-yes' : 'badge-no'}>
                            {sharepointStatus.sharepoint_integration?.enabled ? (
                              <><CheckCircleIcon fontSize="small" sx={{verticalAlign: 'middle', mr: 0.5}} /> Yes</>
                            ) : (
                              <><CancelIcon fontSize="small" sx={{verticalAlign: 'middle', mr: 0.5}} /> No</>
                            )}
                          </span>
                        </div>
                        <div className="status-item">
                          <label>Folder URL:</label>
                          <span className="status-value">{sharepointStatus.config?.folder_url || 'N/A'}</span>
                        </div>
                        <div className="status-item">
                          <label>Excel File:</label>
                          <span className="status-value">{sharepointStatus.config?.excel_file_name || 'N/A'}</span>
                        </div>
                        <div className="status-item">
                          <label>Worksheet:</label>
                          <span className="status-value">{sharepointStatus.config?.worksheet_name || 'N/A'}</span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="status-section">
                      <h4>Access Token</h4>
                      <div className="status-grid">
                        <div className="status-item">
                          <label>Present:</label>
                          <span className={sharepointStatus.token?.present ? 'badge-yes' : 'badge-no'}>
                            {sharepointStatus.token?.present ? (
                              <><CheckCircleIcon fontSize="small" sx={{verticalAlign: 'middle', mr: 0.5}} /> Yes</>
                            ) : (
                              <><CancelIcon fontSize="small" sx={{verticalAlign: 'middle', mr: 0.5}} /> No</>
                            )}
                          </span>
                        </div>
                        <div className="status-item">
                          <label>Valid Format:</label>
                          <span className={sharepointStatus.token?.valid_format ? 'badge-yes' : 'badge-no'}>
                            {sharepointStatus.token?.valid_format ? (
                              <><CheckCircleIcon fontSize="small" sx={{verticalAlign: 'middle', mr: 0.5}} /> Yes (JWT)</>
                            ) : (
                              <><CancelIcon fontSize="small" sx={{verticalAlign: 'middle', mr: 0.5}} /> No</>
                            )}
                          </span>
                        </div>
                        <div className="status-item">
                          <label>Length:</label>
                          <span className="status-value">{sharepointStatus.token?.length || 0} characters</span>
                        </div>
                        {sharepointStatus.token?.preview && (
                          <div className="status-item full-width">
                            <label>Preview:</label>
                            <code className="token-preview">{sharepointStatus.token.preview}</code>
                          </div>
                        )}
                      </div>
                    </div>
                    
                    {sharepointStatus.connection_test && (
                      <div className="status-section">
                        <h4>Connection Test</h4>
                        {sharepointStatus.connection_test.success ? (
                          <div className="status-success-msg">
                            <CheckCircleIcon fontSize="small" sx={{verticalAlign: 'middle', mr: 0.5}} /> Connection successful to {sharepointStatus.connection_test.folder_url}
                          </div>
                        ) : (
                          <div className="status-error-msg">
                            <CancelIcon fontSize="small" sx={{verticalAlign: 'middle', mr: 0.5}} /> Connection failed: {sharepointStatus.connection_test.error}
                            <br/>
                            <small>Type: {sharepointStatus.connection_test.error_type}</small>
                          </div>
                        )}
                      </div>
                    )}
                    
                    <div className="status-footer">
                      Last check: {new Date(sharepointStatus.last_check).toLocaleString()}
                    </div>
                    </>
                  )}
                  </div>
                )}
              </div>
            )}
            
            {performanceMetrics && showMetricsBox && (
              <div className={`performance-metrics-box ${performanceMetrics.success ? 'status-success' : 'status-error'}`}>
                <div className="status-header" onClick={() => setMetricsExpanded(!metricsExpanded)}>
                  <h3><SpeedOutlinedIcon fontSize="small" sx={{verticalAlign: 'middle', mr: 0.5}} /> Performance Metrics</h3>
                  <div className="header-buttons">
                    <Tooltip title="Reset Statistics" arrow>
                      <IconButton 
                        size="small"
                        className="status-close-icon-btn" 
                        onClick={(e) => { e.stopPropagation(); resetMetrics(); }}
                        disabled={resetLoading}
                        sx={{ 
                          color: '#000000ff',
                          '&:hover': { backgroundColor: 'rgba(255, 255, 255, 0.6)' },
                          '&:disabled': { color: '#ccc' }
                        }}
                      >
                        <DeleteSweepOutlinedIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Close" arrow>
                      <IconButton 
                        size="small"
                        className="status-close-icon-btn" 
                        onClick={(e) => { e.stopPropagation(); setShowMetricsBox(false); }}
                        sx={{ 
                          color: '#dc3545',
                          '&:hover': { backgroundColor: 'rgba(255, 255, 255, 0.6)' }
                        }}
                      >
                        <CloseOutlinedIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <button className="status-toggle-btn" title={metricsExpanded ? 'Collapse' : 'Expand'}>
                      {metricsExpanded ? '▼' : '▶'}
                    </button>
                  </div>
                </div>
                {metricsExpanded && (
                  <div className="metrics-scrollable-content">
                    {performanceMetrics.success ? (
                      <>
                        {performanceMetrics.metrics.submissions && (
                        <div className="status-section">
                          <h4>Submission Statistics</h4>
                          <div className="status-grid">
                            <div className="status-item">
                              <label>Total Submissions:</label>
                              <span className="status-value">{performanceMetrics.metrics.submissions.total_submissions || 0}</span>
                            </div>
                            <div className="status-item">
                              <label>Successful:</label>
                              <span className={(performanceMetrics.metrics.submissions.successful_submissions || 0) > 0 ? 'badge-yes' : 'badge-no'}>
                                {performanceMetrics.metrics.submissions.successful_submissions || 0}
                              </span>
                            </div>
                            <div className="status-item">
                              <label>Failed:</label>
                              <span className={(performanceMetrics.metrics.submissions.failed_submissions || 0) === 0 ? 'badge-yes' : 'badge-no'}>
                                {performanceMetrics.metrics.submissions.failed_submissions || 0}
                              </span>
                            </div>
                            <div className="status-item">
                              <label>Success Rate:</label>
                              <span className="status-value">
                                {(performanceMetrics.metrics.submissions.total_submissions || 0) > 0 
                                  ? (((performanceMetrics.metrics.submissions.successful_submissions || 0) / performanceMetrics.metrics.submissions.total_submissions) * 100).toFixed(1)
                                  : 0}%
                              </span>
                            </div>
                            <div className="status-item">
                              <label>With Attachments:</label>
                              <span className="status-value">{performanceMetrics.metrics.submissions.with_attachments || 0}</span>
                            </div>
                            <div className="status-item">
                              <label>Without Attachments:</label>
                              <span className="status-value">{performanceMetrics.metrics.submissions.without_attachments || 0}</span>
                            </div>
                            <div className="status-item">
                              <label>Avg Duration:</label>
                              <span className="status-value">{performanceMetrics.metrics.submissions.avg_duration_seconds || 0}s</span>
                            </div>
                            <div className="status-item">
                              <label>Min/Max Duration:</label>
                              <span className="status-value">
                                {performanceMetrics.metrics.submissions.min_duration_seconds || 0}s / {performanceMetrics.metrics.submissions.max_duration_seconds || 0}s
                              </span>
                            </div>
                          </div>
                        </div>
                      )}
                      
                      {performanceMetrics.metrics.uploads && (
                        <div className="status-section">
                          <h4>Upload Statistics</h4>
                          <div className="status-grid">
                            <div className="status-item">
                              <label>Total Uploads:</label>
                              <span className="status-value">{performanceMetrics.metrics.uploads.total_uploads || 0}</span>
                            </div>
                            <div className="status-item">
                              <label>Successful:</label>
                              <span className={(performanceMetrics.metrics.uploads.successful_uploads || 0) > 0 ? 'badge-yes' : 'badge-no'}>
                                {performanceMetrics.metrics.uploads.successful_uploads || 0}
                              </span>
                            </div>
                            <div className="status-item">
                              <label>Failed:</label>
                              <span className={(performanceMetrics.metrics.uploads.failed_uploads || 0) === 0 ? 'badge-yes' : 'badge-no'}>
                                {performanceMetrics.metrics.uploads.failed_uploads || 0}
                              </span>
                            </div>
                            <div className="status-item">
                              <label>Success Rate:</label>
                              <span className="status-value">
                                {(performanceMetrics.metrics.uploads.total_uploads || 0) > 0 
                                  ? (((performanceMetrics.metrics.uploads.successful_uploads || 0) / performanceMetrics.metrics.uploads.total_uploads) * 100).toFixed(1)
                                  : 0}%
                              </span>
                            </div>
                          </div>
                        </div>
                      )}
                      
                      {performanceMetrics.metrics.uploads && (
                        <div className="status-section">
                          <h4>Upload Performance</h4>
                          <div className="status-grid">
                            <div className="status-item">
                              <label>Avg Duration:</label>
                              <span className="status-value">{performanceMetrics.metrics.uploads.avg_duration_seconds || 0}s</span>
                            </div>
                            <div className="status-item">
                              <label>Min Duration:</label>
                              <span className="status-value">{performanceMetrics.metrics.uploads.min_duration_seconds || 0}s</span>
                            </div>
                            <div className="status-item">
                              <label>Max Duration:</label>
                              <span className="status-value">{performanceMetrics.metrics.uploads.max_duration_seconds || 0}s</span>
                            </div>
                            <div className="status-item">
                              <label>Avg File Size:</label>
                              <span className="status-value">{performanceMetrics.metrics.uploads.avg_file_size_mb || 0} MB</span>
                            </div>
                          </div>
                        </div>
                      )}
                      
                      {performanceMetrics.metrics.uploads && performanceMetrics.metrics.uploads.recent_uploads && performanceMetrics.metrics.uploads.recent_uploads.length > 0 && (
                        <div className="status-section">
                          <h4>Recent Uploads (Last 20)</h4>
                          <div className="metrics-table-container">
                            <table className="metrics-table">
                              <thead>
                                <tr>
                                  <th>Time</th>
                                  <th>File</th>
                                  <th>Size</th>
                                  <th>Duration</th>
                                  <th>Status</th>
                                </tr>
                              </thead>
                              <tbody>
                                {performanceMetrics.metrics.uploads.recent_uploads.map((upload, idx) => (
                                  <tr key={idx}>
                                    <td className="metrics-time" data-label="Time">{new Date(upload.timestamp).toLocaleTimeString()}</td>
                                    <td className="metrics-filename" data-label="File" title={upload.filename}>{upload.filename}</td>
                                    <td className="metrics-size" data-label="Size">{(upload.file_size_bytes / 1024).toFixed(1)} KB</td>
                                    <td className="metrics-duration" data-label="Duration">{upload.duration_seconds}s</td>
                                    <td className="metrics-status" data-label="Status">
                                      {upload.success ? (
                                        <span className="badge-yes"><CheckCircleIcon fontSize="small" /> OK</span>
                                      ) : (
                                        <span className="badge-no" title={upload.error}><CancelIcon fontSize="small" /> Fail</span>
                                      )}
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      )}
                      
                      <div className="status-footer">
                        Last updated: {new Date(performanceMetrics.timestamp).toLocaleString()}
                      </div>
                      </>
                    ) : (
                      <div className="status-error-msg">
                        ✗ {performanceMetrics.error || 'Failed to fetch metrics'}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
            
            {jsonData && showJsonBox && (
              <div className={`json-data-box ${jsonData.success ? 'status-success' : 'status-error'}`}>
                <div className="status-header" onClick={() => setJsonExpanded(!jsonExpanded)}>
                  <h3><DescriptionOutlinedIcon fontSize="small" sx={{verticalAlign: 'middle', mr: 0.5}} /> JSON Data File</h3>
                  <div className="header-buttons">
                    <Tooltip title="Close" arrow>
                      <IconButton 
                        size="small"
                        className="status-close-icon-btn" 
                        onClick={(e) => { e.stopPropagation(); setShowJsonBox(false); }}
                        sx={{ 
                          color: '#dc3545',
                          '&:hover': { backgroundColor: 'rgba(255, 255, 255, 0.6)' }
                        }}
                      >
                        <CloseOutlinedIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <button className="status-toggle-btn" title={jsonExpanded ? 'Collapse' : 'Expand'}>
                      {jsonExpanded ? '▼' : '▶'}
                    </button>
                  </div>
                </div>
                {jsonExpanded && (
                  <div className="json-scrollable-content">
                  {jsonData.success ? (
                    <>
                      <div className="json-info">
                        <span><strong>Total Records:</strong> {jsonData.total_records}</span>
                        <span className="json-file-path"><strong>File:</strong> {jsonData.file_path}</span>
                        {selectedRecords.size > 0 && (
                          <button 
                            className="delete-selected-btn"
                            onClick={handleDeleteSelected}
                            disabled={deleteLoading}
                          >
                            <DeleteSweepOutlinedIcon fontSize="small" sx={{verticalAlign: 'middle', mr: 0.5}} /> Delete Selected ({selectedRecords.size})
                          </button>
                        )}
                      </div>
                      <div className="json-table-container">
                        <table className="json-records-table">
                          <thead>
                            <tr>
                              <th style={{width: '40px'}}>
                                <input 
                                  type="checkbox"
                                  checked={selectedRecords.size === jsonData.records.length && jsonData.records.length > 0}
                                  onChange={(e) => handleSelectAll(e.target.checked)}
                                  title="Select All"
                                />
                              </th>
                              <th>#</th>
                              <th>Request ID</th>
                              <th>Timestamp</th>
                              <th>Delivery Note</th>
                              <th>Truck Plates</th>
                              <th>Trailer Plates</th>
                              <th>Carrier Country</th>
                              <th>Carrier Tax Code</th>
                              <th>Carrier Name</th>
                              <th>Border Crossing</th>
                              <th>Crossing Date</th>
                              <th>Email</th>
                              <th>Phone Number</th>
                              <th>Attachment</th>
                              <th>SharePoint</th>
                            </tr>
                          </thead>
                          <tbody>
                            {jsonData.records.map((record, index) => (
                              <tr key={index}>
                                <td className="checkbox-cell" data-label="Select">
                                  <input 
                                    type="checkbox"
                                    checked={selectedRecords.has(record.Request_ID)}
                                    onChange={(e) => handleSelectRecord(record.Request_ID, e.target.checked)}
                                    disabled={!record.Request_ID}
                                  />
                                </td>
                                <td className="row-number" data-label="#">{index + 1}</td>
                                <td className="request-id" data-label="Request ID">{record.Request_ID || '-'}</td>
                                <td className="timestamp" data-label="Timestamp">{record.Timestamp ? new Date(record.Timestamp).toLocaleString('pl-PL') : '-'}</td>
                                <td data-label="Delivery Note">{record.Delivery_Note_Number || '-'}</td>
                                <td data-label="Truck">{record.Truck_License_Plates || '-'}</td>
                                <td data-label="Trailer">{record.Trailer_License_Plates || '-'}</td>
                                <td data-label="Country">{record.Carrier_Country || '-'}</td>
                                <td data-label="Tax Code">{record.Carrier_Tax_Code || '-'}</td>
                                <td data-label="Carrier">{record.Carrier_Full_Name || '-'}</td>
                                <td data-label="Border">{record.Border_Crossing || '-'}</td>
                                <td data-label="Date">{record.Border_Crossing_Date || '-'}</td>
                                <td data-label="Email">{record.Email || '-'}</td>
                                <td data-label="Phone">{record.Phone_Number || '-'}</td>
                                <td data-label="Attachment">
                                  {record.Has_Attachment === 'Yes' ? (
                                    <span className="badge-attachment-yes">
                                      <AttachFileIcon fontSize="small" sx={{verticalAlign: 'middle', mr: 0.5}} /> Yes
                                    </span>
                                  ) : (
                                    <span className="badge-attachment-no">
                                      <CancelIcon fontSize="small" sx={{verticalAlign: 'middle', mr: 0.5}} /> No
                                    </span>
                                  )}
                                  {record.Attachment_Error && (
                                    <div className="attachment-error" title={record.Attachment_Error}>
                                      <WarningAmberIcon fontSize="small" sx={{color: '#ff9800'}} />
                                    </div>
                                  )}
                                </td>
                                <td data-label="SharePoint">
                                  {record.SharePoint_Synced ? (
                                    <span className="badge-sync-yes">
                                      <CheckCircleIcon fontSize="small" sx={{verticalAlign: 'middle', mr: 0.5}} /> Synced
                                    </span>
                                  ) : (
                                    <span className="badge-sync-no">
                                      <PendingIcon fontSize="small" sx={{verticalAlign: 'middle', mr: 0.5}} /> Pending
                                    </span>
                                  )}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </>
                  ) : (
                    <div className="status-error-msg">
                      ✗ {jsonData.error || jsonData.message}
                    </div>
                  )}
                  </div>
                )}
              </div>
            )}
            
            {logInfo && (
              <div className="logs-viewer-info">
                <div className="logs-info-left">
                  <span>Showing {logInfo.lines_returned} of {logInfo.total_lines} lines</span>
                  <span className="log-file-path">{logInfo.log_file}</span>
                </div>
                <div className="logs-file-selector">
                  <label htmlFor="log-file-select">Log File:</label>
                  <select 
                    id="log-file-select"
                    value={selectedLogFile || ''}
                    onChange={(e) => {
                      const newFile = e.target.value || null;
                      setSelectedLogFile(newFile);
                      // Auto-refresh logs with new file selection
                      fetchLogs(100, newFile);
                    }}
                    disabled={logFiles.length <= 1}
                  >
                    <option value="">Latest (Today)</option>
                    {logFiles.map((file) => (
                      <option key={file.filename} value={file.filename}>
                        {file.date} ({(file.size / 1024).toFixed(1)} KB)
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            )}
            
            {error && (
              <div className="logs-viewer-error">
                ⚠ {error}
              </div>
            )}
            
            <div className="logs-viewer-content">
              {loading ? (
                <div className="logs-viewer-loading">Loading logs...</div>
              ) : logs.length > 0 ? (
                <table className="logs-table">
                  <thead>
                    <tr>
                      <th style={{width: '40px'}}></th>
                      <th>Timestamp</th>
                      <th>Level</th>
                      <th>Message</th>
                      <th>Details</th>
                    </tr>
                  </thead>
                  <tbody>
                    {logs.map((log, index) => (
                      <React.Fragment key={index}>
                        <tr 
                          className={`log-row log-${log.level?.toLowerCase() || 'info'} ${expandedRows.has(index) ? 'expanded' : ''}`}
                          onClick={() => toggleRow(index)}
                        >
                          <td className="expand-cell">
                            <span className="expand-icon">
                              {expandedRows.has(index) ? '▼' : '▶'}
                            </span>
                          </td>
                          <td className="log-timestamp">
                            {log.timestamp ? new Date(log.timestamp).toLocaleString() : 'N/A'}
                          </td>
                          <td className="log-level">
                            <span 
                              className="level-badge" 
                              style={{ backgroundColor: getLevelColor(log.level) }}
                            >
                              {log.level || 'INFO'}
                            </span>
                          </td>
                          <td className="log-message">{log.message || log.msg || 'No message'}</td>
                          <td className="log-details">
                            {log.form_data ? (
                              <span className="has-form-data"><DescriptionOutlinedIcon fontSize="small" sx={{verticalAlign: 'middle', mr: 0.5}} /> Form Data</span>
                            ) : log.request_id ? (
                              <span className="has-data">{log.request_id}</span>
                            ) : (
                              '-'
                            )}
                          </td>
                        </tr>
                        {expandedRows.has(index) && (
                          <tr className="expanded-row">
                            <td colSpan="5">
                              {renderExpandedContent(log)}
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="logs-viewer-empty">No logs available</div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default LogsViewer;
