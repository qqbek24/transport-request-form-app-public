import React from 'react';
import PropTypes from 'prop-types';
import { Controller } from 'react-hook-form';
import { Autocomplete, TextField } from '@mui/material';
import borderCrossingsData from '../../data/borderCrossings.json';
import diacriticsConfig from '../../data/diacritics.json';
import './MuiFormField.css';

const MuiBorderCrossingField = ({
  label,
  name,
  control,
  required = false,
  placeholder = 'Start typing...',
  helperText = 'Type to filter (e.g., "nadlac" → "Nădlac")',
  width
}) => {
  const [isFocused, setIsFocused] = React.useState(false);

  // Build diacritics map from JSON config (inverted format: target -> [sources])
  // JSON format: { "a": ["ă", "â", "á"], "s": ["ș", "ş"] }
  // Converts to: { "ă": "a", "â": "a", "á": "a", "ș": "s", "ş": "s" }
  const diacriticsMap = React.useMemo(() => {
    const map = {};
    Object.entries(diacriticsConfig).forEach(([target, sources]) => {
      sources.forEach(source => {
        map[source] = target;
      });
    });
    return map;
  }, []);

  // Normalize diacritics for filtering (uses external JSON config)
  const normalizeDiacritics = (text) => {
    if (!text) return '';
    
    return text
      .toLowerCase()
      .split('')
      .map(char => diacriticsMap[char] || char)
      .join('');
  };

  // Flatten grouped options into single array with country info
  const allOptions = React.useMemo(() => {
    return Object.entries(borderCrossingsData).flatMap(([country, cities]) =>
      cities.map(city => ({ label: city, country }))
    );
  }, []);

  return (
    <Controller
      name={name}
      control={control}
      render={({ field, fieldState }) => (
        <Autocomplete
          {...field}
          options={allOptions}
          groupBy={(option) => option.country}
          getOptionLabel={(option) => option?.label || ''}
          value={allOptions.find(opt => opt.label === field.value) || null}
          onChange={(event, newValue) => {
            field.onChange(newValue?.label || '');
          }}
          filterOptions={(options, state) => {
            const inputValue = normalizeDiacritics(state.inputValue);
            return options.filter(option => 
              normalizeDiacritics(option.label).includes(inputValue)
            );
          }}
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
              onBlur={() => setIsFocused(false)}
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

MuiBorderCrossingField.propTypes = {
  label: PropTypes.string.isRequired,
  name: PropTypes.string.isRequired,
  control: PropTypes.object.isRequired,
  required: PropTypes.bool,
  placeholder: PropTypes.string,
  helperText: PropTypes.string,
  width: PropTypes.string
};

export default MuiBorderCrossingField;
