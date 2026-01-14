import Box from "@mui/material/Box";
import TextField from "@mui/material/TextField";
import Autocomplete from "@mui/material/Autocomplete";
import PropTypes from 'prop-types';
import countriesListJson from '../data/Countries_List.json'

// Controlled component for react-hook-form
export default function CountrySelect({ value, onChange, name, error, label }) {
  // Find the current value object for the Autocomplete
  const currentValue = countriesListJson.find(country => country.Country_EN === value) || null;

  return (
    <Autocomplete
      id="country-select"
      size="small"
      fullWidth
      options={countriesListJson}
      value={currentValue}
      autoHighlight
      onChange={(_event, newValue) => {
        onChange(newValue ? newValue.Country_EN : '');
      }}
      getOptionLabel={(option) => option.Country_EN}
      renderOption={(props, option) => {
        /**
         * MUI passes key in props for renderOption, but it's not in prop-types by default.
         * This disables the warning for this line only.
         */
        // eslint-disable-next-line react/prop-types
        const { key, ...rest } = props;
        return (
          <Box
            key={key}
            component="li"
            sx={{ "& > img": { mr: 2, flexShrink: 0 } }}
            {...rest}
          >
            <img
              loading="lazy"
              width="20"
              srcSet={`https://flagcdn.com/w40/${option.Code_ISO.toLowerCase()}.png 2x`}
              src={`https://flagcdn.com/w20/${option.Code_ISO.toLowerCase()}.png`}
              alt=""
            />
            {option.CountryNames} ({option.Code_ISO})
          </Box>
        );
      }}
      renderInput={(params) => (
        <TextField
          {...params}
          name={name}
          label={label || "Choose a country"}
          error={!!error}
          helperText={error?.message}
          inputProps={{
            ...params.inputProps,
            //autoComplete: "new-password", // disable autocomplete and autofill
          }}
        />
      )}
    />
  );
}

CountrySelect.propTypes = {
  value: PropTypes.string,
  onChange: PropTypes.func.isRequired,
  name: PropTypes.string,
  error: PropTypes.object,
  label: PropTypes.node
};
