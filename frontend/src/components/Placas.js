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
  Button,
  TextField,
  Box,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Radio,
  RadioGroup,
  FormControlLabel,
  FormLabel,
  Grid,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import VisibilityIcon from '@mui/icons-material/Visibility';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import SearchIcon from '@mui/icons-material/Search';
import axios from 'axios';

const Placas = () => {
  const [placas, setPlacas] = useState([]);
  const [openDialog, setOpenDialog] = useState(false);
  const [openViewDialog, setOpenViewDialog] = useState(false);
  const [openEditDialog, setOpenEditDialog] = useState(false);
  const [selectedPlaca, setSelectedPlaca] = useState(null);
  const [filtros, setFiltros] = useState({
    texto: '',
    tipoBusqueda: 'placa',
    estado: 'todos'
  });
  const [nuevaPlaca, setNuevaPlaca] = useState({
    placa: '',
    usuario: '',
    cargo: 'Visitante',
    tipoVehiculo: 'Automóvil',
    marca: '',
    modelo: '',
    color: ''
  });

  useEffect(() => {
    fetchPlacas();
  }, []);

  const fetchPlacas = async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/placas');
      setPlacas(response.data);
    } catch (error) {
      console.error('Error al obtener placas:', error);
    }
  };

  const handleOpenDialog = () => {
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setNuevaPlaca({
      placa: '',
      usuario: '',
      cargo: 'Visitante',
      tipoVehiculo: 'Automóvil',
      marca: '',
      modelo: '',
      color: ''
    });
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setNuevaPlaca(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      // Primero registramos la placa
      const response = await fetch('http://localhost:5000/api/placas', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(nuevaPlaca)
      });

      if (response.ok) {
        const result = await response.json();
        
        // Luego registramos el acceso automáticamente
        try {
          const accesoResponse = await fetch('http://localhost:5000/api/accesos', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              placa_id: result.placa_id,
              acceso: 'Entrada'
            })
          });

          if (!accesoResponse.ok) {
            throw new Error('Error al registrar el acceso automático');
          }
        } catch (error) {
          console.error('Error al registrar acceso automático:', error);
        }

        // Actualizamos el estado y cerramos el diálogo
        setOpenDialog(false);
        setNuevaPlaca({
          placa: '',
          usuario: '',
          cargo: 'Visitante',
          tipoVehiculo: 'Automóvil',
          marca: '',
          modelo: '',
          color: ''
        });
        
        // Actualizamos las placas y forzamos una actualización del dashboard
        fetchPlacas();
        
        // Mostramos mensaje de éxito
        alert('Placa registrada exitosamente y acceso registrado automáticamente');
      } else {
        const error = await response.json();
        alert('Error al registrar la placa: ' + error.error);
      }
    } catch (error) {
      alert('Error al registrar la placa: ' + error.message);
    }
  };

  const handleViewPlaca = (placa) => {
    setSelectedPlaca(placa);
    setOpenViewDialog(true);
  };

  const handleEditPlaca = (placa) => {
    setSelectedPlaca(placa);
    setOpenEditDialog(true);
  };

  const handleDeletePlaca = async (placa) => {
    if (window.confirm(`¿Está seguro que desea eliminar la placa ${placa.placa}?`)) {
      try {
        const response = await axios.delete(`http://localhost:5000/api/placas/${placa.id}`);
        if (response.status === 200) {
          alert('Placa eliminada exitosamente');
          fetchPlacas();
        }
      } catch (error) {
        alert('Error al eliminar la placa: ' + error.message);
      }
    }
  };

  const handleUpdatePlaca = async (e) => {
    e.preventDefault();
    try {
      const placaData = {
        placa: selectedPlaca.placa,
        usuario: selectedPlaca.usuario,
        tipoVehiculo: selectedPlaca.tipo_vehiculo,
        marca: selectedPlaca.marca,
        modelo: selectedPlaca.modelo,
        color: selectedPlaca.color
      };

      const response = await axios.put(`http://localhost:5000/api/placas/${selectedPlaca.id}`, placaData);
      if (response.status === 200) {
        alert('Placa actualizada exitosamente');
        setOpenEditDialog(false);
        fetchPlacas();
      }
    } catch (error) {
      alert('Error al actualizar la placa: ' + error.message);
    }
  };

  const placasFiltradas = placas.filter(placa => {
    const cumpleFiltroTexto = filtros.tipoBusqueda === 'placa' 
      ? placa.placa.toLowerCase().includes(filtros.texto.toLowerCase())
      : filtros.tipoBusqueda === 'usuario'
      ? placa.usuario.toLowerCase().includes(filtros.texto.toLowerCase())
      : placa.tipo_vehiculo.toLowerCase().includes(filtros.texto.toLowerCase());
    
    const cumpleFiltroEstado = filtros.estado === 'todos' 
      ? true 
      : placa.estado.toLowerCase() === filtros.estado.toLowerCase();
    
    return cumpleFiltroTexto && cumpleFiltroEstado;
  });

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">PLACAS REGISTRADAS</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          sx={{ backgroundColor: '#002A5C' }}
          onClick={handleOpenDialog}
        >
          Nueva Placa
        </Button>
      </Box>

      <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
          <SearchIcon sx={{ color: 'action.active', mr: 1 }} />
          <TextField
            label="Buscar placas..."
            variant="outlined"
            size="small"
            value={filtros.texto}
            onChange={(e) => setFiltros(prev => ({ ...prev, texto: e.target.value }))}
            sx={{ flexGrow: 1 }}
          />
        </Box>
        <FormControl size="small" sx={{ minWidth: 180 }}>
          <InputLabel>Buscar por</InputLabel>
          <Select
            value={filtros.tipoBusqueda}
            label="Buscar por"
            onChange={(e) => setFiltros(prev => ({ ...prev, tipoBusqueda: e.target.value }))}
          >
            <MenuItem value="placa">Número de Placa</MenuItem>
            <MenuItem value="usuario">Usuario</MenuItem>
            <MenuItem value="tipo">Tipo de Vehículo</MenuItem>
          </Select>
        </FormControl>
        <FormControl size="small" sx={{ minWidth: 180 }}>
          <InputLabel>Estado</InputLabel>
          <Select
            value={filtros.estado}
            label="Estado"
            onChange={(e) => setFiltros(prev => ({ ...prev, estado: e.target.value }))}
          >
            <MenuItem value="todos">Todos</MenuItem>
            <MenuItem value="activo">Activo</MenuItem>
            <MenuItem value="inactivo">Inactivo</MenuItem>
          </Select>
        </FormControl>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Placa</TableCell>
              <TableCell>Usuario</TableCell>
              <TableCell>Tipo de Vehículo</TableCell>
              <TableCell>Marca</TableCell>
              <TableCell>Modelo</TableCell>
              <TableCell>Color</TableCell>
              <TableCell>Estado</TableCell>
              <TableCell>Fecha Registro</TableCell>
              <TableCell>Acciones</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {placasFiltradas.map((placa, index) => (
              <TableRow key={index}>
                <TableCell>{placa.placa}</TableCell>
                <TableCell>{placa.usuario}</TableCell>
                <TableCell>{placa.tipo_vehiculo}</TableCell>
                <TableCell>{placa.marca}</TableCell>
                <TableCell>{placa.modelo}</TableCell>
                <TableCell>{placa.color}</TableCell>
                <TableCell>
                  <Typography
                    color={placa.estado === 'Activo' ? 'success.main' : 'error.main'}
                  >
                    {placa.estado}
                  </Typography>
                </TableCell>
                <TableCell>{placa.fecha_registro}</TableCell>
                <TableCell>
                  <IconButton 
                    size="small" 
                    color="primary"
                    onClick={() => handleViewPlaca(placa)}
                  >
                    <VisibilityIcon />
                  </IconButton>
                  <IconButton 
                    size="small" 
                    color="primary"
                    onClick={() => handleEditPlaca(placa)}
                  >
                    <EditIcon />
                  </IconButton>
                  <IconButton 
                    size="small" 
                    color="error"
                    onClick={() => handleDeletePlaca(placa)}
                  >
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>Registrar Nueva Placa</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={4}>
              <TextField
                fullWidth
                label="Número de Placa"
                name="placa"
                value={nuevaPlaca.placa}
                onChange={handleInputChange}
                margin="normal"
                required
              />
              <TextField
                fullWidth
                label="Nombre de Usuario"
                name="usuario"
                value={nuevaPlaca.usuario}
                onChange={handleInputChange}
                margin="normal"
                required
                helperText="Si el usuario no existe, se creará automáticamente"
              />
              <FormControl fullWidth margin="normal" required>
                <InputLabel>Cargo</InputLabel>
                <Select
                  name="cargo"
                  value={nuevaPlaca.cargo}
                  onChange={handleInputChange}
                >
                  <MenuItem value="Estudiante">Estudiante</MenuItem>
                  <MenuItem value="Docente">Docente</MenuItem>
                  <MenuItem value="Administrativo">Administrativo</MenuItem>
                  <MenuItem value="Visitante">Visitante</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={4}>
              <FormControl component="fieldset" margin="normal" required>
                <FormLabel component="legend">Tipo de Vehículo</FormLabel>
                <RadioGroup
                  name="tipoVehiculo"
                  value={nuevaPlaca.tipoVehiculo}
                  onChange={handleInputChange}
                >
                  <FormControlLabel value="Automóvil" control={<Radio />} label="Automóvil" />
                  <FormControlLabel value="Motocicleta" control={<Radio />} label="Motocicleta" />
                  <FormControlLabel value="Otro" control={<Radio />} label="Otro" />
                </RadioGroup>
              </FormControl>
            </Grid>
            
            <Grid item xs={4}>
              <TextField
                fullWidth
                label="Marca"
                name="marca"
                value={nuevaPlaca.marca}
                onChange={handleInputChange}
                margin="normal"
                required
              />
              <TextField
                fullWidth
                label="Modelo"
                name="modelo"
                value={nuevaPlaca.modelo}
                onChange={handleInputChange}
                margin="normal"
                required
              />
              <TextField
                fullWidth
                label="Color"
                name="color"
                value={nuevaPlaca.color}
                onChange={handleInputChange}
                margin="normal"
                required
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancelar</Button>
          <Button onClick={handleSubmit} variant="contained" color="primary">
            Registrar
          </Button>
        </DialogActions>
      </Dialog>

      {/* Diálogo para ver detalles */}
      <Dialog open={openViewDialog} onClose={() => setOpenViewDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Detalles de la Placa</DialogTitle>
        <DialogContent>
          {selectedPlaca && (
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={6}>
                <Typography variant="subtitle1" gutterBottom>
                  <strong>Número de Placa:</strong> {selectedPlaca.placa}
                </Typography>
                <Typography variant="subtitle1" gutterBottom>
                  <strong>Usuario:</strong> {selectedPlaca.usuario}
                </Typography>
                <Typography variant="subtitle1" gutterBottom>
                  <strong>Tipo de Vehículo:</strong> {selectedPlaca.tipo_vehiculo}
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="subtitle1" gutterBottom>
                  <strong>Marca:</strong> {selectedPlaca.marca}
                </Typography>
                <Typography variant="subtitle1" gutterBottom>
                  <strong>Modelo:</strong> {selectedPlaca.modelo}
                </Typography>
                <Typography variant="subtitle1" gutterBottom>
                  <strong>Color:</strong> {selectedPlaca.color}
                </Typography>
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenViewDialog(false)}>Cerrar</Button>
        </DialogActions>
      </Dialog>

      {/* Diálogo para editar */}
      <Dialog open={openEditDialog} onClose={() => setOpenEditDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Editar Placa</DialogTitle>
        <DialogContent>
          {selectedPlaca && (
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={4}>
                <TextField
                  fullWidth
                  label="Número de Placa"
                  value={selectedPlaca.placa}
                  onChange={(e) => setSelectedPlaca({...selectedPlaca, placa: e.target.value})}
                  margin="normal"
                  required
                />
                <TextField
                  fullWidth
                  label="Nombre de Usuario"
                  value={selectedPlaca.usuario}
                  onChange={(e) => setSelectedPlaca({...selectedPlaca, usuario: e.target.value})}
                  margin="normal"
                  required
                />
              </Grid>
              <Grid item xs={4}>
                <FormControl fullWidth margin="normal" required>
                  <InputLabel>Tipo de Vehículo</InputLabel>
                  <Select
                    value={selectedPlaca.tipo_vehiculo}
                    onChange={(e) => setSelectedPlaca({...selectedPlaca, tipo_vehiculo: e.target.value})}
                  >
                    <MenuItem value="Automóvil">Automóvil</MenuItem>
                    <MenuItem value="Motocicleta">Motocicleta</MenuItem>
                    <MenuItem value="Otro">Otro</MenuItem>
                  </Select>
                </FormControl>
                <TextField
                  fullWidth
                  label="Marca"
                  value={selectedPlaca.marca}
                  onChange={(e) => setSelectedPlaca({...selectedPlaca, marca: e.target.value})}
                  margin="normal"
                  required
                />
              </Grid>
              <Grid item xs={4}>
                <TextField
                  fullWidth
                  label="Modelo"
                  value={selectedPlaca.modelo}
                  onChange={(e) => setSelectedPlaca({...selectedPlaca, modelo: e.target.value})}
                  margin="normal"
                  required
                />
                <TextField
                  fullWidth
                  label="Color"
                  value={selectedPlaca.color}
                  onChange={(e) => setSelectedPlaca({...selectedPlaca, color: e.target.value})}
                  margin="normal"
                  required
                />
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenEditDialog(false)}>Cancelar</Button>
          <Button onClick={handleUpdatePlaca} variant="contained" color="primary">
            Guardar Cambios
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default Placas; 