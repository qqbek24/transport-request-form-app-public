import React, { useCallback, useState, useEffect } from 'react'
import PropTypes from 'prop-types'
import { useDropzone } from 'react-dropzone'
import UploadFileIcon from '@mui/icons-material/UploadFile'
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf'
import AttachFileOutlinedIcon from '@mui/icons-material/AttachFileOutlined'
import './FileUpload.css'

const FileUpload = ({ onFilesChange, maxFiles = 10, maxSize = 10 * 1024 * 1024, clearFiles = false, labels = {} }) => { // 10MB default, 10 files max
  const [files, setFiles] = useState([])
  const [uploadError, setUploadError] = useState('')

  // Clear files when parent component requests it
  useEffect(() => {
    if (clearFiles) {
      setFiles([])
      setUploadError('')
      onFilesChange([])
    }
  }, [clearFiles, onFilesChange])

  const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    setUploadError('')
    
    // Handle rejected files
    if (rejectedFiles.length > 0) {
      const error = rejectedFiles[0].errors[0]
      if (error.code === 'file-too-large') {
        setUploadError(labels.fileTooLarge || `File is too large. Maximum size is ${maxSize / 1024 / 1024}MB`)
      } else if (error.code === 'file-invalid-type') {
        setUploadError('Invalid file type. Please upload PDF, JPG, or PNG files only.')
      } else {
        setUploadError('File upload error. Please try again.')
      }
      return
    }

    // Handle accepted files
    if (files.length + acceptedFiles.length > maxFiles) {
      setUploadError(`Maximum ${maxFiles} files allowed`)
      return
    }

    const newFiles = acceptedFiles.map(file => ({
      file,
      id: Date.now() + Math.random(),
      name: file.name,
      size: file.size,
      type: file.type,
      preview: file.type.startsWith('image/') ? URL.createObjectURL(file) : null
    }))

    const updatedFiles = [...files, ...newFiles]
    setFiles(updatedFiles)
    onFilesChange(updatedFiles)
  }, [files, maxFiles, maxSize, onFilesChange, labels])

  const removeFile = (fileId) => {
    const updatedFiles = files.filter(f => f.id !== fileId)
    setFiles(updatedFiles)
    onFilesChange(updatedFiles)
    
    // Clean up preview URLs
    const fileToRemove = files.find(f => f.id === fileId)
    if (fileToRemove && fileToRemove.preview) {
      URL.revokeObjectURL(fileToRemove.preview)
    }
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png']
    },
    maxSize,
    multiple: true
  })

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  return (
    <div className="file-upload">
      <div
        {...getRootProps()}
        className={`dropzone ${isDragActive ? 'active' : ''} ${uploadError ? 'error' : ''}`}
      >
        <input {...getInputProps()} />
        <div className="dropzone-content">
          {/* <div className="upload-icon">📁</div> */}
          <div className="upload-icon">
            <UploadFileIcon 
              sx={{ 
                fontSize: 48,
                transition: 'all 0.3s ease'
              }} 
            />
          </div>
          {isDragActive ? (
            <p>{labels.dropHere || 'Drop the files here...'}</p>
          ) : (
            <div>
              <p>{labels.dragDrop || 'Drag & drop files here, or click to select files'}</p>
              <p className="file-info">
                {labels.supported 
                  ? labels.supported
                      .replace('{{maxSize}}', maxSize / 1024 / 1024)
                      .replace('{{maxFiles}}', maxFiles)
                  : `Supported: PDF, JPG, PNG (max ${maxSize / 1024 / 1024}MB each, ${maxFiles} files total)`
                }
              </p>
            </div>
          )}
        </div>
      </div>

      {uploadError && (
        <div className="upload-error">
          {uploadError}
        </div>
      )}

      {files.length > 0 && (
        <div className="uploaded-files">
          <h4>
            {labels.uploadedFiles
              ? labels.uploadedFiles
                  .replace('{{count}}', files.length)
                  .replace('{{maxFiles}}', maxFiles)
              : `Uploaded Files (${files.length}/${maxFiles})`
            }
          </h4>
          <div className="file-list">
            {files.map((fileItem) => (
              <div key={fileItem.id} className="file-item">
                <div className="file-info">
                  {fileItem.preview ? (
                    <img 
                      src={fileItem.preview} 
                      alt={fileItem.name}
                      className="file-preview"
                    />
                  ) : (
                    <div className="file-icon">
                      {fileItem.type === 'application/pdf' ? (
                        <PictureAsPdfIcon sx={{ fontSize: 32, color: '#d32f2f' }} />
                      ) : (
                        <AttachFileOutlinedIcon sx={{ fontSize: 32, color: '#6c63ff' }} />
                      )}
                    </div>
                  )}
                  <div className="file-details">
                    <div className="file-name">{fileItem.name}</div>
                    <div className="file-size">{formatFileSize(fileItem.size)}</div>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => removeFile(fileItem.id)}
                  className="remove-file"
                  aria-label="Remove file"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
FileUpload.propTypes = {
  onFilesChange: PropTypes.func.isRequired,
  maxFiles: PropTypes.number,
  maxSize: PropTypes.number,
  clearFiles: PropTypes.bool,
  labels: PropTypes.object
}

export default FileUpload
