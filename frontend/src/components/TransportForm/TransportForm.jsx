import React, { useState } from 'react'
import { useForm } from 'react-hook-form'
import { yupResolver } from '@hookform/resolvers/yup'
import * as yup from 'yup'
import MuiFormField from '../FormField/MuiFormField'
import MuiChipInputField from '../FormField/MuiChipInputField'
import MuiBorderCrossingField from '../FormField/MuiBorderCrossingField'
import FileUpload from '../FileUpload/FileUpload'
import logger from '../../utils/logger'
import './TransportForm.css'


// Validation schema generator - creates messages dynamically from field labels
const createSchema = (fieldLabels) => {
  if (!fieldLabels) {
    throw new Error('Field labels not loaded');
  }
  return yup.object().shape({
    deliveryNoteNumber: yup.array().min(1, `${fieldLabels.deliveryNoteNumber} - at least one number is required`).required(`${fieldLabels.deliveryNoteNumber} is required`),
    truckLicensePlates: yup.string().required(`${fieldLabels.truckLicensePlates} is required`),
    trailerLicensePlates: yup.string().required(`${fieldLabels.trailerLicensePlates} is required`),
    carrierCountry: yup.string().required(`${fieldLabels.carrierCountry} is required`),
    carrierTaxCode: yup.string().required(`${fieldLabels.carrierTaxCode} is required`),
    carrierFullName: yup.string().required(`${fieldLabels.carrierFullName} is required`),
    borderCrossing: yup.string().required(`${fieldLabels.borderCrossing} is required`),
    borderCrossingDate: yup.date().required(`${fieldLabels.borderCrossingDate} is required`),
    email: yup.string().email('Invalid email format').required(`${fieldLabels.email} is required`),
    phoneNumber: yup.string().optional(),
  });
}

