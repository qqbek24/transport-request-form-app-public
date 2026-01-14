import React from 'react'
import PropTypes from 'prop-types'
import './FormField.css'

const FormField = ({
  label,
  name,
  type = 'text',
  register,
  error,
  required = false,
  options = [],
  placeholder,
  ...props
}) => {
  const renderInput = () => {
    switch (type) {
      case 'textarea':
        return (
          <textarea
            id={name}
            {...register(name)}
            className={`form-input ${error ? 'error' : ''}`}
            placeholder={placeholder}
            rows={4}
            {...props}
          />
        )
      

      case 'select': {
        // If options is an object, render grouped options
        const isGrouped = options && typeof options === 'object' && !Array.isArray(options);
        return (
          <select
            id={name}
            {...register(name)}
            className={`form-input ${error ? 'error' : ''}`}
            {...props}
          >
            <option value="">Select {label}</option>
            {isGrouped
              ? Object.entries(options).map(([group, opts]) => (
                  <optgroup key={group} label={group}>
                    {opts.map((option) => (
                      <option key={option} value={option}>
                        {option}
                      </option>
                    ))}
                  </optgroup>
                ))
              : options.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
          </select>
        );
      }
      
      default:
        return (
          <input
            id={name}
            type={type}
            {...register(name)}
            className={`form-input ${error ? 'error' : ''}`}
            placeholder={placeholder}
            {...props}
          />
        )
    }
  }

  return (
    <div className="form-field">
      <label htmlFor={name} className="form-label">
        {label}
        {required && <span className="required">*</span>}
      </label>
      
      {renderInput()}
      
      {error && (
        <div className="error-message">
          {error.message}
        </div>
      )}
    </div>
  )
}

FormField.propTypes = {
  label: PropTypes.string.isRequired,
  name: PropTypes.string.isRequired,
  type: PropTypes.string,
  register: PropTypes.func.isRequired,
  error: PropTypes.shape({
    message: PropTypes.string
  }),
  required: PropTypes.bool,
  options: PropTypes.arrayOf(PropTypes.string),
  placeholder: PropTypes.string
}

export default FormField