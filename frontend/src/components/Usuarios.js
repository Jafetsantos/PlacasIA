import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  TextField,
  Box,
  Select,
  MenuItem,
} from '@mui/material';
import axios from 'axios';

const Usuarios = () => {
  const [usuarios, setUsuarios] = useState([]);
  const [filtro, setFiltro] = useState('');
  const [tipoFiltro, setTipoFiltro] = useState('nombre');

  useEffect(() => {
    const fetchUsuarios = async () => {
      try {
        const response = await axios.get('http://localhost:5000/api/usuarios');
        setUsuarios(response.data);
      } catch (error) {
        console.error('Error al obtener usuarios:', error);
      }
    };

    fetchUsuarios();
  }, []);

  const usuariosFiltrados = usuarios.filter(usuario => {
    const valorBuscado = usuario[tipoFiltro]?.toLowerCase() || '';
    return valorBuscado.includes(filtro.toLowerCase());
  });

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">Usuarios Registrados</Typography>
      </Box>

      <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
        <TextField
          label="Buscar usuarios..."
          variant="outlined"
          size="small"
          value={filtro}
          onChange={(e) => setFiltro(e.target.value)}
          sx={{ flexGrow: 1 }}
        />
        <Select
          value={tipoFiltro}
          onChange={(e) => setTipoFiltro(e.target.value)}
          size="small"
          sx={{ minWidth: 120 }}
        >
          <MenuItem value="nombre">Nombre</MenuItem>
          <MenuItem value="tipo">Tipo</MenuItem>
          <MenuItem value="placa">Placa</MenuItem>
        </Select>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Nombre</TableCell>
              <TableCell>Tipo</TableCell>
              <TableCell>Vehículo</TableCell>
              <TableCell>Placa</TableCell>
              <TableCell>Estado</TableCell>
              <TableCell>Fecha Registro</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {usuariosFiltrados.map((usuario, index) => (
              <TableRow key={index}>
                <TableCell>{usuario.nombre}</TableCell>
                <TableCell>{usuario.tipo}</TableCell>
                <TableCell>{usuario.vehiculo}</TableCell>
                <TableCell>{usuario.placa}</TableCell>
                <TableCell>
                  <Typography
                    color={usuario.estado === 'Activo' ? 'success.main' : 'error.main'}
                  >
                    {usuario.estado}
                  </Typography>
                </TableCell>
                <TableCell>{usuario.fecha_registro}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Container>
  );
};

export default Usuarios; 