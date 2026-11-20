import React from 'react';
import { ReporteGestion } from './ReporteGestion';

export const ReporteTiemposSla: React.FC = () => <ReporteGestion
  endpoint="/api/v1/reportes/tiempos-sla"
  filename="reporte_muestras_y_analisis"
  titulo="ESTADÍSTICAS DE MUESTRAS Y ANÁLISIS"
  subtitulo="Muestras extraídas y resultados de laboratorio registrados"
  filtros={[{ parametro: 'tipo_analisis', etiqueta: 'Tipo de muestra', opciones: 'tipos_analisis', inicial: 'Todos' }]}
  indicadores={[
    { etiqueta: 'Muestras extraídas', clave: 'total_muestras_extraidas' },
    { etiqueta: 'Con resultado', clave: 'muestras_con_resultado' },
    { etiqueta: 'Pendientes de resultado', clave: 'muestras_sin_resultado' },
    { etiqueta: 'Muestras con resultado', clave: 'porcentaje_con_resultado', formato: 'porcentaje' },
  ]}
  series={[
    { titulo: 'Muestras extraídas por tipo', clave: 'distribucion_tipo_muestra', categoria: 'tipo_muestra', valor: 'cantidad' },
    { titulo: 'Extraídas y con resultado', clave: 'comparacion_muestras', categoria: 'estado', valor: 'cantidad' },
  ]}
/>;
