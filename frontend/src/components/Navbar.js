import React from 'react';
import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material';
import { Link } from 'react-router-dom';

const Navbar = () => {
  return (
    <AppBar position="static" sx={{ backgroundColor: '#002A5C' }}>
      <Toolbar>
        <Box sx={{ display: 'flex', alignItems: 'center', mr: 2 }}>
          <img 
            src="/UNAH-version-horizontal.png" 
            alt="Logo UNAH" 
            style={{ height: '40px', width: 'auto' }} 
          />
        </Box>
        
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Control de Acceso
        </Typography>
        <Box>
          <Button color="inherit" component={Link} to="/">
            Dashboard
          </Button>
          <Button color="inherit" component={Link} to="/usuarios">
            Usuarios
          </Button>
          <Button color="inherit" component={Link} to="/placas">
            Placas
          </Button>
          <Button color="inherit" component={Link} to="/accesos">
            Accesos
          </Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Navbar; 