import React from 'react';
import PropTypes from 'prop-types';
import { Controller } from 'react-hook-form';
import { Autocomplete, TextField, Chip } from '@mui/material';
import './MuiFormField.css';

const MuiChipInputField = ({
  label,
  name,
  control,
  required = false,
  placeholder = 'Type and press Enter...',
  helperText = 'Press Enter to add each number. Paste multiple: comma, semicolon, or new line.',
  width
}) => {
  const [isFocused, setIsFocused] = React.useState(false);
  const [inputValue, setInputValue] = React.useState('');

  return (
    <Controller
      name={name}
      control={control}
      render={({ field, fieldState }) => (
        <Autocomplete
          {...field}
          multiple
          freeSolo
          options={[]}
          value={field.value || []}
          inputValue={inputValue}
          onInputChange={(event, newInputValue, reason) => {
            // Don't update input value when chip is being created (reason: 'reset')
            if (reason !== 'reset') {
              setInputValue(newInputValue);
            }
          }}
          onChange={(event, newValue) => {
            // Handle paste with separators (comma, semicolon, newline)
            const processed = newValue.flatMap(val => {
              if (typeof val === 'string') {
                // Split by comma, semicolon, or newline
                return val.split(/[,;\n]+/).map(v => v.trim()).filter(Boolean);
              }
              return val;
            });
            // Remove duplicates
            const unique = [...new Set(processed)];
            field.onChange(unique);
            // Clear input after adding chip
            setInputValue('');
          }}
          renderTags={(value, getTagProps) =>
            value.map((option, index) => {
              const { key, ...tagProps } = getTagProps({ index });
              return (
                <Chip
                  key={key}
                  label={option}
                  {...tagProps}
                  sx={{ margin: '2px' }}
                />
              );
            })
          }
          renderInput={(params) => (
            <TextField
              {...params}
              label={
                required ? (
                  <span>
                    {label} <span className="MuiFormLabel-asterisk">*</span>
                  </span>
                ) : label
              }
              error={!!fieldState.error}
              helperText={
                fieldState.error?.message || 
                (isFocused ? helperText : ' ')
              }
              margin="normal"
              size="small"
              placeholder={placeholder}
              onFocus={() => setIsFocused(true)}
              onBlur={(e) => {
                setIsFocused(false);
                // Add current input as chip on blur if not empty
                const currentInput = inputValue.trim();
                if (currentInput) {
                  // Split by separators and add to existing values
                  const newItems = currentInput.split(/[,;\n]+/).map(v => v.trim()).filter(Boolean);
                  const currentValues = field.value || [];
                  const combined = [...currentValues, ...newItems];
                  // Remove duplicates
                  const unique = [...new Set(combined)];
                  field.onChange(unique);
                  setInputValue('');
                }
              }}
              className="mui-form-field"
            />
          )}
          sx={theme => ({
            width: '100%',
            [theme.breakpoints.up(800)]: {
              width: width || '50%'
            }
          })}
          className="mui-form-field"
        />
      )}
    />
  );
};

MuiChipInputField.propTypes = {
  label: PropTypes.string.isRequired,
  name: PropTypes.string.isRequired,
  control: PropTypes.object.isRequired,
  required: PropTypes.bool,
  placeholder: PropTypes.string,
  helperText: PropTypes.string,
  width: PropTypes.string
};

export default MuiChipInputField;
