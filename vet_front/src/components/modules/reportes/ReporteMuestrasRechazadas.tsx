import React from 'react';
import { ReporteGestion } from './ReporteGestion';

export const ReporteMuestrasRechazadas: React.FC = () => <ReporteGestion
  endpoint="/api/v1/reportes/muestras-rechazadas"
  filename="reporte_recepcion_muestras"
  titulo="RECEPCIÓN DE MUESTRAS EN LABORATORIO"
  subtitulo="Estado de recepción y tiempo desde la extracción hasta el ingreso"
  filtros={[
    { parametro: 'transportista', etiqueta: 'Transportista', opciones: 'transportistas', inicial: 'Todos' },
    { parametro: 'estado', etiqueta: 'Estado de recepción', opciones: 'estados', inicial: 'Todos' },
  ]}
  indicadores={[
    { etiqueta: 'Muestras aceptadas', clave: 'muestras_aceptadas', subclave: 'porcentaje_aceptadas', subformato: 'porcentaje', subetiqueta: 'Porcentaje de las recibidas' },
    { etiqueta: 'Muestras rechazadas', clave: 'muestras_rechazadas', subclave: 'porcentaje_rechazadas', subformato: 'porcentaje', subetiqueta: 'Porcentaje de las recibidas' },
    { etiqueta: 'Pendientes de recepción', clave: 'muestras_pendientes' },
    { etiqueta: 'Tiempo promedio de recepción', clave: 'tiempo_promedio_recepcion_horas', formato: 'horas' },
  ]}
  series={[
    { titulo: 'Estado de recepción', clave: 'distribucion_estados_recepcion', categoria: 'estado', valor: 'cantidad' },
    { titulo: 'Tiempo de recepción', clave: 'tiempos_recepcion', categoria: 'estado', valor: 'tiempo_promedio_horas' },
  ]}
/>;
