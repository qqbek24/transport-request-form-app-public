import React from 'react';
import PropTypes from 'prop-types';
import { Controller } from 'react-hook-form';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import './MuiFormField.css';

  const MuiDatePickerField = ({
    label,
    name,
    control,
    error,
    required = false,
    width,
    format,
  }) => {
  return (
    <Controller
      name={name}
      control={control}
      render={({ field }) => (
        <DatePicker
          {...field}
          label={label}
          value={field.value || null}
          onChange={(date) => field.onChange(date)}
          slotProps={{
            textField: {
              error: !!error,
              helperText: error?.message,
              margin: 'normal',
              size: 'small',
              required,
              className: 'mui-form-field',
              sx: theme => ({
                width: '100%',
                [theme.breakpoints.up(800)]: {
                  width: width || '50%'
                }
              }),
              InputLabelProps: {
                sx: required ? { '& .MuiFormLabel-asterisk': { color: '#dc3545' } } : undefined
              }
            },
            actionBar: { actions: ['today'] }
          }}
          format={format || 'MM/dd/yyyy'}
        />
      )}
    />
  );
};

MuiDatePickerField.propTypes = {
  label: PropTypes.string.isRequired,
  name: PropTypes.string.isRequired,
  control: PropTypes.object.isRequired,
  error: PropTypes.object,
  required: PropTypes.bool,
  width: PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.number,
  ]),
  format: PropTypes.string,
};

export default MuiDatePickerField;
