# TODO: Internationalization (i18n) Implementation

## Current State Analysis

### Already Externalized
- **Form labels** (`frontend/public/form-labels.json`): 25 texts
  - Page title, field labels, buttons, file upload messages

---

## Hardcoded Texts Requiring i18n

### Priority by Impact:

#### ** PRIORITY 1: Critical User-Facing** (~80 texts)

**1. App.jsx** (3 texts):
```jsx
- "Transport Form App" (main header)
- "Please fill out the form below for transport registration"
- "© 2025. All rights reserved."
```

**2. TransportForm.jsx** (15 texts):
- Validation messages:
  - "Invalid email format"
  - "is required" (11× - dynamically appended)
  - "Loading form..."
  - "⚠ Configuration Error"
  - "Please contact system administrator or check browser console for details."
  
- Success/Error messages:
  - "Form submitted successfully! Request ID: {id}"
  - "⚠ Warning: Excel file is currently LOCKED (open by another user)."
  - "Data saved locally. Please close the Excel file and the system will retry automatically."
  - "⚠ Warning: Data saved locally, but SharePoint update failed."
  - "Check browser console for details or use 'SharePoint Status' in Logs."
  - "Error submitting form: {error}. Please try again."

**3. FileUpload.jsx** (6 texts):
```jsx
- "Invalid file type. Please upload PDF, JPG, or PNG files only."
- "File too large. Maximum size is {maxSize}MB"
- "Too many files. Maximum {maxFiles} files allowed."
```

**4. Email Template** (`backend/res/confirmation_email.html`) (30 texts):
- "Transport Request Confirmation" (title)
- "✓ Request Received Successfully"
- "Your transport request has been successfully submitted"
- "Request Details", "Delivery Note", "Truck Plates", etc. (15+ fields)
- "Attachments" section
- "Need Help?", "Contact us at:", "This is an automated message"
- "© 2025. All rights reserved."

---

#### ** PRIORITY 2: Admin/Support Features** (~80 texts)

**5. LogsViewer.jsx** (80+ texts):
- Main sections:
  - "Logs Viewer", "Form Submission Logs"
  - "SharePoint Integration Status", "JSON Backup Data"
  
- Actions:
  - "Refresh", "Download JSON", "Export Logs"
  - "Clear Session Logs", "Delete Selected", "Cleanup Old Attachments"
  
- Authentication:
  - "Password Required", "Enter Debug Secret Key"
  - "Unlock", "Cancel", "Invalid secret key"
  
- Status messages: 50+ labels for various states

---

#### ** PRIORITY 3: Technical/Optional** (~200 texts)

**6. Backend API Messages** (`backend/fastapi_app.py`):
- Error responses:
  - "Invalid JSON: {e}"
  - "Invalid data: {e}"
  - "Invalid email format"
  - "Field cannot be empty"
  
- Status values in JSON/Excel:
  - "Processing", "Processing..."
  - "Saved", "Failed", "None"
  - "Success", "Error"

**7. Backend Logs** (~150 texts):
- Console logs (info, warning, error)
- Technical messages for debugging
- SharePoint integration logs

---

## Proposed Folder Structure

```
frontend/
  public/
    locales/
      en.json     ← English (default)
      pl.json     ← Polish (optional)
      ro.json     ← Romanian (optional)
      de.json     ← German (optional)
      
backend/
  locales/
    en.json     ← Backend messages (email + API)
    pl.json
    ro.json
```

---

## Example Locale File Structure

