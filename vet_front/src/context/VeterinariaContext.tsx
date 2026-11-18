import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import {
  Responsable,
  Mascota,
  Turno,
  ConsultaMedica,
  OrdenAnalisis,
  MuestraBiologica,
  Conservadora,
  RemitoBiologico,
  PrecintoSanitario,
  Incidencia,
  ResultadoAnalisis,
  EstadoTurno,
  EstadoPrecinto,
  EstadoMuestra,
  EstadoOrden,
  TipoAnalisis
} from '../types/veterinaria';
import {
  parseCurrentRoute,
  navigateToRoute,
  MODULE_ROUTES,
  REPORTE_ROUTES,
  ReporteTabId
} from '../utils/navigation';

export type ActiveModule = 'pacientes' | 'ordenes' | 'despacho' | 'recepcion' | 'notificaciones' | 'reportes' | 'python';

interface ToastMessage {
  id: string;
  type: 'success' | 'warning' | 'error' | 'info';
  title: string;
  description?: string;
}

interface VeterinariaContextType {
  responsables: Responsable[];
  mascotas: Mascota[];
  turnos: Turno[];
  consultas: ConsultaMedica[];
  ordenes: OrdenAnalisis[];
  muestras: MuestraBiologica[];
  conservadoras: Conservadora[];
  precintos: PrecintoSanitario[];
  remitos: RemitoBiologico[];
  incidencias: Incidencia[];
  resultados: ResultadoAnalisis[];
  
  // Navigation & UI state
  activeModule: ActiveModule;
  setActiveModule: (module: ActiveModule) => void;
  activeReportTab: ReporteTabId;
  setActiveReportTab: (tab: ReporteTabId) => void;
  isSidebarCollapsed: boolean;
  setIsSidebarCollapsed: (collapsed: boolean | ((prev: boolean) => boolean)) => void;
  isMobileMenuOpen: boolean;
  setIsMobileMenuOpen: (open: boolean) => void;
  selectedMascotaId: string | null;
  setSelectedMascotaId: (id: string | null) => void;
  toast: ToastMessage | null;
  showToast: (toast: Omit<ToastMessage, 'id'>) => void;
  clearToast: () => void;

  // Actions
  addResponsable: (resp: Omit<Responsable, 'id' | 'fechaAlta'>) => Promise<Responsable>;
  addMascota: (mascota: Omit<Mascota, 'id'>) => Promise<Mascota>;
  updateMascota: (id: string, updates: Partial<Mascota>) => Promise<void>;
  addTurno: (turno: Omit<Turno, 'id'>) => Promise<{ success: boolean; error?: string }>;
  updateTurnoEstado: (id: string, nuevoEstado: EstadoTurno) => Promise<void>;
  addConsulta: (consulta: Omit<ConsultaMedica, 'id'>) => Promise<ConsultaMedica>;
  createOrden: (orden: Omit<OrdenAnalisis, 'id'>) => Promise<OrdenAnalisis>;
  registrarMuestra: (muestra: Omit<MuestraBiologica, 'id' | 'historialTrazabilidad' | 'estadoActual'>) => Promise<MuestraBiologica>;
  vincularMuestraConAnalisis: (ordenId: string, detalleId: string, muestraId: string) => Promise<void>;
  prepararEnvio: (params: {
    conservadoraId: string;
    precintoCodigo: string;
    responsableDespacho: string;
    transportista: string;
    muestrasIds: string[];
    temperaturaDespachoC: number;
    observaciones?: string;
  }) => Promise<RemitoBiologico>;
  verificarPrecintoYRecepcion: (params: {
    remitoId: string;
    estadoPrecinto: EstadoPrecinto;
    verificadoPor: string;
    observaciones?: string;
  }) => Promise<void>;
  registrarResultado: (resultado: Omit<ResultadoAnalisis, 'id'>) => Promise<ResultadoAnalisis>;
  recibirResultadosLaboratorio: (muestraId: string, escenario: string) => Promise<void>;
  resolverIncidencia: (id: string, resolucion: string) => Promise<void>;
  reloadFromDatabase: () => void;
}

const VeterinariaContext = createContext<VeterinariaContextType | undefined>(undefined);

async function errorApi(response: Response): Promise<string> {
  try {
    const body = await response.json();
    return typeof body.detail === 'string' ? body.detail : `Error HTTP ${response.status}: ${JSON.stringify(body.detail || body)}`;
  } catch {
    return `Error HTTP ${response.status}`;
  }
}

async function api<T = any>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: { ...(init?.body ? { 'Content-Type': 'application/json' } : {}), ...init?.headers },
  });
  if (!response.ok) throw new Error(await errorApi(response));
  if (response.status === 204) return undefined as T;
  return response.json();
}

