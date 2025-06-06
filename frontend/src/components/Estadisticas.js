import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Box,
  Tabs,
  Tab,
  Card,
  CardContent,
  CardHeader,
} from '@mui/material';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Line,
  LineChart,
  Legend,
} from 'recharts';
import axios from 'axios';
import StatsFilters from './StatsFilters';

const Estadisticas = () => {
  const [stats, setStats] = useState({
    total_accesos: 0,
    total_entradas: 0,
    total_salidas: 0,
    total_denegados: 0,
    grafica_data: [],
  });
  const [selectedTab, setSelectedTab] = useState('general');
  const [filtros, setFiltros] = useState({
    periodo: 'semana',
    fechaInicio: null,
    fechaFin: null,
  });
  const [datosDB, setDatosDB] = useState(null);

  const fetchStats = async (params = {}) => {
    try {
      const [statsResponse, datosDetalladosResponse] = await Promise.all([
        axios.get('http://localhost:5000/api/dashboard/stats', { params }),
        axios.get('http://localhost:5000/api/estadisticas/detalladas')
      ]);
      
      setStats(statsResponse.data);
      setDatosDB(datosDetalladosResponse.data);
    } catch (error) {
      console.error('Error al obtener estadísticas:', error);
    }
  };

  useEffect(() => {
    fetchStats(filtros);
    const interval = setInterval(() => fetchStats(filtros), 30000);
    return () => clearInterval(interval);
  }, [filtros]);

  const handleFilterChange = (newFiltros) => {
    setFiltros(newFiltros);
  };

  // Datos actualizados desde la base de datos
  const userTypeData = datosDB?.vehiculos_por_tipo?.map(item => ({
    name: item.tipo,
    accesos: item.total
  })) || [];

  const accessRatioData = datosDB?.distribucion_accesos?.map(item => ({
    name: item.tipo,
    value: item.total
  })) || [];

  const timeData = datosDB?.accesos_por_hora?.map(item => ({
    hora: item.hora,
    accesos: item.total
  })) || [];

  const COLORS = ['#4CAF50', '#F44336'];
  const VEHICLE_COLORS = ['#0088FE', '#00C49F', '#FFBB28'];

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Estadísticas
      </Typography>

      <StatsFilters onFilterChange={handleFilterChange} />
      
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
          <Tabs value={selectedTab} onChange={(e, newValue) => setSelectedTab(newValue)}>
            <Tab label="General" value="general" />
            <Tab label="Por Usuario" value="usuarios" />
            <Tab label="Por Tiempo" value="tiempo" />
            <Tab label="Por Vehículo" value="vehiculos" />
          </Tabs>
        </Box>

        {selectedTab === 'general' && (
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardHeader 
                  title="Accesos por Tipo de Usuario"
                  subheader="Distribución de accesos según el tipo de usuario"
                />
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart
                      width={500}
                      height={300}
                      data={[
                        { name: 'Estudiantes', accesos: stats.total_estudiantes || 0 },
                        { name: 'Docentes', accesos: stats.total_docentes || 0 },
                        { name: 'Administrativos', accesos: stats.total_administrativos || 0 },
                        { name: 'Visitantes', accesos: stats.total_visitantes || 0 }
                      ]}
                      margin={{
                        top: 5,
                        right: 30,
                        left: 20,
                        bottom: 5,
                      }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                      <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `${value}`} />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="accesos" fill="#1976d2" radius={[4, 4, 0, 0]} name="Accesos" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardHeader 
                  title="Proporción de Accesos"
                  subheader="Accesos permitidos vs. denegados"
                />
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={accessRatioData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        outerRadius={100}
                        fill="#8884d8"
                        dataKey="value"
                        label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      >
                        {accessRatioData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(value) => [`${value} accesos`, "Cantidad"]} />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12}>
              <Card>
                <CardHeader 
                  title="Accesos por Hora del Día"
                  subheader="Distribución de accesos según la hora del día"
                />
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={timeData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="hora" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                      <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `${value}`} />
                      <Tooltip />
                      <Line type="monotone" dataKey="accesos" stroke="#8884d8" activeDot={{ r: 8 }} name="Accesos" />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {selectedTab === 'usuarios' && (
          <Card>
            <CardHeader 
              title="Estadísticas por Usuario"
              subheader="Análisis detallado de accesos por tipo de usuario"
            />
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={datosDB?.top_usuarios || []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="usuario" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `${value}`} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="total" fill="#1976d2" radius={[4, 4, 0, 0]} name="Total de Accesos" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}

        {selectedTab === 'tiempo' && (
          <Card>
            <CardHeader 
              title="Estadísticas por Tiempo"
              subheader="Análisis detallado de accesos por hora y día"
            />
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={datosDB?.accesos_por_mes || []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="mes" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `${value}`} />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="total" stroke="#8884d8" activeDot={{ r: 8 }} name="Total de Accesos" />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}

        {selectedTab === 'vehiculos' && (
          <Card>
            <CardHeader 
              title="Estadísticas por Vehículo"
              subheader="Análisis detallado de accesos por tipo de vehículo"
            />
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <PieChart>
                  <Pie
                    data={datosDB?.vehiculos_por_tipo || []}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    outerRadius={150}
                    fill="#8884d8"
                    dataKey="total"
                    nameKey="tipo"
                    label={({ tipo, percent }) => `${tipo} ${(percent * 100).toFixed(0)}%`}
                  >
                    {(datosDB?.vehiculos_por_tipo || []).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={VEHICLE_COLORS[index % VEHICLE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => [`${value} accesos`, "Cantidad"]} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}
      </Paper>
    </Container>
  );
};

export default Estadisticas; 