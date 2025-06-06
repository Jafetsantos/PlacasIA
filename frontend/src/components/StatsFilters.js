import React from 'react';
import {
  Box,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Button,
  Grid,
} from '@mui/material';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { es } from 'date-fns/locale';

const StatsFilters = ({ onFilterChange }) => {
  const [periodo, setPeriodo] = React.useState('semana');
  const [fechaInicio, setFechaInicio] = React.useState(null);
  const [fechaFin, setFechaFin] = React.useState(null);

  const handlePeriodoChange = (event) => {
    const newPeriodo = event.target.value;
    setPeriodo(newPeriodo);
    
    if (newPeriodo !== 'personalizado') {
      setFechaInicio(null);
      setFechaFin(null);
      onFilterChange({
        periodo: newPeriodo,
        fechaInicio: null,
        fechaFin: null
      });
    }
  };

  const handleFechaChange = (tipo, fecha) => {
    if (tipo === 'inicio') {
      setFechaInicio(fecha);
    } else {
      setFechaFin(fecha);
    }

    if (periodo === 'personalizado') {
      onFilterChange({
        periodo,
        fechaInicio: tipo === 'inicio' ? fecha : fechaInicio,
        fechaFin: tipo === 'fin' ? fecha : fechaFin
      });
    }
  };

  const handleLimpiar = () => {
    setPeriodo('semana');
    setFechaInicio(null);
    setFechaFin(null);
    onFilterChange({
      periodo: 'semana',
      fechaInicio: null,
      fechaFin: null
    });
  };

  return (
    <Card sx={{ mb: 3 }}>
      <CardContent sx={{ pt: 3 }}>
        <Grid container spacing={3} alignItems="flex-end">
          <Grid item xs={12} md={3}>
            <FormControl fullWidth>
              <InputLabel>Período</InputLabel>
              <Select
                value={periodo}
                label="Período"
                onChange={handlePeriodoChange}
              >
                <MenuItem value="dia">Hoy</MenuItem>
                <MenuItem value="semana">Esta semana</MenuItem>
                <MenuItem value="mes">Este mes</MenuItem>
                <MenuItem value="anio">Este año</MenuItem>
                <MenuItem value="personalizado">Personalizado</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          {periodo === 'personalizado' && (
            <>
              <Grid item xs={12} md={3}>
                <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={es}>
                  <DatePicker
                    label="Fecha inicio"
                    value={fechaInicio}
                    onChange={(date) => handleFechaChange('inicio', date)}
                    renderInput={(params) => <TextField {...params} fullWidth />}
                  />
                </LocalizationProvider>
              </Grid>

              <Grid item xs={12} md={3}>
                <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={es}>
                  <DatePicker
                    label="Fecha fin"
                    value={fechaFin}
                    onChange={(date) => handleFechaChange('fin', date)}
                    renderInput={(params) => <TextField {...params} fullWidth />}
                    minDate={fechaInicio}
                  />
                </LocalizationProvider>
              </Grid>
            </>
          )}

          <Grid item xs={12} md={periodo === 'personalizado' ? 3 : 9}>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button
                variant="contained"
                color="primary"
                fullWidth
                onClick={() => onFilterChange({ periodo, fechaInicio, fechaFin })}
              >
                Aplicar
              </Button>
              <Button
                variant="outlined"
                color="primary"
                fullWidth
                onClick={handleLimpiar}
              >
                Limpiar
              </Button>
            </Box>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

export default StatsFilters; 