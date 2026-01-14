# Transport Form Application

A React-based web application for collecting transport request information for UIT-RO (Romanian International Road Transport Union) border crossing registration.

## Features

- **Comprehensive Form Validation**: Real-time validation for all required fields
- **File Upload**: Support for multiple attachments (PDF, JPG, PNG) with drag-and-drop functionality
- **Async Submit**: Instant response to user (background processing handles uploads)
- **Email Confirmation**: Automatic email with form data and attachment status
- **Responsive Design**: Works on desktop and mobile devices
- **User-Friendly Interface**: Clear sections and intuitive form layout
- **Border Crossing Points**: Pre-populated dropdown with Romanian border crossings
- **i18n Ready**: Form labels externalized to `form-labels.json`

## Form Sections

### 1. Delivery Note Information
- Delivery note number (required)

### 2. Vehicle Information
- Truck license plates (required)
- Trailer license plates (required)

### 3. Carrier Information
- Carrier country (dropdown, required)
- Tax code (required)
- Full company name (required)

### 4. Border Crossing Information
- Border crossing point selection (required)
- Border crossing date (required)

### 5. Contact Information
- Email address (required)
- Phone number (Optional)

### 6. Attachments Upload (Optional)
- Support for multiple file uploads
- File type validation (PDF, JPG, PNG)
- File size limits (10MB per file, 10 files max)
- Drag and drop functionality
- **Parallel upload**: 3 files simultaneously (3x faster!)

## Tech Stack

- **React 18** - Frontend framework
- **Material-UI (MUI)** - UI component library
- **React Hook Form** - Form state management and validation
- **Yup** - Schema validation
- **React Dropzone** - File upload functionality
- **Vite** - Build tool and development server

## Performance

- **Instant submit**: User receives immediate confirmation (~100-200ms)
- **Background processing**: Attachments upload in parallel (3 workers)
- **No timeout**: Even with 10+ large files
- **Example**: 5 files × 3MB = ~5 seconds (parallel), not 15s (sequential)

## Getting Started

### Prerequisites
- Node.js (version 16 or higher)
- npm or yarn

### Installation

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

3. Open your browser and navigate to `http://localhost:3000`

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Form Validation Rules

### Required Fields
- Delivery note number
- Truck license plates
- Trailer license plates
- Carrier country
- Carrier tax code
- Carrier full name
- Border crossing point
- Border crossing date
- Email address

### Optional Fields
- Phone number
- File attachments

### Validation Rules
- **Email**: Must be valid email format
- **Phone**: Must be valid phone format (if provided)
- **Border Crossing Date**: Must be a valid date
- **File Upload**: PDF, JPG, PNG, max 10MB per file, max 20 files total
- **Delivery Note**: Required, must not be empty
- **License Plates**: Required, must not be empty

## Development

### Project Structure
```
src/
├── components/
│   ├── TransportForm/     # Main form component
│   ├── FileUpload/        # File upload component with drag-and-drop
│   ├── StatusMessage/     # Success/error message display
│   └── LogsViewer/        # Debug logs viewer (admin only)
├── utils/
│   └── api.js            # API client for backend communication
├── App.jsx               # Main application component
├── main.jsx             # Application entry point
├── App.css              # Application styles
└── index.css            # Global styles

public/
├── form-labels.json     # i18n-ready form labels
├── footer.txt           # Customizable footer text
└── robots.txt           # SEO configuration
```
s
### Current Features
- Backend API integration (FastAPI)
- SharePoint Excel synchronization
- Email notifications (MS Graph API)
- JSON backup persistence
- Debug mode with logs viewer
- Async parallel file uploads

### Future Enhancements
- Multi-language support (i18n - see [TODO_INTERNATIONALIZATION.md](../TODO_INTERNATIONALIZATION.md))
- PDF generation of submitted forms
- Dashboard with submission statistics
- Real-time notifications
- Form progress saving (draft mode)

## Related Documentation

- **[Main README](../README.md)** - User documentation and quick start
- **[DEVELOPER.md](../DEVELOPER.md)** - Complete technical documentation
- **[TODO_INTERNATIONALIZATION.md](../TODO_INTERNATIONALIZATION.md)** - i18n implementation plan
- **[DEBUG_MODE.md](../DEBUG_MODE.md)** - Debug mode configuration
