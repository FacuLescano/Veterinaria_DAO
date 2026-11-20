import React from 'react';
import { ReporteGestion } from './ReporteGestion';

export const ReporteEficaciaDiagnostica: React.FC = () => <ReporteGestion
  endpoint="/api/v1/reportes/eficacia-diagnostica"
  filename="reporte_seguimiento_resultados"
  titulo="SEGUIMIENTO DE RESULTADOS DE LABORATORIO"
  subtitulo="Resultados recibidos, análisis pendientes y tiempos de respuesta registrados"
  filtros={[{ parametro: 'tipo_analisis', etiqueta: 'Tipo de análisis', opciones: 'tipos_analisis', inicial: 'Todos' }]}
  indicadores={[
    { etiqueta: 'Resultados recibidos', clave: 'resultados_recibidos' },
    { etiqueta: 'Análisis pendientes', clave: 'analisis_pendientes' },
    { etiqueta: 'Análisis con resultado', clave: 'porcentaje_con_resultado', formato: 'porcentaje' },
    { etiqueta: 'Tiempo promedio de respuesta', clave: 'tiempo_promedio_respuesta_horas', formato: 'horas' },
    { etiqueta: 'Análisis solicitados', clave: 'total_analisis_solicitados' },
  ]}
  series={[
    { titulo: 'Estado de los resultados', clave: 'estado_resultados', categoria: 'estado', valor: 'cantidad' },
    { titulo: 'Tiempo de respuesta', clave: 'tiempos_respuesta', categoria: 'período', valor: 'tiempo_promedio_horas' },
    { titulo: 'Resultados recibidos por fecha', clave: 'evolucion_resultados', categoria: 'fecha', valor: 'cantidad' },
    { titulo: 'Antigüedad de análisis pendientes (días)', clave: 'antiguedad_pendientes_dias', categoria: 'analisis', valor: 'antiguedad_dias' },
  ]}
/>;