const estadoTitulo = (value: string | undefined) => (value || '').replaceAll('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase());
const fechaLocal = (value: string | undefined) => value ? value.replace('T', ' ').slice(0, 16) : '';

function mapMuestra(m: any, envio?: any): MuestraBiologica {
  const estados: Record<string, EstadoMuestra> = {
    extraida: 'Extraída', pendiente_preparacion: 'Extraída', lista_para_envio: 'Extraída', empaquetada: 'Empaquetada', enviada: 'En tránsito', en_transito: 'En tránsito', recibida: 'Recibida', analizada: 'Analizada', rechazada: 'Rechazada', con_inconveniente: 'Rechazada',
  };
  return {
    id: String(m.id), ordenId: String(m.orden_id), identificacionFisica: m.codigo_etiqueta,
    tipoMaterial: m.tipo_muestra?.nombre || '', fechaHoraExtraccion: fechaLocal(m.fecha_extraccion),
    responsableExtraccion: m.responsable_extraccion, condicionConservacion: m.condiciones_conservacion,
    estadoActual: estados[m.estado] || 'Extraída', conservadoraId: envio ? String(envio.conservadoras?.[0]?.conservadora?.id || '') : undefined,
    remitoId: envio?.remito?.numero, historialTrazabilidad: (m.historial || []).map((h: any) => ({
      id: String(h.id), fechaHora: fechaLocal(h.changed_at), estadoAnterior: h.estado_anterior ? estados[h.estado_anterior] : undefined,
      estadoNuevo: estados[h.estado_nuevo] || 'Extraída', responsable: h.responsable || '', ubicacion: '', observaciones: h.motivo || '',
    })), observaciones: m.observaciones_calidad,
  };
}

function mapOrden(o: any): OrdenAnalisis {
  const estados: Record<string, EstadoOrden> = { solicitada: 'Solicitada', en_preparacion: 'En preparación', enviada: 'Enviada', con_resultados: 'Con resultados', cancelada: 'Cancelada' };
  return {
    id: String(o.id), consultaId: String(o.consulta_id), mascotaId: String(o.paciente_id || ''),
    veterinarioSolicitante: o.veterinario_nombre || '', fechaSolicitud: fechaLocal(o.created_at), prioridad: o.observaciones?.toLowerCase().includes('urgente') ? 'Urgente' : 'Normal',
    estado: estados[o.estado] || 'Solicitada', detalles: (o.detalles || []).map((d: any) => ({
      id: String(d.id), tipoAnalisis: (d.tipo_analisis?.nombre || '') as TipoAnalisis, indicaciones: d.indicaciones || '',
      muestraAsociadaId: d.asociaciones_muestras?.[0] ? String(d.asociaciones_muestras[0].muestra_id) : undefined,
      estado: d.estado === 'resultado_listo' ? 'Resultado listo' : d.tiene_muestra ? 'Muestra vinculada' : 'Pendiente de muestra',
    })),
  };
}

function mapEnvio(e: any, recibido: boolean, incidenciasM4: any[]): RemitoBiologico {
  const contenido = e.remito?.contenido || {};
  const firstSeal = e.precintos?.[0];
  const hasIncident = incidenciasM4.some((i) => String(i.envio_id) === String(e.id) && !i.resuelta_en);
  return {
    id: e.remito?.numero || String(e.id), envioId: String(e.id), numeroRemito: e.remito?.numero,
    fechaEmision: fechaLocal(e.fecha_despacho || e.fecha_creacion), clinicaOrigen: e.origen, laboratorioDestino: e.destino,
    responsableDespacho: e.responsable_despacho || '', transportista: e.transportista || '',
    conservadoraId: String(firstSeal?.conservadora_id || e.conservadoras?.[0]?.conservadora?.id || ''),
    precintoCodigo: firstSeal?.codigo || '', muestrasIds: (e.muestras || []).map((m: any) => String(m.id)),
    estado: hasIncident ? 'Con incidencias' : recibido ? 'Recibido' : e.estado === 'despachado' ? 'Despachado' : 'En preparación',
    temperaturaDespachoC: e.registros_temperatura?.[0]?.temperatura_medida_c ?? 4,
    observaciones: e.observaciones || contenido.condiciones_empaquetado,
  };
}

export const VeterinariaProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Operational state starts empty and is populated exclusively from the API.
  const [responsables, setResponsables] = useState<Responsable[]>([]);
  const [mascotas, setMascotas] = useState<Mascota[]>([]);
  const [turnos, setTurnos] = useState<Turno[]>([]);
  const [consultas, setConsultas] = useState<ConsultaMedica[]>([]);
  const [ordenes, setOrdenes] = useState<OrdenAnalisis[]>([]);
  const [muestras, setMuestras] = useState<MuestraBiologica[]>([]);
  const [conservadoras, setConservadoras] = useState<Conservadora[]>([]);
  const [precintos, setPrecintos] = useState<PrecintoSanitario[]>([]);
  const [remitos, setRemitos] = useState<RemitoBiologico[]>([]);
  const [incidencias, setIncidencias] = useState<Incidencia[]>([]);
  const [resultados, setResultados] = useState<ResultadoAnalisis[]>([]);

  // UI & Navigation state sincronizado con URL
  const initialRoute = parseCurrentRoute();
  const [activeModule, setActiveModuleState] = useState<ActiveModule>(initialRoute.module);
  const [activeReportTab, setActiveReportTabState] = useState<ReporteTabId>(initialRoute.reporteTab || 'reporte1');
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [selectedMascotaId, setSelectedMascotaId] = useState<string | null>(null);
  const [toast, setToast] = useState<ToastMessage | null>(null);
  const veterinariosApiRef = useRef<any[]>([]);

  const setActiveModule = (mod: ActiveModule) => {
    setActiveModuleState(mod);
    if (mod === 'reportes') {
      navigateToRoute(REPORTE_ROUTES[activeReportTab] || '/reportes/1');
    } else if (mod === 'python') {
      navigateToRoute('/docs');
    } else {
      navigateToRoute(MODULE_ROUTES[mod] || `/${mod}`);
    }
  };

  const setActiveReportTab = (tab: ReporteTabId) => {
    setActiveReportTabState(tab);
    if (activeModule !== 'reportes') {
      setActiveModuleState('reportes');
    }
    navigateToRoute(REPORTE_ROUTES[tab]);
  };

  useEffect(() => {
    const handleUrlChange = () => {
      const route = parseCurrentRoute();
      setActiveModuleState(route.module);
      if (route.reporteTab) {
        setActiveReportTabState(route.reporteTab);
      }
    };

    window.addEventListener('popstate', handleUrlChange);
    return () => window.removeEventListener('popstate', handleUrlChange);
  }, []);

  useEffect(() => {
    let activo = true;
    const cargarDatos = async () => {
      try {
        const [responsablesApi, mascotasApi, veterinariosApi, turnosApi, consultasApi, ordenesApi, tiposAnalisisApi, tiposMuestraApi, enviosApi, conservadorasApi, pendientesApi, incidenciasApi, resultadosApi] = await Promise.all([
          api('/api/v1/responsables'), api('/api/v1/mascotas'), api('/api/v1/veterinarios'), api('/api/v1/turnos'), api('/api/v1/consultas'),
          api('/api/v1/ordenes-analisis'), api('/api/v1/tipos-analisis'), api('/api/v1/tipos-muestra'),
          api('/api/v1/envios'), api('/api/v1/conservadoras'), api('/api/v1/envios-pendientes'),
          api('/api/v1/incidencias'), api('/api/v1/resultados'),
        ]);
        if (!activo) return;
        setResponsables(responsablesApi.map((r: any): Responsable => ({ id: String(r.id), nombreCompleto: r.full_name, documento: r.document_number, telefono: r.phone, email: r.email || '', domicilio: r.address || '', fechaAlta: '' })));
        setMascotas(mascotasApi.map((m: any): Mascota => ({ id: String(m.id), responsableId: String(m.responsible_id), nombre: m.name, especie: m.species as Mascota['especie'], raza: m.breed || '', sexo: (m.sex || 'Hembra') as Mascota['sexo'], fechaNacimientoAprox: m.birth_date || '', pesoKg: m.weight_kg || 0, microchip: m.microchip || '', alergias: m.notes || '', fotoUrl: m.photo_url || '' })));
        veterinariosApiRef.current = veterinariosApi;
        setTurnos(turnosApi.map((t: any): Turno => ({ id: String(t.id), mascotaId: String(t.pet_id), responsableId: String(mascotasApi.find((m: any) => m.id === t.pet_id)?.responsible_id || ''), veterinario: veterinariosApi.find((v: any) => v.id === t.veterinarian_id)?.full_name || String(t.veterinarian_id), fecha: t.scheduled_at.slice(0, 10), hora: t.scheduled_at.slice(11, 16), motivo: t.reason || '', estado: estadoTitulo(t.status) as EstadoTurno })));
        setConsultas(consultasApi.map((c: any): ConsultaMedica => ({ id: String(c.id), mascotaId: String(c.pet_id), veterinario: veterinariosApi.find((v: any) => v.id === c.veterinarian_id)?.full_name || String(c.veterinarian_id), fecha: c.attended_at.slice(0, 10), hora: c.attended_at.slice(11, 16), motivo: c.reason, evaluacionClinica: c.observations || '', diagnosticoPresuntivo: c.diagnosis || '', tratamiento: c.treatment || '', requiereAnalisis: false, turnoId: c.appointment_id ? String(c.appointment_id) : undefined })));
        setOrdenes(ordenesApi.map(mapOrden));
        setMuestras(ordenesApi.flatMap((o: any) => (o.muestras || []).map((m: any) => mapMuestra(m, enviosApi.find((e: any) => e.muestras?.some((em: any) => em.id === m.id))))));
        setConservadoras(conservadorasApi.map((c: any): Conservadora => ({ id: String(c.id), nombre: c.descripcion || c.codigo, capacidadMuestras: 20, temperaturaRequerida: '2°C a 8°C', disponible: c.disponible })));
        const pendingIds = new Set(pendientesApi.map((e: any) => String(e.envio_id)));
        setRemitos(enviosApi.map((e: any) => mapEnvio(e, e.estado === 'despachado' && !pendingIds.has(String(e.id)), incidenciasApi)));
        setPrecintos(enviosApi.flatMap((e: any) => (e.precintos || []).map((p: any) => ({ id: String(p.id), codigoUnico: p.codigo, conservadoraId: String(p.conservadora_id), colocadoPor: p.colocado_por, fechaHoraColocacion: fechaLocal(p.fecha_colocacion), estadoVerificacion: p.verificaciones?.length ? estadoTitulo(p.verificaciones[p.verificaciones.length - 1].resultado) as EstadoPrecinto : undefined }))));
        setIncidencias(incidenciasApi.map((i: any): Incidencia => ({ id: String(i.id), fechaHora: fechaLocal(i.fecha), remitoId: String(i.envio_id), muestraId: i.muestra_id ? String(i.muestra_id) : undefined, tipo: 'Discrepancia en Remito', descripcion: i.descripcion, responsableReporte: i.responsable_id, resuelto: Boolean(i.resuelta_en), resolucion: i.resolucion || undefined })));
        setResultados(resultadosApi.map((r: any): ResultadoAnalisis => ({ id: String(r.id), ordenId: String(r.orden_id), detalleAnalisisId: String(r.detalle_orden_id), muestraId: String(r.muestra_id || ''), fechaRecepcionResultado: fechaLocal(r.fecha_recepcion), laboratorioNombre: r.procedencia, valores: r.datos.valores || [], conclusionDiagnostica: r.datos.conclusionDiagnostica || '', nombreArchivoAdjunto: r.informe_nombre || undefined, estado: r.estado === 'validado' ? 'Validado por Veterinario' : r.estado === 'en_revision' ? 'En revisión' : 'Recibido', validadoPor: r.registrado_por })));

        // Bootstrap only operational catalogs/equipment, never fake patient records.
        const sampleNames = ['Sangre con EDTA (Tubo lila)', 'Suero sanguíneo (Tubo rojo)', 'Plasma heparinizado', 'Orina por cistocentesis', 'Materia fecal', 'Biopsia / Tejido en formol', 'Raspado cutáneo'];
        const analysisNames = ['Hemograma Completo', 'Perfil Bioquímico Hepático', 'Perfil Renal (Urea y Creatinina)', 'Orina Completa y Sedimento', 'Coproparasitológico Seriado', 'Citología Cutánea / PAAF', 'Dosaje Hormonal (T4 / Cortisol)'];
        const sampleIds = [...tiposMuestraApi];
        for (const nombre of sampleNames) if (!sampleIds.some((t: any) => t.nombre === nombre)) sampleIds.push(await api('/api/v1/tipos-muestra', { method: 'POST', body: JSON.stringify({ nombre, condiciones_conservacion_default: 'Refrigerada (2° a 8°C)' }) }));
        for (const nombre of analysisNames) if (!tiposAnalisisApi.some((t: any) => t.nombre === nombre)) await api('/api/v1/tipos-analisis', { method: 'POST', body: JSON.stringify({ nombre, tipos_muestra_compatibles_ids: sampleIds.map((t: any) => t.id) }) });
        const defaultCoolers = [
          ['CON-01', 'Conservadora Isotérmica Azul A1'],
          ['CON-02', 'Conservadora Isotérmica Roja B2'],
          ['CON-03', 'Conservadora Portátil C3'],
        ];
        for (const [codigo, descripcion] of defaultCoolers) {
          if (!conservadorasApi.some((c: any) => c.codigo === codigo)) await api('/api/v1/conservadoras', { method: 'POST', body: JSON.stringify({ codigo, descripcion }) });
        }
        const conservadorasFinal = await api('/api/v1/conservadoras');
        if (activo) setConservadoras(conservadorasFinal.map((c: any): Conservadora => ({ id: String(c.id), nombre: c.descripcion || c.codigo, capacidadMuestras: 20, temperaturaRequerida: '2°C a 8°C', disponible: c.disponible })));
      } catch (error) {
        if (activo) showToast({ type: 'warning', title: 'No se pudieron cargar los datos de SQLite', description: error instanceof Error ? error.message : 'Verificá que el backend esté activo.' });
      }
    };
    void cargarDatos();
    return () => { activo = false; };
  }, []);

  // Auto-dismiss toast
  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 4000);
      return () => clearTimeout(timer);
    }
  }, [toast]);

  const showToast = (t: Omit<ToastMessage, 'id'>) => {
    setToast({ ...t, id: Date.now().toString() });
  };

  const clearToast = () => setToast(null);

  const obtenerVeterinarioId = async (nombre: string): Promise<number> => {
    const existente = veterinariosApiRef.current.find((v) => v.full_name.toLowerCase() === nombre.toLowerCase());
    if (existente) return existente.id;
    const license = `MP-${nombre.toLowerCase().replace(/[^a-z0-9]+/g, '-').slice(0, 50)}`;
    const creado = await api('/api/v1/veterinarios', { method: 'POST', body: JSON.stringify({ full_name: nombre, license_number: license }) });
    veterinariosApiRef.current = [...veterinariosApiRef.current, creado];
    return creado.id;
  };

  const obtenerTipoAnalisisId = async (nombre: string): Promise<number> => {
    const tipos = await api<any[]>('/api/v1/tipos-analisis');
    const existente = tipos.find((t) => t.nombre === nombre);
    if (existente) return existente.id;
    const creado = await api('/api/v1/tipos-analisis', { method: 'POST', body: JSON.stringify({ nombre }) });
    return creado.id;
  };

  const obtenerTipoMuestraId = async (nombre: string): Promise<number> => {
    const tipos = await api<any[]>('/api/v1/tipos-muestra');
    const existente = tipos.find((t) => t.nombre === nombre);
    if (existente) return existente.id;
    const creado = await api('/api/v1/tipos-muestra', { method: 'POST', body: JSON.stringify({ nombre, condiciones_conservacion_default: 'Refrigerada (2° a 8°C)' }) });
    return creado.id;
  };

  // ACTIONS

  const addResponsable = async (data: Omit<Responsable, 'id' | 'fechaAlta'>): Promise<Responsable> => {
    const response = await fetch('/api/v1/responsables', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ document_number: data.documento, full_name: data.nombreCompleto, phone: data.telefono, email: data.email || null, address: data.domicilio || null }),
    });
    if (!response.ok) throw new Error(await errorApi(response));
    const saved = await response.json();
    const newResp: Responsable = {
      ...data, id: String(saved.id), fechaAlta: new Date().toISOString().split('T')[0],
    };
    setResponsables(prev => [newResp, ...prev]);
    showToast({
      type: 'success',
      title: 'Responsable registrado',
      description: `${newResp.nombreCompleto} ha sido registrado exitosamente.`
    });
    return newResp;
  };

  const addMascota = async (data: Omit<Mascota, 'id'>): Promise<Mascota> => {
    if (!Number.isInteger(Number(data.responsableId))) {
      throw new Error('Esperá a que carguen los responsables desde el backend y volvé a intentar.');
    }
    const response = await fetch('/api/v1/mascotas', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        responsible_id: Number(data.responsableId), name: data.nombre, species: data.especie,
        breed: data.raza || null, sex: data.sexo, birth_date: data.fechaNacimientoAprox || null,
        notes: data.alergias || null, weight_kg: data.pesoKg || null,
        microchip: data.microchip || null, photo_url: data.fotoUrl || null,
      }),
    });
    if (!response.ok) throw new Error(await errorApi(response));
    const saved = await response.json();
    const newMascota: Mascota = {
      ...data, id: String(saved.id),
    };
    setMascotas(prev => [newMascota, ...prev]);
    showToast({
      type: 'success',
      title: 'Mascota registrada',
      description: `${newMascota.nombre} ya tiene su ficha en la clínica.`
    });
    return newMascota;
  };

  const updateMascota = async (id: string, updates: Partial<Mascota>) => {
    const payload: Record<string, unknown> = {};
    if (updates.responsableId !== undefined) payload.responsible_id = Number(updates.responsableId);
    if (updates.nombre !== undefined) payload.name = updates.nombre;
    if (updates.especie !== undefined) payload.species = updates.especie;
    if (updates.raza !== undefined) payload.breed = updates.raza || null;
    if (updates.sexo !== undefined) payload.sex = updates.sexo;
    if (updates.fechaNacimientoAprox !== undefined) payload.birth_date = updates.fechaNacimientoAprox || null;
    if (updates.pesoKg !== undefined) payload.weight_kg = updates.pesoKg || null;
    if (updates.microchip !== undefined) payload.microchip = updates.microchip || null;
    if (updates.alergias !== undefined) payload.notes = updates.alergias || null;
    if (updates.fotoUrl !== undefined) payload.photo_url = updates.fotoUrl || null;
    const response = await fetch(`/api/v1/mascotas/${id}`, {
      method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error(await errorApi(response));
    setMascotas(prev => prev.map(m => (m.id === id ? { ...m, ...updates } : m)));
    showToast({
      type: 'success',
      title: 'Ficha médica actualizada',
      description: 'Los cambios del paciente se guardaron correctamente.'
    });
  };

  const addTurno = async (data: Omit<Turno, 'id'>): Promise<{ success: boolean; error?: string }> => {
    try {
      const veterinarianId = await obtenerVeterinarioId(data.veterinario);
      const created = await api<any>('/api/v1/turnos', { method: 'POST', body: JSON.stringify({
        pet_id: Number(data.mascotaId), veterinarian_id: veterinarianId,
        scheduled_at: `${data.fecha}T${data.hora}:00`, duration_minutes: 30, reason: data.motivo,
      }) });
      const newTurno: Turno = { ...data, id: String(created.id), veterinario: data.veterinario };
    setTurnos(prev => [newTurno, ...prev]);
    showToast({
      type: 'success',
      title: 'Turno agendado',
      description: `Turno agendado para el ${data.fecha} a las ${data.hora}.`
    });
      return { success: true };
    } catch (error) {
      const err = error instanceof Error ? error.message : 'No se pudo guardar el turno.';
      showToast({ type: 'error', title: 'No se pudo agendar el turno', description: err });
      return { success: false, error: err };
    }
  };

  const updateTurnoEstado = async (id: string, nuevoEstado: EstadoTurno) => {
    try {
      await api(`/api/v1/turnos/${id}/estado`, { method: 'PATCH', body: JSON.stringify({ status: nuevoEstado.toLowerCase(), reason: null }) });
    } catch (error) {
      showToast({ type: 'error', title: 'No se pudo actualizar el turno', description: error instanceof Error ? error.message : 'Error de conexión con la API.' });
      return;
    }
    setTurnos(prev => prev.map(t => t.id === id ? { ...t, estado: nuevoEstado } : t));
    showToast({
      type: 'info',
      title: 'Estado de turno actualizado',
      description: `El turno pasó a estado ${nuevoEstado}.`
    });
  };

  const addConsulta = async (data: Omit<ConsultaMedica, 'id'>): Promise<ConsultaMedica> => {
    const veterinarianId = await obtenerVeterinarioId(data.veterinario);
    const created = await api<any>('/api/v1/consultas', { method: 'POST', body: JSON.stringify({
      pet_id: Number(data.mascotaId), veterinarian_id: veterinarianId,
      appointment_id: data.turnoId ? Number(data.turnoId) : null,
      attended_at: `${data.fecha}T${data.hora}:00`, reason: data.motivo,
      observations: data.evaluacionClinica, diagnosis: data.diagnosticoPresuntivo, treatment: data.tratamiento,
    }) });
    const newConsulta: ConsultaMedica = { ...data, id: String(created.id), turnoId: created.appointment_id ? String(created.appointment_id) : undefined };
    setConsultas(prev => [newConsulta, ...prev]);

    // If it was linked to a turno, mark the turno as Atendido
    if (created.appointment_id) {
      setTurnos(prev => prev.map(t => t.id === String(created.appointment_id) ? { ...t, estado: 'Atendido' } : t));
    }

    showToast({
      type: 'success',
      title: 'Consulta médica guardada',
      description: `Se registró la atención para ${mascotas.find(m => m.id === data.mascotaId)?.nombre || 'el paciente'}.`
    });
    return newConsulta;
  };

  const createOrden = async (data: Omit<OrdenAnalisis, 'id'>): Promise<OrdenAnalisis> => {
    let consultaId = Number(data.consultaId);
    if (!Number.isInteger(consultaId)) {
      const latest = consultas.find((c) => c.mascotaId === data.mascotaId);
      if (latest) consultaId = Number(latest.id);
      else {
        const petId = Number(data.mascotaId);
        const vetId = await obtenerVeterinarioId(data.veterinarioSolicitante);
        const consulta = await api<any>('/api/v1/consultas', { method: 'POST', body: JSON.stringify({ pet_id: petId, veterinarian_id: vetId, reason: 'Solicitud de análisis clínicos' }) });
        consultaId = consulta.id;
        const consultaLocal: ConsultaMedica = { id: String(consulta.id), mascotaId: data.mascotaId, veterinario: data.veterinarioSolicitante, fecha: new Date().toISOString().slice(0, 10), hora: new Date().toTimeString().slice(0, 5), motivo: 'Solicitud de análisis clínicos', evaluacionClinica: '', diagnosticoPresuntivo: '', tratamiento: '', requiereAnalisis: true };
        setConsultas((prev) => [consultaLocal, ...prev]);
      }
    }
    const vetId = await obtenerVeterinarioId(data.veterinarioSolicitante);
    const detalles = await Promise.all(data.detalles.map(async (d) => ({ tipo_analisis_id: await obtenerTipoAnalisisId(d.tipoAnalisis), indicaciones: d.indicaciones })));
    const saved = await api<any>('/api/v1/ordenes-analisis', { method: 'POST', body: JSON.stringify({ consulta_id: consultaId, veterinario_id: vetId, observaciones: data.prioridad === 'Urgente' ? 'Prioridad urgente' : null, detalles }) });
    const newOrden = mapOrden(saved);
    setOrdenes(prev => [newOrden, ...prev]);
    showToast({
      type: 'success',
      title: 'Orden de derivación creada',
      description: `Se formalizó la orden ${newOrden.id} con ${data.detalles.length} análisis.`
    });
    return newOrden;
  };

  const registrarMuestra = async (
    data: Omit<MuestraBiologica, 'id' | 'historialTrazabilidad' | 'estadoActual'>
  ): Promise<MuestraBiologica> => {
    const tipoMuestraId = await obtenerTipoMuestraId(data.tipoMaterial);
    const saved = await api<any>('/api/v1/muestras', { method: 'POST', body: JSON.stringify({
      codigo_etiqueta: data.identificacionFisica, orden_id: Number(data.ordenId), tipo_muestra_id: tipoMuestraId,
      responsable_extraccion: data.responsableExtraccion, condiciones_conservacion: data.condicionConservacion,
      observaciones_calidad: data.observaciones, fecha_extraccion: new Date().toISOString(),
    }) });
    const newMuestra = mapMuestra(saved);

    setMuestras(prev => [newMuestra, ...prev]);
    
    // Update orden state if needed
    setOrdenes(prev => prev.map(o => o.id === data.ordenId && o.estado === 'Solicitada' ? { ...o, estado: 'En preparación' } : o));

    showToast({
      type: 'success',
      title: 'Muestra biológica registrada',
      description: `Identificador ${newMuestra.id} (${data.identificacionFisica}) registrado con trazabilidad de origen.`
    });
    return newMuestra;
  };

  const vincularMuestraConAnalisis = async (ordenId: string, detalleId: string, muestraId: string) => {
    await api(`/api/v1/ordenes-analisis/${ordenId}/asociar-muestra`, { method: 'POST', body: JSON.stringify({ muestra_id: Number(muestraId), detalle_ids: [Number(detalleId)] }) });
    const currentSample = muestras.find((m) => m.id === muestraId);
    if (currentSample?.estadoActual === 'Extraída') {
      await api(`/api/v1/muestras/${muestraId}/estado`, { method: 'PATCH', body: JSON.stringify({ nuevo_estado: 'lista_para_envio', responsable: currentSample.responsableExtraccion, motivo: 'Muestra vinculada y lista para despacho' }) });
    }
    setOrdenes(prev => prev.map(ord => {
      if (ord.id !== ordenId) return ord;
      return {
        ...ord,
        detalles: ord.detalles.map(det => {
          if (det.id !== detalleId) return det;
          return {
            ...det,
            muestraAsociadaId: muestraId,
            estado: 'Muestra vinculada'
          };
        })
      };
    }));

    showToast({
      type: 'info',
      title: 'Muestra vinculada al análisis',
      description: `La muestra ${muestraId} fue asociada al análisis solicitado.`
    });
  };

  const prepararEnvio = async (params: {
    conservadoraId: string;
    precintoCodigo: string;
    responsableDespacho: string;
    transportista: string;
    muestrasIds: string[];
    temperaturaDespachoC: number;
    observaciones?: string;
  }): Promise<RemitoBiologico> => {
    const envio = await api<any>('/api/v1/envios', { method: 'POST', body: JSON.stringify({
      origen: 'Clínica Veterinaria Patitas & Co. - Sede Central', destino: 'Laboratorio Central de Derivación BioVet',
      condiciones_empaquetado: params.observaciones || 'Muestras protegidas y refrigeradas', responsable_preparacion: params.responsableDespacho,
      conservadoras: [{ conservadora_id: Number(params.conservadoraId), muestra_ids: params.muestrasIds.map(Number) }], observaciones: params.observaciones,
    }) });
    const conPrecinto = await api<any>(`/api/v1/envios/${envio.id}/precintos`, { method: 'POST', body: JSON.stringify({ codigo: params.precintoCodigo, conservadora_id: Number(params.conservadoraId), colocado_por: params.responsableDespacho }) });
    const despachado = await api<any>(`/api/v1/envios/${envio.id}/despachar`, { method: 'POST', body: JSON.stringify({ responsable_despacho: params.responsableDespacho, transportista: params.transportista }) });
    await api(`/api/v1/envios/${envio.id}/temperaturas`, { method: 'POST', body: JSON.stringify({ conservadora_id: Number(params.conservadoraId), temperatura_requerida_c: 4, temperatura_medida_c: params.temperaturaDespachoC, fecha_medicion: new Date().toISOString(), responsable: params.responsableDespacho, observaciones: params.observaciones }) });
    const nuevoRemito = mapEnvio({ ...despachado, precintos: conPrecinto.precintos }, false, []);
    nuevoRemito.estado = 'Despachado';
    const now = new Date().toISOString().replace('T', ' ').substring(0, 16);
    setPrecintos(prev => [{ id: String(despachado.precintos?.[0]?.id || ''), codigoUnico: params.precintoCodigo, conservadoraId: params.conservadoraId, colocadoPor: params.responsableDespacho, fechaHoraColocacion: now }, ...prev]);
    setRemitos(prev => [nuevoRemito, ...prev]);
    setConservadoras(prev => prev.map(c => c.id === params.conservadoraId ? { ...c, disponible: false } : c));
    setMuestras(prev => prev.map(m => params.muestrasIds.includes(m.id) ? { ...m, estadoActual: 'En tránsito', conservadoraId: params.conservadoraId, remitoId: String(envio.id) } : m));
    setOrdenes(prev => prev.map(o => params.muestrasIds.some(id => o.detalles.some(d => d.muestraAsociadaId === id)) ? { ...o, estado: 'Enviada' } : o));

    showToast({
      type: 'success',
      title: 'Envío despachado con éxito',
      description: `Remito ${nuevoRemito.numeroRemito || nuevoRemito.id} generado con ${params.muestrasIds.length} muestras. Precinto ${params.precintoCodigo}.`
    });

    return nuevoRemito;
  };

  const verificarPrecintoYRecepcion = async (params: {
    remitoId: string;
    estadoPrecinto: EstadoPrecinto;
    verificadoPor: string;
    observaciones?: string;
  }): Promise<void> => {
    const now = new Date().toISOString().replace('T', ' ').substring(0, 16);
    const targetRemito = remitos.find(r => r.id === params.remitoId || r.envioId === params.remitoId);
    if (!targetRemito) throw new Error('No se encontró el envío seleccionado.');

    const esPrecintoValido = params.estadoPrecinto === 'Integro';

    const codigoEstado: Record<EstadoPrecinto, string> = { Integro: 'integro', Roto: 'roto', Ausente: 'ausente', CodigoNoCoincide: 'codigo_no_coincide' };
    const estadoRecepcion = params.estadoPrecinto === 'CodigoNoCoincide' ? 'otra_anomalia' : codigoEstado[params.estadoPrecinto];
    await api('/api/v1/verificaciones-precinto', { method: 'POST', body: JSON.stringify({
      envio_id: targetRemito.envioId || targetRemito.id, precinto_id: precintos.find((p) => p.codigoUnico === targetRemito.precintoCodigo)?.id || null,
      codigo_esperado: targetRemito.precintoCodigo, codigo_observado: params.estadoPrecinto === 'Ausente' ? null : params.estadoPrecinto === 'CodigoNoCoincide' ? 'NO COINCIDE' : targetRemito.precintoCodigo,
      estado: estadoRecepcion, responsable_id: params.verificadoPor, fecha_verificacion: new Date().toISOString(),
      observaciones: params.observaciones,
    }) });
    await api('/api/v1/recepciones', { method: 'POST', body: JSON.stringify({
      envio_id: targetRemito.envioId || targetRemito.id, fecha_recepcion: new Date().toISOString(), responsable_id: params.verificadoPor,
      muestras_despachadas: targetRemito.muestrasIds, muestras_recibidas: targetRemito.muestrasIds, observaciones: params.observaciones,
    }) });
    setPrecintos(prev => prev.map(p => p.codigoUnico === targetRemito.precintoCodigo ? { ...p, estadoVerificacion: params.estadoPrecinto, verificadoPor: params.verificadoPor, fechaHoraVerificacion: now, observaciones: params.observaciones } : p));
    setConservadoras(prev => prev.map(c => c.id === targetRemito.conservadoraId ? { ...c, disponible: true } : c));

    if (esPrecintoValido) {
      // SUCCESSFUL RECEIPT
      setRemitos(prev => prev.map(r => r.id === params.remitoId ? { ...r, estado: 'Recibido' } : r));

      setMuestras(prev => prev.map(m => {
        if (!targetRemito.muestrasIds.includes(m.id)) return m;
        return {
          ...m,
          estadoActual: 'Recibida',
          historialTrazabilidad: [
            ...m.historialTrazabilidad,
            {
              id: `TRAZ-${Date.now()}`,
              fechaHora: now,
              estadoAnterior: m.estadoActual,
              estadoNuevo: 'Recibida',
              responsable: params.verificadoPor,
              ubicacion: 'Laboratorio Central BioVet - Recepción y Triaje',
              observaciones: `Precinto ${targetRemito.precintoCodigo} ÍNTEGRO. Remito verificado. ${params.observaciones || ''}`
            }
          ]
        };
      }));

      showToast({
        type: 'success',
        title: 'Recepción validada con precinto íntegro',
        description: `Se confirmó la llegada de las muestras al laboratorio en condiciones óptimas.`
      });
    } else {
      // REJECTED - CRITICAL BUSINESS RULE!
      // "Impedir el procesamiento de muestras si el precinto sanitario llega roto (cambio de estado a Muestra Rechazada)"
      setRemitos(prev => prev.map(r => r.id === params.remitoId ? { ...r, estado: 'Con incidencias' } : r));

      const motivoFalla = params.estadoPrecinto === 'Roto' 
        ? 'Precinto sanitario roto / vulnerado en transporte. Pérdida de cadena de custodia biológica.'
        : params.estadoPrecinto === 'CodigoNoCoincide'
        ? 'Código de precinto no coincide con el remito biológico despachado.'
        : 'Precinto sanitario ausente.';

      // Register Incident
      const incidents = await api<any[]>('/api/v1/incidencias?abiertas=true');
      setIncidencias(incidents.map((i): Incidencia => ({ id: String(i.id), fechaHora: fechaLocal(i.fecha), remitoId: String(i.envio_id), tipo: 'Precinto Roto', descripcion: i.descripcion, responsableReporte: i.responsable_id, resuelto: Boolean(i.resuelta_en) })).concat(incidencias));

      // Mutate samples to RECHAZADA
      setMuestras(prev => prev.map(m => {
        if (!targetRemito.muestrasIds.includes(m.id)) return m;
        return {
          ...m,
          estadoActual: 'Rechazada',
          motivoRechazo: motivoFalla,
          historialTrazabilidad: [
            ...m.historialTrazabilidad,
            {
              id: `TRAZ-${Date.now()}`,
              fechaHora: now,
              estadoAnterior: m.estadoActual,
              estadoNuevo: 'Rechazada',
              responsable: params.verificadoPor,
              ubicacion: 'Laboratorio Central BioVet - Control de Ingreso',
              observaciones: `RECHAZO BIOLÓGICO: ${motivoFalla}`
            }
          ]
        };
      }));

      showToast({
        type: 'error',
        title: '¡Muestras rechazadas por precinto!',
        description: `Regla de seguridad: ${motivoFalla} Se bloqueó el procesamiento y se registró la incidencia.`
      });
    }
  };

  const registrarResultado = async (data: Omit<ResultadoAnalisis, 'id'>): Promise<ResultadoAnalisis> => {
    const order = ordenes.find((o) => o.id === data.ordenId);
    const pet = mascotas.find((m) => m.id === order?.mascotaId);
    if (!order || !pet) throw new Error('No se encontró la orden o el paciente vinculado.');
    const saved = await api<any>('/api/v1/resultados', { method: 'POST', body: JSON.stringify({
      orden_id: data.ordenId, detalle_orden_id: data.detalleAnalisisId, paciente_id: pet.id, muestra_id: data.muestraId || null,
      fecha_recepcion: new Date(data.fechaRecepcionResultado).toISOString(), procedencia: data.laboratorioNombre,
      datos: { valores: data.valores, conclusionDiagnostica: data.conclusionDiagnostica }, informe_nombre: data.nombreArchivoAdjunto || null,
      registrado_por: data.validadoPor || data.laboratorioNombre,
    }) });
    const status = data.estado === 'Validado por Veterinario' ? 'validado' : data.estado === 'En revisión' ? 'en_revision' : 'recibido';
    if (status !== 'recibido') await api(`/api/v1/resultados/${saved.id}/estado`, { method: 'PATCH', body: JSON.stringify({ estado: status }) });
    const newResultado: ResultadoAnalisis = { ...data, id: String(saved.id) };
    setResultados(prev => [newResultado, ...prev]);

    // Update Muestra to Analizada
    setMuestras(prev => prev.map(m => {
      if (m.id !== data.muestraId) return m;
      return {
        ...m,
        estadoActual: 'Analizada',
        historialTrazabilidad: [
          ...m.historialTrazabilidad,
          {
            id: `TRAZ-${Date.now()}`,
            fechaHora: data.fechaRecepcionResultado,
            estadoAnterior: m.estadoActual,
            estadoNuevo: 'Analizada',
            responsable: data.laboratorioNombre,
            ubicacion: 'Laboratorio Central BioVet - Análisis Finalizado',
            observaciones: `Resultado emitido y validado (${newResultado.conclusionDiagnostica}).`
          }
        ]
      };
    }));

    // Update DetalleAnalisis to Resultado listo
    setOrdenes(prev => prev.map(ord => {
      if (ord.id !== data.ordenId) return ord;
      const updatedDetalles = ord.detalles.map(d => {
        if (d.id === data.detalleAnalisisId) {
          return { ...d, estado: 'Resultado listo' as const };
        }
        return d;
      });
      // Check if all are done
      const allDone = updatedDetalles.every(d => d.estado === 'Resultado listo');
      return {
        ...ord,
        detalles: updatedDetalles,
        estado: allDone ? ('Con resultados' as const) : ord.estado
      };
    }));

    showToast({
      type: 'success',
      title: 'Resultado de análisis cargado',
      description: `Se incorporó el informe del laboratorio a la historia clínica del paciente.`
    });

    return newResultado;
  };

  const recibirResultadosLaboratorio = async (muestraId: string, escenario: string): Promise<void> => {
    const respuesta = await api<any>(`/api/v1/muestras/${encodeURIComponent(muestraId)}/resultados-laboratorio?escenario=${encodeURIComponent(escenario)}`, { method: 'POST' });
    if (respuesta.estado !== 'registrado') {
      showToast({ type: 'warning', title: respuesta.estado === 'pendiente' ? 'Resultados pendientes' : 'Sin resultados', description: respuesta.mensaje || 'El laboratorio todavía no entregó resultados.' });
      return;
    }
    const registrados: ResultadoAnalisis[] = respuesta.resultados.map((r: any) => ({
      id: String(r.id), ordenId: String(r.orden_id), detalleAnalisisId: String(r.detalle_orden_id),
      muestraId: String(r.muestra_id), fechaRecepcionResultado: fechaLocal(r.fecha_recepcion),
      laboratorioNombre: r.procedencia, valores: r.datos?.valores || [],
      conclusionDiagnostica: r.datos?.conclusionDiagnostica || '', nombreArchivoAdjunto: r.informe_nombre || undefined,
      estado: 'Recibido', validadoPor: r.registrado_por,
    }));
    setResultados(prev => [...registrados, ...prev]);
    setMuestras(prev => prev.map(m => m.id === muestraId ? { ...m, estadoActual: 'Analizada' } : m));
    const detalleIds = new Set(registrados.map(r => r.detalleAnalisisId));
    setOrdenes(prev => prev.map(o => {
      const detalles = o.detalles.map(d => detalleIds.has(d.id) ? { ...d, estado: 'Resultado listo' as const } : d);
      return { ...o, detalles, estado: detalles.every(d => d.estado === 'Resultado listo') ? 'Con resultados' : o.estado };
    }));
    showToast({ type: 'success', title: 'Resultados recibidos', description: `Se registraron ${registrados.length} resultado(s) del laboratorio para la muestra ${muestraId}.` });
  };

  const resolverIncidencia = async (id: string, resolucion: string) => {
    await api(`/api/v1/incidencias/${id}/resolver`, { method: 'POST', body: JSON.stringify({ resolucion, responsable_resolucion_id: 'Laboratorio' }) });
    setIncidencias(prev => prev.map(inc => inc.id === id ? { ...inc, resuelto: true, resolucion } : inc));
    showToast({
      type: 'info',
      title: 'Incidencia resuelta',
      description: 'Se registró la resolución y acciones correctivas tomadas.'
    });
  };

  const reloadFromDatabase = () => {
    showToast({
      type: 'info',
      title: 'Actualizando desde SQLite',
      description: 'Se volverán a cargar los datos persistidos en la base.'
    });
    window.location.reload();
  };

  return (
    <VeterinariaContext.Provider
      value={{
        responsables,
        mascotas,
        turnos,
        consultas,
        ordenes,
        muestras,
        conservadoras,
        precintos,
        remitos,
        incidencias,
        resultados,
        activeModule,
        setActiveModule,
        activeReportTab,
        setActiveReportTab,
        isSidebarCollapsed,
        setIsSidebarCollapsed,
        isMobileMenuOpen,
        setIsMobileMenuOpen,
        selectedMascotaId,
        setSelectedMascotaId,
        toast,
        showToast,
        clearToast,
        addResponsable,
        addMascota,
        updateMascota,
        addTurno,
        updateTurnoEstado,
        addConsulta,
        createOrden,
        registrarMuestra,
        vincularMuestraConAnalisis,
        prepararEnvio,
        verificarPrecintoYRecepcion,
        registrarResultado,
        recibirResultadosLaboratorio,
        resolverIncidencia,
        reloadFromDatabase
      }}
    >
      {children}
    </VeterinariaContext.Provider>
  );
};

export const useVeterinaria = () => {
  const context = useContext(VeterinariaContext);
  if (!context) {
    throw new Error('useVeterinaria debe utilizarse dentro de un VeterinariaProvider');
  }
  return context;
};

// Aliases para compatibilidad
export const VeterinaryProvider = VeterinariaProvider;
export const useVeterinary = useVeterinaria;
