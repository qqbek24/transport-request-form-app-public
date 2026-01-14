import { createTheme } from '@mui/material/styles';

const getTheme = (mode) => createTheme({
  palette: {
    mode,
    primary: {
      main: '#ff6600',
    },
    ...(mode === 'dark' && {
      background: {
        default: '#2c3e50',
        paper: '#3a4f5f',
      },
      text: {
        primary: '#ecf0f1',
        secondary: '#bdc3c7',
      },
    }),
  },
  components: {
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          ...(mode === 'dark' && {
            color: '#bdc3c7 !important',
            '& .MuiOutlinedInput-notchedOutline': {
              borderColor: 'rgba(236, 240, 241, 0.3)',
            },
            '&:hover .MuiOutlinedInput-notchedOutline': {
              borderColor: 'rgba(236, 240, 241, 0.5)',
            },
            '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
              borderColor: '#ff6600',
              borderWidth: '2px',
            },
          }),
        },
        input: {
          ...(mode === 'dark' && {
            color: '#bdc3c7 !important',
            '&::placeholder': {
              color: '#95a5a6',
              opacity: 1,
            },
          }),
        },
      },
    },
    MuiInputLabel: {
      styleOverrides: {
        root: {
          ...(mode === 'dark' && {
            color: '#bdc3c7',
            '&.Mui-focused': {
              color: '#ff6600',
            },
          }),
        },
      },
    },
    MuiSelect: {
      styleOverrides: {
        icon: {
          ...(mode === 'dark' && {
            color: '#bdc3c7',
          }),
        },
      },
    },
  },
});

export default getTheme;
