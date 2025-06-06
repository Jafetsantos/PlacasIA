import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  List,
  ListItem,
  Avatar,
  Chip,
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
  Legend,
  LineChart,
  Line,
} from 'recharts';
import PersonAddIcon from '@mui/icons-material/PersonAdd';
import DirectionsCarIcon from '@mui/icons-material/DirectionsCar';
import HistoryIcon from '@mui/icons-material/History';
import AssessmentIcon from '@mui/icons-material/Assessment';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import GroupIcon from '@mui/icons-material/Group';
import ExitToAppIcon from '@mui/icons-material/ExitToApp';
import TimelineIcon from '@mui/icons-material/Timeline';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const Dashboard = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    total_accesos: 0,
    total_entradas: 0,
    total_salidas: 0,
    total_denegados: 0,
    total_estudiantes: 0,
    total_docentes: 0,
    total_administrativos: 0,
    total_visitantes: 0
  });
  const [accesosRecientes, setAccesosRecientes] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsResponse, accesosResponse] = await Promise.all([
          axios.get('http://localhost:5000/api/dashboard/stats'),
          axios.get('http://localhost:5000/api/accesos')
        ]);
        
        // Asegurarse de que las salidas se carguen correctamente
        const statsData = statsResponse.data;
        if (typeof statsData.total_salidas === 'undefined' || statsData.total_salidas === null) {
          statsData.total_salidas = 0;
        }
        
        setStats(statsData);
        
        // Filtrar y formatear los accesos recientes
        const accesosFiltrados = accesosResponse.data
          .slice(0, 5)
          .map(acceso => {
            // Determinar el estado basado en la fecha de salida y el estado
            let estado = 'Entrada';
            if (acceso.salida) {
              estado = 'Salida';
            } else if (acceso.estado === 'Denegado') {
              estado = 'Denegado';
            }
            
            return {
              ...acceso,
              estado: estado
            };
          });
        
        setAccesosRecientes(accesosFiltrados);
      } catch (error) {
        console.error('Error al obtener datos:', error);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const StatCard = ({ title, value, subtitle, color, icon: Icon }) => (
    <Card sx={{ bgcolor: color, color: 'white' }}>
      <CardHeader
        title={title}
        action={<Icon />}
        sx={{ pb: 0 }}
      />
      <CardContent>
        <Typography variant="h4" sx={{ mb: 1 }}>{value}</Typography>
        <Typography variant="body2">{subtitle}</Typography>
      </CardContent>
    </Card>
  );

  const QuickAction = ({ icon: Icon, title, onClick, color, variant = "contained", sx }) => (
    <Button
      variant={variant}
      startIcon={<Icon />}
      onClick={onClick}
      fullWidth
      sx={{
        py: 1.5,
        justifyContent: 'flex-start',
        backgroundColor: variant === 'contained' ? color : 'transparent',
        color: variant === 'contained' ? 'white' : color,
        '&:hover': {
          backgroundColor: variant === 'contained' ? color : 'rgba(0, 0, 0, 0.04)',
          filter: variant === 'contained' ? 'brightness(0.9)' : 'none',
          ...sx
        },
      }}
    >
      {title}
    </Button>
  );

  return (
    <Box sx={{ 
      p: 6,
      maxWidth: '100%',
      margin: '0 auto',
      width: '100%'
    }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h3" sx={{ 
          color: 'primary.main', 
          fontWeight: 'bold',
          fontSize: '2.5rem'
        }}>
          SISTEMA DE CONTROL DE ACCESO VEHICULAR
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ fontSize: '1.1rem' }}>
          Bienvenido al sistema de control de acceso vehicular de UNAH
        </Typography>
      </Box>

      <Box sx={{ 
        display: 'flex', 
        gap: 3, 
        flexDirection: 'column',
        maxWidth: '95%',
        margin: '0 auto'
      }}>
        {/* Tarjetas de estadísticas */}
        <Grid container spacing={2} sx={{ 
          width: '100%', 
          display: 'flex', 
          flexDirection: 'row', 
          flexWrap: 'nowrap',
          justifyContent: 'space-between'
        }}>
          <Grid item sx={{ flex: 1, maxWidth: 'calc(25% - 8px)' }}>
            <Card sx={{ 
              bgcolor: '#FFC107', 
              color: 'white',
              height: '100%',
              minHeight: '110px'
            }}>
              <CardHeader
                title="Total de Accesos Hoy"
                action={<AccessTimeIcon />}
                sx={{ 
                  pb: 0,
                  pt: 1,
                  '& .MuiCardHeader-content': { 
                    fontSize: '0.9rem'
                  },
                  '& .MuiCardHeader-title': {
                    fontSize: '1.1rem'
                  },
                  '& .MuiCardHeader-action': {
                    marginTop: 0,
                    marginRight: 0
                  }
                }}
              />
              <CardContent sx={{ pt: 0.5, pb: 1 }}>
                <Typography variant="h3" sx={{ mb: 0.2, fontSize: '2rem' }}>{stats.total_accesos}</Typography>
                <Typography variant="body2" sx={{ fontSize: '0.9rem' }}>Vehículos registrados</Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item sx={{ flex: 1, maxWidth: 'calc(25% - 8px)' }}>
            <Card sx={{ 
              bgcolor: '#4CAF50', 
              color: 'white',
              height: '100%',
              minHeight: '110px'
            }}>
              <CardHeader
                title="Entradas Hoy"
                action={<GroupIcon />}
                sx={{ 
                  pb: 0,
                  pt: 1,
                  '& .MuiCardHeader-content': { 
                    fontSize: '0.9rem'
                  },
                  '& .MuiCardHeader-title': {
                    fontSize: '1.1rem'
                  },
                  '& .MuiCardHeader-action': {
                    marginTop: 0,
                    marginRight: 0
                  }
                }}
              />
              <CardContent sx={{ pt: 0.5, pb: 1 }}>
                <Typography variant="h3" sx={{ mb: 0.2, fontSize: '2rem' }}>{stats.total_entradas}</Typography>
                <Typography variant="body2" sx={{ fontSize: '0.9rem' }}>Entradas registradas</Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item sx={{ flex: 1, maxWidth: 'calc(25% - 8px)' }}>
            <Card sx={{ 
              bgcolor: '#5DADE2', 
              color: 'white',
              height: '100%',
              minHeight: '110px'
            }}>
              <CardHeader
                title="Salidas Hoy"
                action={<ExitToAppIcon />}
                sx={{ 
                  pb: 0,
                  pt: 1,
                  '& .MuiCardHeader-content': { 
                    fontSize: '0.9rem'
                  },
                  '& .MuiCardHeader-title': {
                    fontSize: '1.1rem'
                  },
                  '& .MuiCardHeader-action': {
                    marginTop: 0,
                    marginRight: 0
                  }
                }}
              />
              <CardContent sx={{ pt: 0.5, pb: 1 }}>
                <Typography variant="h3" sx={{ mb: 0.2, fontSize: '2rem' }}>{stats.total_salidas}</Typography>
                <Typography variant="body2" sx={{ fontSize: '0.9rem' }}>Salidas registradas</Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item sx={{ flex: 1, maxWidth: 'calc(25% - 8px)' }}>
            <Card sx={{ 
              bgcolor: '#F44336', 
              color: 'white',
              height: '100%',
              minHeight: '110px'
            }}>
              <CardHeader
                title="Accesos Denegados"
                action={<TimelineIcon />}
                sx={{ 
                  pb: 0,
                  pt: 1,
                  '& .MuiCardHeader-content': { 
                    fontSize: '0.9rem'
                  },
                  '& .MuiCardHeader-title': {
                    fontSize: '1.1rem'
                  },
                  '& .MuiCardHeader-action': {
                    marginTop: 0,
                    marginRight: 0
                  }
                }}
              />
              <CardContent sx={{ pt: 0.5, pb: 1 }}>
                <Typography variant="h3" sx={{ mb: 0.2, fontSize: '2rem' }}>{stats.total_denegados}</Typography>
                <Typography variant="body2" sx={{ fontSize: '0.9rem' }}>Accesos no autorizados hoy</Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Gráfico y Accesos Recientes */}
        <Box sx={{ display: 'flex', gap: 3, mt: 3 }}>
          {/* Gráfico */}
          <Box sx={{ flex: 1 }}>
            <Typography variant="h6" sx={{ mb: 1 }}>Detección de Placas</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Accesos por día durante la última semana
            </Typography>
            <Box sx={{ height: '300px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={[
                    { name: 'Estudiantes', accesos: stats.total_estudiantes },
                    { name: 'Docentes', accesos: stats.total_docentes },
                    { name: 'Administrativos', accesos: stats.total_administrativos },
                    { name: 'Visitantes', accesos: stats.total_visitantes }
                  ]}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="accesos" fill="#4A90E2" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Box>
          </Box>

          {/* Accesos Recientes */}
          <Box sx={{ flex: 1 }}>
            <Typography variant="h6" sx={{ mb: 1 }}>Accesos Recientes</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Últimos registros de entrada y salida
            </Typography>
            <Box sx={{ 
              height: '300px',
              overflow: 'auto',
              '&::-webkit-scrollbar': {
                width: '8px',
              },
              '&::-webkit-scrollbar-track': {
                background: '#f1f1f1',
              },
              '&::-webkit-scrollbar-thumb': {
                background: '#888',
                borderRadius: '4px',
              },
              '&::-webkit-scrollbar-thumb:hover': {
                background: '#555',
              },
            }}>
              <List sx={{ bgcolor: 'background.paper', borderRadius: 1 }}>
                {accesosRecientes.map((acceso, index) => (
                  <ListItem 
                    key={index} 
                    sx={{ 
                      borderBottom: '1px solid #eee', 
                      py: 2,
                      '&:last-child': {
                        borderBottom: 'none'
                      }
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                      <Avatar sx={{ 
                        bgcolor: acceso.estado === 'Entrada' ? '#4CAF50' : 
                                acceso.estado === 'Salida' ? '#5DADE2' : 
                                '#F44336', 
                        mr: 2 
                      }}>
                        {acceso.estado === 'Entrada' ? 'E' : 
                         acceso.estado === 'Salida' ? 'S' : 'D'}
                      </Avatar>
                      <Box sx={{ flexGrow: 1 }}>
                        <Typography variant="subtitle1" sx={{ fontWeight: 'medium' }}>
                          {acceso.usuario}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Placa: {acceso.placa}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {acceso.entrada}
                        </Typography>
                      </Box>
                      <Chip 
                        label={acceso.estado}
                        color={acceso.estado === 'Entrada' ? 'success' : 
                               acceso.estado === 'Salida' ? 'info' : 
                               'error'}
                        size="small"
                        sx={{ minWidth: '80px' }}
                      />
                    </Box>
                  </ListItem>
                ))}
              </List>
            </Box>
            <Button 
              variant="contained" 
              fullWidth 
              sx={{ 
                mt: 2,
                bgcolor: '#FFC107',
                '&:hover': {
                  bgcolor: '#FFB000'
                }
              }}
              onClick={() => navigate('/accesos')}
            >
              Ver todos los accesos
            </Button>
          </Box>
        </Box>

        {/* Acciones Rápidas */}
        <Box sx={{ mt: 3 }}>
          <Card>
            <CardHeader 
              title="Acciones Rápidas"
              sx={{
                '& .MuiCardHeader-title': {
                  fontSize: '1.25rem',
                  fontWeight: 'bold'
                }
              }}
            />
            <CardContent>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <QuickAction
                  icon={DirectionsCarIcon}
                  title="Registrar Nueva Placa"
                  onClick={() => navigate('/placas')}
                  color="#FFC107"
                  sx={{
                    '&:hover': {
                      bgcolor: '#FFB000'
                    }
                  }}
                />
                <QuickAction
                  icon={HistoryIcon}
                  title="Ver Historial de Accesos"
                  onClick={() => navigate('/accesos')}
                  color="#FFC107"
                  sx={{
                    '&:hover': {
                      bgcolor: '#FFB000'
                    }
                  }}
                />
                <QuickAction
                  icon={AssessmentIcon}
                  title="Ver Estadísticas"
                  onClick={() => navigate('/estadisticas')}
                  color="#FFC107"
                  sx={{
                    '&:hover': {
                      bgcolor: '#FFB000'
                    }
                  }}
                />
              </Box>
            </CardContent>
          </Card>
        </Box>
      </Box>
    </Box>
  );
};

export default Dashboard; 