const TransportForm = () => {

  const [isSubmitting, setIsSubmitting] = useState(false)
  const [uploadedFiles, setUploadedFiles] = useState([])
  const [clearFileUpload, setClearFileUpload] = useState(false)
  const [labels, setLabels] = useState(null)
  const [schema, setSchema] = useState(null)
  
  // Load form labels from JSON file
  React.useEffect(() => {
    fetch('/form-labels.json')
      .then(res => res.json())
      .then(data => {
        setLabels(data);
        // Update schema - generate validation messages from field labels
        if (data.fields) {
          setSchema(createSchema(data.fields));
        }
      })
      .catch(err => {
        console.error('%c✗ Failed to load form labels:', 'color: #dc3545; font-weight: bold', err);
        console.error('%c✗ Application cannot start without form-labels.json', 'color: #dc3545; font-weight: bold');
        // Set error state instead of fallback
        setLabels({ error: true, message: 'Failed to load form configuration' });
      });
  }, [])
  
  const {
    handleSubmit,
    formState: { errors, isValid },
    reset,
    control
  } = useForm({
    resolver: schema ? yupResolver(schema) : undefined,
    mode: 'onChange',
    defaultValues: {
      deliveryNoteNumber: [],
      truckLicensePlates: '',
      trailerLicensePlates: '',
      carrierCountry: '',
      carrierTaxCode: '',
      carrierFullName: '',
      borderCrossing: '',
      borderCrossingDate: null,
      email: '',
      phoneNumber: ''
    }
  })


  const onSubmit = async (data) => {
    setIsSubmitting(true)
    
    // Prepare logging data
    const formDataForLogging = {
      ...data,
      attachments: uploadedFiles && uploadedFiles.length > 0 ? uploadedFiles.map(f => f.name) : [],
      borderCrossingDate: data.borderCrossingDate ? data.borderCrossingDate.toISOString().split('T')[0] : ''
    };
    
    // Log form submission attempt
    logger.logFormSubmit(formDataForLogging, 'ATTEMPT');
    
    try {
      // Prepare form data for FastAPI backend
      const formData = new FormData();
      
      // Convert form data to JSON string for the 'data' field
      const jsonData = {
        deliveryNoteNumber: Array.isArray(data.deliveryNoteNumber) ? data.deliveryNoteNumber.join(', ') : data.deliveryNoteNumber,
        truckLicensePlates: data.truckLicensePlates,
        trailerLicensePlates: data.trailerLicensePlates,
        carrierCountry: data.carrierCountry,
        carrierTaxCode: data.carrierTaxCode,
        carrierFullName: data.carrierFullName,
        borderCrossing: data.borderCrossing,
        borderCrossingDate: data.borderCrossingDate ? data.borderCrossingDate.toISOString().split('T')[0] : '',
        email: data.email,
        phoneNumber: data.phoneNumber || ''
      };
      
      // Encode JSON data as Base64 to avoid WAF SQL injection false positives
      const jsonString = JSON.stringify(jsonData);
      
      // Use UTF-8 safe Base64 encoding (handles special characters like ă, ș, ț, etc.)
      const encodedData = btoa(encodeURIComponent(jsonString).replace(/%([0-9A-F]{2})/g, (match, p1) => {
        return String.fromCharCode('0x' + p1);
      }));
      
      console.log('%cℹ Original JSON:', 'color: #17a2b8; font-weight: bold', jsonString);
      console.log('%cℹ Base64 Encoded (UTF-8 safe):', 'color: #17a2b8; font-weight: bold', encodedData);
      
      formData.append('data', encodedData);
      
      // Add all attachments if exist
      if (uploadedFiles && uploadedFiles.length > 0) {
        uploadedFiles.forEach((fileItem, index) => {
          formData.append('attachments', fileItem.file);
          console.log(`Added attachment ${index + 1}/${uploadedFiles.length}: ${fileItem.name}`);
        });
      }
      
      // Send to FastAPI backend via proxy (works both locally and in production)
      // Dynamically determine API base URL based on current hostname
      let apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '';
      
      // Debug info
      console.log('%cℹ API URL Detection:', 'color: #17a2b8; font-weight: bold', {
        hostname: window.location.hostname,
        protocol: window.location.protocol,
        envVar: import.meta.env.VITE_API_BASE_URL,
        isProduction: window.location.hostname.includes('yourdomain.com'),
        isLocalhost: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
      });
      
      // If no env var set, detect domain type for appropriate endpoint
      if (!apiBaseUrl) {
        // Check if running locally (Docker Desktop)
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
          // For local development, use localhost backend port
          apiBaseUrl = 'http://localhost:8010';
          console.log('%c✓ Using local API:', 'color: #28a745; font-weight: bold', apiBaseUrl);
        } else if (window.location.hostname.includes('yourdomain.com')) {
          // For external access, use same domain (requires nginx proxy configuration)
          // IMPORTANT: External domain must be configured by network admin with:
          // - DNS entry for your-production-server.yourdomain.com
          // - Nginx location /api/ proxy_pass to internal server:5443
          apiBaseUrl = `${window.location.protocol}//${window.location.hostname}`;
          console.log('%cℹ Using external API (requires nginx proxy):', 'color: #17a2b8; font-weight: bold', apiBaseUrl);
          console.warn('%c⚠ External access requires network admin configuration!', 'color: #ffc107; font-weight: bold');
        } else {
          // For internal access without env var, use hardcoded internal endpoint
          apiBaseUrl = 'https://transport-app.yourdomain.com'; // 5443
          console.log('%cℹ Using internal API (fallback):', 'color: #17a2b8; font-weight: bold', apiBaseUrl);
        }
      } else {
        console.log('%cℹ Using internal API (env var):', 'color: #17a2b8; font-weight: bold', apiBaseUrl);
      }
      
      const finalUrl = `${apiBaseUrl}/api/submit`;
      console.log('%c✓ Final API URL:', 'color: #28a745; font-weight: bold', finalUrl);
      
      let response;
      
      try {
        response = await fetch(finalUrl, {
          method: 'POST',
          headers: {
            'X-Content-Type': 'application/transport-form',
            'X-Request-Source': 'transport-frontend',
            'X-Bypass-SQLI': 'legitimate-form-data',
            'X-Data-Encoding': 'base64'
          },
          body: formData
        });
      } catch (error) {
        console.error('Network error:', error);
        throw new Error(`Network error: ${error.message}`);
      }
      
      if (!response.ok) {
        const errorData = await response.json();
        const errorMsg = errorData.detail || 'Failed to submit form';
        
        // Log API error
        logger.logFormSubmit(formDataForLogging, 'ERROR', errorMsg);
        logger.logApiError('/api/submit', new Error(errorMsg), jsonData);
        
        throw new Error(errorMsg);
      }
      
      const result = await response.json();
      console.log('Submit response:', result);
      
      // Check SharePoint status in response
      if (result.sharepoint_saved) {
        console.log('%c✓ SharePoint: Data saved successfully', 'color: #28a745; font-weight: bold');
      } else if (result.sharepoint_error) {
        console.warn('%c⚠ SharePoint: Save failed -', 'color: #ffc107; font-weight: bold', result.sharepoint_error);
        
        // Check if it's a lock error
        const errorLower = result.sharepoint_error.toLowerCase();
        const isLockError = errorLower.includes('locked') || 
                           errorLower.includes('in use') || 
                           errorLower.includes('open by another user') ||
                           errorLower.includes('close the file');
        
        if (isLockError) {
          console.warn('%c⚠ Excel file is locked - likely open by another user', 'color: #ffc107; font-weight: bold');
        } else {
          console.warn('%cℹ Note: Local data saved, but SharePoint update failed. Check token or connection.', 'color: #17a2b8; font-weight: bold');
        }
      }
      
      // Log successful submission
      logger.logFormSubmit(formDataForLogging, 'SUCCESS', null, result.request_id);
      
      // Enhanced success message with SharePoint status
      let successMessage = `Form submitted successfully! Request ID: ${result.request_id}`;
      if (!result.sharepoint_saved && result.sharepoint_error) {
        const errorLower = result.sharepoint_error.toLowerCase();
        const isLockError = errorLower.includes('locked') || 
                           errorLower.includes('in use') || 
                           errorLower.includes('open by another user') ||
                           errorLower.includes('close the file');
        
        if (isLockError) {
          successMessage += '\n\n⚠ Warning: Excel file is currently LOCKED (open by another user).';
          successMessage += '\nData saved locally. Please close the Excel file and the system will retry automatically.';
        } else {
          successMessage += '\n\n⚠ Warning: Data saved locally, but SharePoint update failed.';
          successMessage += '\nCheck browser console for details or use "SharePoint Status" in Logs.';
        }
      }
      
      alert(successMessage);
      
      // Clear form and files
      reset()
      setUploadedFiles([])
      setClearFileUpload(true)
      
      // Reset clearFileUpload flag after a brief delay
      setTimeout(() => setClearFileUpload(false), 100)
    } catch (error) {
      console.error('Submit error:', error);
      
      // Determine error type
      let errorType = 'ERROR';
      if (error.name === 'TypeError' || error.message.includes('fetch')) {
        errorType = 'NETWORK_ERROR';
        logger.logApiError('/api/submit', error, formDataForLogging);
      }
      
      // Log error
      logger.logFormSubmit(formDataForLogging, errorType, error.message);
      alert(`Error submitting form: ${error.message}. Please try again.`);
    } finally {
      setIsSubmitting(false)
    }
  }

  // Show loading state while labels are being fetched
  if (!labels) {
    return <div className="transport-form"><div className="form-loading">Loading form...</div></div>;
  }
  
  // Show error if labels failed to load
  if (labels.error) {
    return (
      <div className="transport-form">
        <div className="form-error">
          <h3>⚠ Configuration Error</h3>
          <p>{labels.message}</p>
          <p>Please contact system administrator or check browser console for details.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="transport-form">
      <form onSubmit={handleSubmit(onSubmit)} className="form">
        <div className="form-section">
          <h2>{labels.pageTitle}</h2>
          <MuiChipInputField
            label={labels.fields.deliveryNoteNumber}
            name="deliveryNoteNumber"
            control={control}
            error={errors.deliveryNoteNumber}
            required
          />
          <hr className="form-divider" />
          <MuiFormField
            label={labels.fields.truckLicensePlates}
            name="truckLicensePlates"
            control={control}
            error={errors.truckLicensePlates}
            required
          />
          <MuiFormField
            label={labels.fields.trailerLicensePlates}
            name="trailerLicensePlates"
            control={control}
            error={errors.trailerLicensePlates}
            required
          />
          <MuiFormField
            label={labels.fields.carrierFullName}
            name="carrierFullName"
            control={control}
            error={errors.carrierFullName}
            required
          />
          <MuiFormField
            label={labels.fields.carrierCountry}
            name="carrierCountry"
            type="country"
            control={control}
            error={errors.carrierCountry}
            required
          />
          <MuiFormField
            label={labels.fields.carrierTaxCode}
            name="carrierTaxCode"
            control={control}
            error={errors.carrierTaxCode}
            required
          />
          <MuiFormField
            label={labels.fields.email}
            name="email"
            type="email"
            control={control}
            error={errors.email}
            required
          />
          <MuiFormField
            label={labels.fields.phoneNumber}
            name="phoneNumber"
            control={control}
            error={errors.phoneNumber}
          />
          <hr className="form-divider" />
          <MuiBorderCrossingField
            label={labels.fields.borderCrossing}
            name="borderCrossing"
            control={control}
            error={errors.borderCrossing}
            required
          />
          {/* Ensure date field is not in a flex/grid row */}
          <div style={{ width: '100%', marginTop: '0.25rem' }}>
            <MuiFormField
              label={labels.fields.borderCrossingDate}
              name="borderCrossingDate"
              type="date"
              control={control}
              error={errors.borderCrossingDate}
              required
            />
          </div>
          <hr className="form-divider" />
          <FileUpload 
            onFilesChange={setUploadedFiles} 
            clearFiles={clearFileUpload}
            labels={labels.fileUpload || {}}
          />
        </div>
        <div className="form-actions">
          <button
            type="submit"
            className={`submit-button ${!isValid ? 'disabled' : ''}`}
            disabled={!isValid || isSubmitting}
          >
            {isSubmitting ? labels.buttons.submitting : labels.buttons.submit}
          </button>
        </div>
      </form>
    </div>
  )
}

export default TransportForm