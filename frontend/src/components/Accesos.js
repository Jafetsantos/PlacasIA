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
  Box,
  TextField,
  Button,
  Select,
  MenuItem,
  IconButton,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import PrintIcon from '@mui/icons-material/Print';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import TableChartIcon from '@mui/icons-material/TableChart';
import axios from 'axios';

const Accesos = () => {
  const [accesos, setAccesos] = useState([]);
  const [filtros, setFiltros] = useState({
    busqueda: '',
    tipo: 'todos',
    fechaInicio: null,
    fechaFin: null,
  });

  useEffect(() => {
    const fetchAccesos = async () => {
      try {
        const response = await axios.get('http://localhost:5000/api/accesos');
        setAccesos(response.data);
      } catch (error) {
        console.error('Error al obtener accesos:', error);
      }
    };

    fetchAccesos();
  }, []);

  const accesosFiltrados = accesos.filter(acceso => {
    const cumpleBusqueda = acceso.usuario.toLowerCase().includes(filtros.busqueda.toLowerCase()) ||
                          acceso.placa.toLowerCase().includes(filtros.busqueda.toLowerCase());
    const cumpleTipo = filtros.tipo === 'todos' || acceso.tipo === filtros.tipo;
    
    return cumpleBusqueda && cumpleTipo;
  });

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Historial de Accesos
      </Typography>

      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <TextField
            label="Buscar"
            variant="outlined"
            size="small"
            value={filtros.busqueda}
            onChange={(e) => setFiltros({ ...filtros, busqueda: e.target.value })}
            sx={{ flexGrow: 1, minWidth: 200 }}
          />
          <Select
            value={filtros.tipo}
            onChange={(e) => setFiltros({ ...filtros, tipo: e.target.value })}
            size="small"
            sx={{ minWidth: 150 }}
          >
            <MenuItem value="todos">Todos</MenuItem>
            <MenuItem value="Estudiante">Estudiante</MenuItem>
            <MenuItem value="Empleado">Empleado</MenuItem>
            <MenuItem value="Visitante">Visitante</MenuItem>
          </Select>
          <LocalizationProvider dateAdapter={AdapterDateFns}>
            <DatePicker
              label="Fecha Inicio"
              value={filtros.fechaInicio}
              onChange={(date) => setFiltros({ ...filtros, fechaInicio: date })}
              renderInput={(params) => <TextField {...params} size="small" />}
            />
            <DatePicker
              label="Fecha Fin"
              value={filtros.fechaFin}
              onChange={(date) => setFiltros({ ...filtros, fechaFin: date })}
              renderInput={(params) => <TextField {...params} size="small" />}
            />
          </LocalizationProvider>
          <Button variant="contained" color="primary">
            Filtrar
          </Button>
        </Box>
      </Paper>

      <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1, mb: 2 }}>
        <IconButton title="Imprimir">
          <PrintIcon />
        </IconButton>
        <IconButton title="Exportar a PDF">
          <PictureAsPdfIcon />
        </IconButton>
        <IconButton title="Exportar a Excel">
          <TableChartIcon />
        </IconButton>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Usuario</TableCell>
              <TableCell>Placa</TableCell>
              <TableCell>Tipo</TableCell>
              <TableCell>Entrada</TableCell>
              <TableCell>Salida</TableCell>
              <TableCell>Estado</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {accesosFiltrados.map((acceso, index) => (
              <TableRow key={index}>
                <TableCell>{acceso.usuario}</TableCell>
                <TableCell>{acceso.placa}</TableCell>
                <TableCell>{acceso.tipo}</TableCell>
                <TableCell>{acceso.entrada}</TableCell>
                <TableCell>{acceso.salida || '—'}</TableCell>
                <TableCell>
                  <Typography
                    color={acceso.estado === 'Permitido' ? 'success.main' : 'error.main'}
                  >
                    {acceso.estado}
                  </Typography>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Container>
  );
};

export default Accesos; 