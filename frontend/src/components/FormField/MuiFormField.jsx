import React from 'react';
import PropTypes from 'prop-types';
import TextField from '@mui/material/TextField';
import MenuItem from '@mui/material/MenuItem';
import FormControl from '@mui/material/FormControl';
import CountrySelect from '../dropDownCountry';
import MuiDatePickerField from './MuiDatePickerField';
import { Controller } from 'react-hook-form';
import './MuiFormField.css';

const MuiFormField = ({
  label,
  name,
  type = 'text',
  control,
  error,
  required = false,
  options = [],
  width,
  ...props
}) => {
  if (type === 'date') {
    return (
      <MuiDatePickerField
        label={label}
        name={name}
        control={control}
        error={error}
        required={required}
      />
    );
  }

  if (type === 'country') {
    return (
      <FormControl
        margin="normal"
        error={!!error}
        className="mui-form-field"
        sx={theme => ({
          width: '100%',
          [theme.breakpoints.up(800)]: {
            width: width || '50%'
          }
        })}
      >
        <Controller
          name={name}
          control={control}
          render={({ field, fieldState }) => (
            <CountrySelect
              value={field.value || ''}
              onChange={field.onChange}
              name={name}
              error={fieldState.error}
              label={
                required ? (
                  <span>
                    {label} <span className="MuiFormLabel-asterisk">*</span>
                  </span>
                ) : label
              }
            />
          )}
        />
        {error && <div className="mui-form-field-error">{error.message}</div>}
      </FormControl>
    );
  }

  if (type === 'select') {
    // Support both array and grouped object for options
    const isGrouped = options && typeof options === 'object' && !Array.isArray(options);
    return (
      <Controller
        name={name}
        control={control}
        render={({ field }) => (
          <TextField
            {...field}
            select
            label={label}
            error={!!error}
            helperText={error?.message}
            margin="normal"
            size="small"
            className="mui-form-field"
            sx={theme => ({
              width: '100%',
              [theme.breakpoints.up(800)]: {
                width: width || '50%'
              }
            })}
            required={required}
            // Nie ustawiamy className na InputLabelProps, by nie nadawać koloru całemu labelowi
          >
            <MenuItem value=""><em>None</em></MenuItem>
            {isGrouped
              ? Object.entries(options).flatMap(([group, opts]) => [
                  <MenuItem key={group} value={group} disabled style={{ fontStyle: 'italic', fontWeight: 'bold', color: '#888' }}>
                    {group}
                  </MenuItem>,
                  ...opts.map((option) => (
                    <MenuItem key={group + '-' + option} value={option} style={{ paddingLeft: 32 }}>{option}</MenuItem>
                  ))
                ])
              : options.map((option) => (
                  <MenuItem key={option} value={option}>{option}</MenuItem>
                ))}
          </TextField>
        )}
      />
    );
  }

  // Default: text field
  return (
    <FormControl fullWidth margin="normal" error={!!error} className="mui-form-field">
      <Controller
        name={name}
        control={control}
        render={({ field }) => (
          <TextField
            {...field}
            size="small"
            label={label}
            error={!!error}
            helperText={error?.message}
            required={required}
            {...props}
            // Nie ustawiamy InputLabelProps.className, by nie nadawać klasy całemu labelowi
          />
        )}
      />
    </FormControl>
  );
};

MuiFormField.propTypes = {
  label: PropTypes.string.isRequired,
  name: PropTypes.string.isRequired,
  type: PropTypes.string,
  control: PropTypes.object.isRequired,
  error: PropTypes.object,
  required: PropTypes.bool,
  options: PropTypes.oneOfType([
    PropTypes.array,
    PropTypes.object
  ]),
  width: PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.number
  ])
};

export default MuiFormField;
