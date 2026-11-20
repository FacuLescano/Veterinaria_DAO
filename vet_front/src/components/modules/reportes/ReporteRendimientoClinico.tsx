import React from 'react';
import { ReporteGestion } from './ReporteGestion';

export const ReporteRendimientoClinico: React.FC = () => <ReporteGestion
  endpoint="/api/v1/reportes/rendimiento-clinico"
  filename="reporte_actividad_medica"
  titulo="ACTIVIDAD MÉDICA Y CONSULTAS"
  subtitulo="Turnos, consultas realizadas y solicitudes de análisis"
  filtros={[
    { parametro: 'veterinario', etiqueta: 'Profesional', opciones: 'veterinarios', inicial: 'Todos' },
    { parametro: 'estado_turno', etiqueta: 'Estado del turno', opciones: 'estados_turno', inicial: 'Todos' },
    { parametro: 'derivacion', etiqueta: 'Orden de análisis', opciones: 'derivaciones', inicial: 'Todos' },
  ]}
  indicadores={[
    { etiqueta: 'Turnos realizados', clave: 'turnos_atendidos' },
    { etiqueta: 'Turnos cancelados', clave: 'turnos_cancelados' },
    { etiqueta: 'Ausencias', clave: 'turnos_ausentes' },
    { etiqueta: 'Consultas realizadas', clave: 'total_consultas_realizadas' },
    { etiqueta: 'Consultas con orden de análisis', clave: 'porcentaje_consultas_con_orden', formato: 'porcentaje' },
  ]}
  series={[
    { titulo: 'Actividad de turnos', clave: 'distribucion_estados_turno', categoria: 'estado', valor: 'cantidad' },
    { titulo: 'Consultas por hora del día', clave: 'actividad_por_hora', categoria: 'hora', valor: 'cantidad' },
    { titulo: 'Consultas y órdenes de análisis', clave: 'comparacion_consultas_ordenes', categoria: 'estado', valor: 'cantidad' },
    { titulo: 'Consultas realizadas por profesional', clave: 'rendimiento_veterinarios', categoria: 'veterinario_nombre', valor: 'consultas_realizadas' },
  ]}
/>;
