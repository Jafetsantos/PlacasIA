import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Box } from '@mui/material';

import Navbar from './components/Navbar';
import Dashboard from './components/Dashboard';
import Usuarios from './components/Usuarios';
import Placas from './components/Placas';
import Accesos from './components/Accesos';
import Estadisticas from './components/Estadisticas';

// Tema personalizado
const theme = createTheme({
  palette: {
    primary: {
      main: '#002A5C', // Color principal UNAH
    },
    secondary: {
      main: '#FFC107',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
          <Navbar />
          <Box component="main" sx={{ flexGrow: 1, bgcolor: 'background.default', p: 3 }}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/usuarios" element={<Usuarios />} />
              <Route path="/placas" element={<Placas />} />
              <Route path="/accesos" element={<Accesos />} />
              <Route path="/estadisticas" element={<Estadisticas />} />
            </Routes>
          </Box>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;
