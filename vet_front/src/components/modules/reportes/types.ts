// Tipos para Reportes de Gestión y Auditoría

// ==========================================
// Reporte 1: Tiempos de Tránsito y SLA
// ==========================================

export interface KpiData {
  total_muestras_analizadas: number;
  total_muestras_registradas: number;
  tiempo_promedio_transito_horas: number;
  tiempo_promedio_procesamiento_horas: number;
  tiempo_promedio_total_horas: number;
  tasa_cumplimiento_sla_porcentaje: number;
  muestras_en_plazo: number;
  muestras_demoradas: number;
}

export interface SlaPorTipo {
  tipo_analisis: string;
  cantidad_muestras: number;
  tiempo_transito_promedio_horas: number;
  tiempo_procesamiento_promedio_horas: number;
  tiempo_total_promedio_horas: number;
  sla_objetivo_horas: number;
  cumplimiento_porcentaje: number;
  estado_sla: 'Cumplido' | 'En riesgo' | 'Excedido';
}

export interface RendimientoTransportista {
  transportista: string;
  envios_realizados: number;
  muestras_transportadas: number;
  tiempo_promedio_viaje_horas: number;
  puntualidad_porcentaje: number;
}

export interface DetalleMuestraReporte {
  muestra_codigo: string;
  paciente_nombre: string;
  especie: string;
  tutor_nombre: string;
  tipo_analisis: string;
  prioridad: 'Normal' | 'Urgente';
  transportista: string;
  remito_numero: string;
  fecha_despacho: string;
  fecha_recepcion_lab: string;
  fecha_resultado: string;
  tiempo_transito_horas: number;
  tiempo_procesamiento_horas: number;
  tiempo_total_horas: number;
  sla_objetivo_horas: number;
  diferencia_sla_horas: number;
  cumple_sla: boolean;
  estado_analisis: string;
}

export interface ReporteTiemposResponse {
  fecha_generacion: string;
  kpis: KpiData;
  sla_por_tipo_analisis: SlaPorTipo[];
  rendimiento_transportistas: RendimientoTransportista[];
  detalles_muestras: DetalleMuestraReporte[];
  filtros_disponibles: {
    tipos_analisis: string[];
    transportistas: string[];
    prioridades: string[];
  };
}

// ==========================================
// Reporte 2: Muestras Rechazadas & Bioseguridad
// ==========================================

export interface KpiRechazadasData {
  total_muestras_auditadas: number;
  muestras_aceptadas: number;
  muestras_rechazadas: number;
  tasa_rechazo_global_porcentaje: number;
  tasa_conformidad_porcentaje: number;
  precintos_integros: number;
  precintos_violados_o_rotos: number;
  integridad_precintos_porcentaje: number;
  temperaturas_en_rango: number;
  excursiones_termicas: number;
  conformidad_cadena_frio_porcentaje: number;
}

export interface CausaRechazoDistribucion {
  causa: string;
  cantidad: number;
  porcentaje: number;
  severidad: 'Crítica' | 'Moderada';
}

export interface ConfiabilidadTransportista {
  transportista: string;
  total_muestras: number;
  muestras_conformes: number;
  muestras_rechazadas: number;
  tasa_conformidad_porcentaje: number;
  tasa_rechazo_porcentaje: number;
  falla_frecuente: string;
  calificacion: 'Excelente' | 'Aceptable' | 'Crítico';
}

export interface DetalleMuestraRechazada {
  muestra_codigo: string;
  paciente_nombre: string;
  especie: string;
  tutor_nombre: string;
  tipo_analisis: string;
  transportista: string;
  remito_numero: string;
  conservadora_codigo: string;
  precinto_esperado: string;
  precinto_observado: string;
  estado_precinto: 'Integro' | 'Roto' | 'Ausente';
  temperatura_salida_c: number;
  temperatura_llegada_c: number;
  temperatura_conforme: boolean;
  rango_admitido: string;
  estado_muestra: 'Rechazada' | 'Aceptada';
  causa_rechazo: string | null;
  fecha_evento: string;
  accion_correctiva: string;
}

export interface ReporteRechazadasResponse {
  fecha_generacion: string;
  kpis: KpiRechazadasData;
  distribucion_causas_rechazo: CausaRechazoDistribucion[];
  confiabilidad_transportistas: ConfiabilidadTransportista[];
  detalles_auditoria: DetalleMuestraRechazada[];
  filtros_disponibles: {
    causas: string[];
    transportistas: string[];
    estados: string[];
  };
}