### `frontend/public/locales/en.json`:
```json
{
  "app": {
    "title": "Transport Form App",
    "subtitle": "Please fill out the form below for transport registration",
    "footer": "© 2025. All rights reserved."
  },
  "form": {
    "pageTitle": "Transport Application",
    "loading": "Loading form...",
    "fields": {
      "deliveryNoteNumber": "Delivery note number",
      "truckLicensePlates": "Truck license plates",
      "trailerLicensePlates": "Trailer license plates",
      "carrierFullName": "Carrier name",
      "carrierCountry": "Carrier country",
      "carrierTaxCode": "Carrier tax code",
      "borderCrossing": "Border crossing point",
      "borderCrossingDate": "Border crossing date",
      "email": "Email",
      "phoneNumber": "Phone number"
    },
    "validation": {
      "required": "{{field}} is required",
      "invalidEmail": "Invalid email format",
      "invalidFileType": "Invalid file type. Please upload PDF, JPG, or PNG files only.",
      "fileTooLarge": "File too large. Maximum size is {{maxSize}}MB",
      "tooManyFiles": "Too many files. Maximum {{maxFiles}} files allowed."
    },
    "buttons": {
      "submit": "Submit Application",
      "submitting": "Submitting...",
      "cancel": "Cancel",
      "clear": "Clear"
    },
    "messages": {
      "submitSuccess": "Form submitted successfully! Request ID: {{requestId}}",
      "excelLocked": "⚠ Warning: Excel file is currently LOCKED (open by another user).\nData saved locally. Please close the Excel file and the system will retry automatically.",
      "sharepointError": "⚠ Warning: Data saved locally, but SharePoint update failed.\nCheck browser console for details or use 'SharePoint Status' in Logs.",
      "submitError": "Error submitting form: {{error}}. Please try again.",
      "configError": "Configuration Error",
      "contactAdmin": "Please contact system administrator or check browser console for details."
    }
  },
  "fileUpload": {
    "dragDrop": "Drag & drop files here, or click to select files",
    "dropHere": "Drop the files here...",
    "supported": "Supported: PDF, JPG, PNG (max {{maxSize}}MB each, {{maxFiles}} files total)",
    "uploadedFiles": "Uploaded Files ({{count}}/{{maxFiles}})"
  },
  "logs": {
    "title": "Logs Viewer",
    "formLogs": "Form Submission Logs",
    "sharepointStatus": "SharePoint Integration Status",
    "jsonBackup": "JSON Backup Data",
    "refresh": "Refresh",
    "download": "Download JSON",
    "export": "Export Logs",
    "clear": "Clear Session Logs",
    "delete": "Delete Selected",
    "cleanup": "Cleanup Old Attachments",
    "passwordRequired": "Password Required",
    "enterKey": "Enter Debug Secret Key",
    "unlock": "Unlock",
    "cancel": "Cancel",
    "invalidKey": "Invalid secret key"
  },
  "email": {
    "title": "Transport Request Confirmation",
    "successBadge": "✓ Request Received Successfully",
    "intro": "Your transport request has been successfully submitted and is being processed.",
    "requestDetails": "Request Details",
    "attachments": "Attachments",
    "attachmentStatus": {
      "uploaded": "Successfully uploaded:",
      "failed": "Failed to upload:"
    },
    "needHelp": "Need Help?",
    "contactUs": "Contact us at:",
    "automated": "This is an automated message. Please do not reply to this email.",
    "footer": "© 2025. All rights reserved.",
    "fields": {
      "deliveryNote": "Delivery Note",
      "truckPlates": "Truck Plates",
      "trailerPlates": "Trailer Plates",
      "carrierName": "Carrier Name",
      "carrierCountry": "Carrier Country",
      "carrierTaxCode": "Carrier Tax Code",
      "borderCrossing": "Border Crossing",
      "borderCrossingDate": "Crossing Date",
      "email": "Email",
      "phoneNumber": "Phone Number"
    }
  }
}
```

### `frontend/public/locales/pl.json`:
```json
{
  "app": {
    "title": "Formularz transportowy",
    "subtitle": "Proszę wypełnić poniższy formularz dla rejestracji transportu",
    "footer": "© 2025. Wszelkie prawa zastrzeżone."
  },
  "form": {
    "pageTitle": "Wniosek transportowy",
    "loading": "Ładowanie formularza...",
    "fields": {
      "deliveryNoteNumber": "Numer dokumentu dostawy",
      "truckLicensePlates": "Tablice rejestracyjne ciężarówki",
      "trailerLicensePlates": "Tablice rejestracyjne naczepy",
      "carrierFullName": "Nazwa przewoźnika",
      "carrierCountry": "Kraj przewoźnika",
      "carrierTaxCode": "NIP przewoźnika",
      "borderCrossing": "Przejście graniczne",
      "borderCrossingDate": "Data przekroczenia granicy",
      "email": "Email",
      "phoneNumber": "Numer telefonu"
    },
    "validation": {
      "required": "{{field}} jest wymagane",
      "invalidEmail": "Nieprawidłowy format email",
      "invalidFileType": "Nieprawidłowy typ pliku. Proszę przesłać tylko pliki PDF, JPG lub PNG.",
      "fileTooLarge": "Plik za duży. Maksymalny rozmiar to {{maxSize}}MB",
      "tooManyFiles": "Za dużo plików. Maksymalnie {{maxFiles}} plików."
    },
    "messages": {
      "submitSuccess": "Formularz wysłany pomyślnie! ID zgłoszenia: {{requestId}}",
      "excelLocked": "⚠ Uwaga: Plik Excel jest obecnie ZABLOKOWANY (otwarty przez innego użytkownika).\nDane zapisane lokalnie. Proszę zamknąć plik Excel, system ponowi próbę automatycznie.",
      "submitError": "Błąd wysyłania formularza: {{error}}. Spróbuj ponownie."
    }
  }
}
```

