import React, { useState, useEffect } from 'react'
import { ThemeProvider } from '@mui/material/styles';
import { styled } from '@mui/material/styles';
import Switch from '@mui/material/Switch';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import TransportForm from './components/TransportForm/TransportForm'
import LogsViewer from './components/LogsViewer/LogsViewer'
import getTheme from './theme'
import './App.css'

const AntSwitch = styled(Switch)(({ theme }) => ({
  width: 28,
  height: 16,
  padding: 0,
  display: 'flex',
  '&:active': {
    '& .MuiSwitch-thumb': {
      width: 15,
    },
    '& .MuiSwitch-switchBase.Mui-checked': {
      transform: 'translateX(9px)',
    },
  },
  '& .MuiSwitch-switchBase': {
    padding: 2,
    '&.Mui-checked': {
      transform: 'translateX(12px)',
      color: '#fff',
      '& + .MuiSwitch-track': {
        opacity: 1,
        backgroundColor: theme.palette.primary.main,
        ...theme.applyStyles('dark', {
          backgroundColor: theme.palette.primary.main,
        }),
      },
    },
  },
  '& .MuiSwitch-thumb': {
    boxShadow: '0 2px 4px 0 rgb(0 35 11 / 20%)',
    width: 12,
    height: 12,
    borderRadius: 6,
    transition: theme.transitions.create(['width'], {
      duration: 200,
    }),
  },
  '& .MuiSwitch-track': {
    borderRadius: 16 / 2,
    opacity: 1,
    backgroundColor: 'rgba(0,0,0,.25)',
    boxSizing: 'border-box',
    ...theme.applyStyles('dark', {
      backgroundColor: 'rgba(255,255,255,.35)',
    }),
  },
}));

function App() {
  const [themeMode, setThemeMode] = useState('light');
  const [footerText, setFooterText] = useState('© 2025 Transport Request System. All rights reserved.');
  
  useEffect(() => {
    const savedMode = localStorage.getItem('themeMode');
    if (savedMode) {
      setThemeMode(savedMode);
    }
  }, []);
  
  useEffect(() => {
    fetch('/footer.txt')
      .then(response => response.text())
      .then(text => setFooterText(text.trim()))
      .catch(err => console.error('Failed to load footer text:', err));
  }, []);
  
  const toggleTheme = () => {
    const newMode = themeMode === 'light' ? 'dark' : 'light';
    setThemeMode(newMode);
    localStorage.setItem('themeMode', newMode);
  };
  
  const theme = getTheme(themeMode);
  
  return (
    <ThemeProvider theme={theme}>
      <div className={`App ${themeMode}`}>
        <header className="App-header">
          <h1>UIT-RO Transport Form</h1>
          <p>Please fill out the form below for transport registration</p>
        </header>
        <div className="theme-switch-container">
          <Stack direction="row" spacing={1} sx={{ alignItems: 'center', justifyContent: 'center' }}>
            <Typography sx={{ fontSize: '0.9rem', fontWeight: 500 }}>Light</Typography>
            <AntSwitch
              checked={themeMode === 'dark'}
              onChange={toggleTheme}
              inputProps={{ 'aria-label': 'theme switch' }}
            />
            <Typography sx={{ fontSize: '0.9rem', fontWeight: 500 }}>Dark</Typography>
          </Stack>
        </div>
        <main>
          <TransportForm />
        </main>
        <footer className="App-footer">
          <p>{footerText}</p>
        </footer>
        <LogsViewer />
      </div>
    </ThemeProvider>
  )
}

export default App