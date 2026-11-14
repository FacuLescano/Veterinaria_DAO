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

// ==========================================
// Reporte 3: Rendimiento Clínico & Derivación Médica
// ==========================================

export interface KpiRendimientoClinicoData {
  total_turnos_agendados: number;
  turnos_atendidos: number;
  turnos_ausentes: number;
  turnos_cancelados: number;
  tasa_ausentismo_porcentaje: number;
  tasa_asistencia_porcentaje: number;
  total_consultas_realizadas: number;
  consultas_con_derivacion: number;
  tasa_derivacion_global_porcentaje: number;
  total_ordenes_laboratorio: number;
  total_estudios_solicitados: number;
  promedio_estudios_por_orden: number;
}

export interface RendimientoVeterinario {
  veterinario_nombre: string;
  matricula: string;
  especialidad: string;
  turnos_asignados: number;
  turnos_atendidos: number;
  turnos_ausentes: number;
  turnos_cancelados: number;
  tasa_asistencia_porcentaje: number;
  consultas_con_derivacion: number;
  tasa_derivacion_porcentaje: number;
  total_ordenes_emitidas: number;
  total_estudios_solicitados: number;
  estudio_frecuente: string;
  perfil_prescriptivo: string;
}

export interface EstudioPrescripto {
  tipo_analisis: string;
  cantidad: number;
  porcentaje: number;
}

export interface DistribucionEstadoTurno {
  estado: string;
  cantidad: number;
  porcentaje: number;
}

export interface DetalleConsultaReporte {
  turno_id: string;
  fecha_hora: string;
  paciente_nombre: string;
  especie: string;
  tutor_nombre: string;
  veterinario_nombre: string;
  matricula: string;
  especialidad: string;
  estado_turno: string;
  motivo_consulta: string;
  diagnostico: string;
  derivo_laboratorio: boolean;
  orden_numero: string;
  estudios_lista: string[];
  estudios_solicitados: string;
}

export interface ReporteRendimientoClinicoResponse {
  fecha_generacion: string;
  kpis: KpiRendimientoClinicoData;
  rendimiento_veterinarios: RendimientoVeterinario[];
  top_estudios_prescriptos: EstudioPrescripto[];
  distribucion_estados_turno: DistribucionEstadoTurno[];
  detalles_consultas: DetalleConsultaReporte[];
  filtros_disponibles: {
    veterinarios: string[];
    especialidades: string[];
    estados_turno: string[];
    derivaciones: string[];
  };
}

// ==========================================
// Reporte 4: Eficacia Diagnóstica & Hallazgos Críticos
// ==========================================

export interface KpiEficaciaData {
  total_estudios_procesados: number;
  total_con_hallazgos_criticos: number;
  total_fisiologicos_normales: number;
  tasa_positividad_porcentaje: number;
  tasa_concordancia_diagnostica: number;
  total_especies_auditadas: number;
}

export interface DesgloseEspecie {
  especie: string;
  total_estudios: number;
  patologicos: number;
  normales: number;
  tasa_positividad_porcentaje: number;
  patologia_predominante: string;
}

export interface DesgloseGrupoEtario {
  grupo_etario: string;
  total_estudios: number;
  patologicos: number;
  normales: number;
  tasa_positividad_porcentaje: number;
}

export interface AnalitoCritico {
  parametro: string;
  tipo_analisis: string;
  frecuencia_alerta: number;
  porcentaje_incidencia: number;
  tipo_alerta_predominante: 'Alto' | 'Bajo';
}

export interface DistribucionSeveridad {
  severidad: 'Crítico' | 'Moderado' | 'Normal';
  cantidad: number;
  porcentaje: number;
}

export interface ParametroAlerta {
  parametro: string;
  valor: string;
  unidad: string;
  rangoReferencia: string;
  alerta: 'Alto' | 'Bajo' | 'Normal' | 'Crítico';
}

export interface DetalleDiagnostico {
  resultado_id: string;
  orden_codigo: string;
  fecha_emision: string;
  paciente_nombre: string;
  especie: string;
  raza: string;
  edad_anios: number;
  grupo_etario: string;
  tutor_nombre: string;
  veterinario_nombre: string;
  motivo_consulta: string;
  diagnostico_presuntivo: string;
  tipo_analisis: string;
  parametros_resumen: string;
  parametros_alterados: string[];
  lista_parametros_alerta: ParametroAlerta[];
  estado_diagnostico: 'Hallazgo Patológico' | 'Fisiológico Normal';
  severidad: 'Crítico' | 'Moderado' | 'Normal';
  concordancia: string;
  conclusion_laboratorio: string;
}

export interface ReporteEficaciaResponse {
  fecha_generacion: string;
  kpis: KpiEficaciaData;
  desglose_por_especie: DesgloseEspecie[];
  desglose_por_grupo_etario: DesgloseGrupoEtario[];
  top_analitos_criticos: AnalitoCritico[];
  distribucion_severidad: DistribucionSeveridad[];
  detalles_diagnosticos: DetalleDiagnostico[];
  filtros_disponibles: {
    especies: string[];
    grupos_etarios: string[];
    estados_diagnosticos: string[];
    tipos_analisis: string[];
  };
}