---

## Implementation Libraries

### Frontend (React):
```bash
npm install react-i18next i18next i18next-http-backend
```

**Features:**
- Automatic locale file loading
- Variable interpolation: `{{requestId}}`
- Pluralization: `{{count}} file(s)`
- Browser language detection
- Persistent language selection (localStorage)

### Backend (Python):
```bash
pip install babel flask-babel
```

Or simple custom solution:
```python
import json

class I18n:
    def __init__(self, lang='en'):
        with open(f'locales/{lang}.json') as f:
            self.messages = json.load(f)
    
    def t(self, key, **kwargs):
        msg = self.messages.get(key, key)
        return msg.format(**kwargs)
```

---

## Implementation Phases

### **PHASE 1: Core User Interface** (2-3h)
**Goal:** Basic multilingual support for main user flow

**Tasks:**
1. Install `react-i18next`:
   ```bash
   cd frontend
   npm install react-i18next i18next i18next-http-backend
   ```

2. Create locale files:
   ```
   frontend/public/locales/en.json (Priority 1 texts)
   frontend/public/locales/pl.json (Polish translation)
   ```

3. Setup i18next configuration:
   ```jsx
   // frontend/src/i18n.js
   import i18n from 'i18next';
   import { initReactI18next } from 'react-i18next';
   import HttpBackend from 'i18next-http-backend';
   
   i18n
     .use(HttpBackend)
     .use(initReactI18next)
     .init({
       lng: localStorage.getItem('language') || 'en',
       fallbackLng: 'en',
       backend: {
         loadPath: '/locales/{{lng}}.json'
       }
     });
   ```

4. Create Language Selector component:
   ```jsx
   // frontend/src/components/LanguageSelector/LanguageSelector.jsx
   import { useTranslation } from 'react-i18next';
   
   function LanguageSelector() {
     const { i18n } = useTranslation();
     
     const changeLanguage = (lng) => {
       i18n.changeLanguage(lng);
       localStorage.setItem('language', lng);
     };
     
     return (
       <select 
         onChange={(e) => changeLanguage(e.target.value)} 
         value={i18n.language}
       >
         <option value="en">English</option>
         <option value="pl">Polski</option>
         <option value="ro">Română</option>
       </select>
     );
   }
   ```

5. Update components:
   - `App.jsx`: Replace hardcoded texts with `t('app.title')`
   - `TransportForm.jsx`: Use `t('form.messages.submitSuccess', { requestId })`
   - `FileUpload.jsx`: Use `t('form.validation.invalidFileType')`

**Deliverables:**
- English locale file (complete)
- Polish locale file (translated)
- Language selector in header
- Form fully translatable

---

### **PHASE 2: Email & Backend** (1-2h)
**Goal:** Multilingual email confirmations

**Tasks:**
1. Create backend locale loader:
   ```python
   # backend/i18n.py
   import json
   from pathlib import Path
   
   class EmailI18n:
       def __init__(self, lang='en'):
           locale_path = Path(__file__).parent / 'locales' / f'{lang}.json'
           with open(locale_path, 'r', encoding='utf-8') as f:
               self.messages = json.load(f)
       
       def t(self, key, **kwargs):
           keys = key.split('.')
           value = self.messages
           for k in keys:
               value = value.get(k, key)
           return value.format(**kwargs) if kwargs else value
   ```

2. Create email template engine:
   ```python
   # backend/email_renderer.py
   from jinja2 import Template
   from i18n import EmailI18n
   
   def render_confirmation_email(request_id, data, lang='en'):
       i18n = EmailI18n(lang)
       template_path = Path(__file__).parent / 'res' / 'confirmation_email.html'
       
       with open(template_path) as f:
           template = Template(f.read())
       
       return template.render(
           t=i18n.t,
           request_id=request_id,
           data=data
       )
   ```

3. Update email template to use `{{ t('email.title') }}`

4. Detect user language from form submission (`data.get('language', 'en')`)

**Deliverables:**
- Backend locale files (en.json, pl.json)
- Email template with i18n support
- Language detection in email sending

---

### **PHASE 3: Admin Panel** (2-3h - Optional)
**Goal:** Translate LogsViewer for support team

**Tasks:**
1. Add LogsViewer texts to locale files
2. Update LogsViewer.jsx to use `useTranslation()`
3. Translate debug/admin messages

**Deliverables:**
- LogsViewer fully translated
- Admin panel in multiple languages
