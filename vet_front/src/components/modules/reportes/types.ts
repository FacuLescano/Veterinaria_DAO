export interface MuestraAnalisisKpis {
  total_muestras_extraidas: number;
  muestras_con_resultado: number;
  muestras_sin_resultado: number;
  porcentaje_con_resultado: number | null;
}

export interface EstadoRecepcionKpis {
  muestras_aceptadas: number;
  muestras_rechazadas: number;
  muestras_pendientes: number;
  porcentaje_aceptadas: number | null;
  porcentaje_rechazadas: number | null;
  tiempo_promedio_recepcion_horas: number | null;
}

export interface ActividadMedicaKpis {
  turnos_atendidos: number;
  turnos_cancelados: number;
  turnos_ausentes: number;
  total_consultas_realizadas: number;
  porcentaje_consultas_con_orden: number | null;
}

export interface SeguimientoResultadosKpis {
  resultados_recibidos: number;
  analisis_pendientes: number;
  porcentaje_con_resultado: number | null;
  tiempo_promedio_respuesta_horas: number | null;
  total_analisis_solicitados: number;
}

export interface SerieReporte<T = Record<string, string | number | null>> {
  fecha_generacion: string;
  kpis: T;
  filtros_disponibles: Record<string, string[]>;
}
