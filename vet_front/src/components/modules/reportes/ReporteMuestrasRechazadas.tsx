import React, { useState, useEffect, useMemo } from 'react';
import { 
  Truck, 
  FlaskConical, 
  CheckCircle2, 
  AlertTriangle, 
  Mail, 
  FileSpreadsheet, 
  FileText, 
  RefreshCw, 
  Filter, 
  Search, 
  ShieldAlert, 
  X,
  Send,
  Loader2,
  Thermometer,
  Lock,
  Unlock
} from 'lucide-react';
import { useVeterinaria } from '../../../context/VeterinariaContext';
import { ReporteRechazadasResponse } from './types';

export const ReporteMuestrasRechazadas: React.FC = () => {
  const { showToast } = useVeterinaria();

  const [reporte2Data, setReporte2Data] = useState<ReporteRechazadasResponse | null>(null);
  const [cargando2, setCargando2] = useState(false);

  // Filtros
  const [fechaDesde2, setFechaDesde2] = useState('');
  const [fechaHasta2, setFechaHasta2] = useState('');
  const [filtroCausa2, setFiltroCausa2] = useState('Todas');
  const [filtroTransportista2, setFiltroTransportista2] = useState('Todos');
  const [filtroEstado2, setFiltroEstado2] = useState('Todos');
  const [busquedaTabla2, setBusquedaTabla2] = useState('');

  // Modal Enviar por Correo
  const [modalEmail2Open, setModalEmail2Open] = useState(false);
  const [emailDestinatario2, setEmailDestinatario2] = useState('');
  const [asuntoEmail2, setAsuntoEmail2] = useState('');
  const [adjuntarPdf2, setAdjuntarPdf2] = useState(true);
  const [adjuntarExcel2, setAdjuntarExcel2] = useState(true);
  const [enviandoEmail2, setEnviandoEmail2] = useState(false);

  const cargarReporte2 = async () => {
    setCargando2(true);
    try {
      const params = new URLSearchParams();
      if (fechaDesde2) params.append('fecha_desde', fechaDesde2);
      if (fechaHasta2) params.append('fecha_hasta', fechaHasta2);
      if (filtroCausa2 !== 'Todas') {
        params.append('causa', filtroCausa2);
        params.append('causa_rechazo', filtroCausa2);
      }
      if (filtroTransportista2 !== 'Todos') {
        params.append('transportista', filtroTransportista2);
      }
      if (filtroEstado2 !== 'Todos') {
        params.append('estado_muestra', filtroEstado2);
        params.append('estado', filtroEstado2);
      }

      const res = await fetch(`/api/v1/reportes/muestras-rechazadas?${params.toString()}`);
      if (!res.ok) throw new Error('No se pudo obtener el reporte de bioseguridad');
      const data: ReporteRechazadasResponse = await res.json();
      setReporte2Data(data);
    } catch (err) {
      showToast({
        type: 'error',
        title: 'Error al cargar reporte de bioseguridad',
        description: err instanceof Error ? err.message : 'Error de comunicación con el backend.'
      });
    } finally {
      setCargando2(false);
    }
  };

  useEffect(() => {
    void cargarReporte2();
  }, [fechaDesde2, fechaHasta2, filtroCausa2, filtroTransportista2, filtroEstado2]);

  const descargarArchivo2 = async (formato: 'excel' | 'pdf') => {
    try {
      const params = new URLSearchParams();
      if (fechaDesde2) params.append('fecha_desde', fechaDesde2);
      if (fechaHasta2) params.append('fecha_hasta', fechaHasta2);
      if (filtroCausa2 !== 'Todas') {
        params.append('causa', filtroCausa2);
        params.append('causa_rechazo', filtroCausa2);
      }
      if (filtroTransportista2 !== 'Todos') {
        params.append('transportista', filtroTransportista2);
      }
      if (filtroEstado2 !== 'Todos') {
        params.append('estado_muestra', filtroEstado2);
        params.append('estado', filtroEstado2);
      }

      const endpoint = `/api/v1/reportes/muestras-rechazadas/${formato}?${params.toString()}`;
      const res = await fetch(endpoint);
      if (!res.ok) throw new Error(`Error al generar ${formato.toUpperCase()}`);

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = formato === 'excel' ? 'reporte_muestras_rechazadas.xlsx' : 'reporte_muestras_rechazadas.pdf';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      showToast({
        type: 'success',
        title: `Descarga completada`,
        description: `Se descargó el archivo ${formato.toUpperCase()} de bioseguridad exitosamente.`
      });
    } catch (err) {
      showToast({
        type: 'error',
        title: `Fallo en la descarga`,
        description: err instanceof Error ? err.message : 'No se pudo descargar el archivo.'
      });
    }
  };

  const handleEnviarEmail2 = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!emailDestinatario2) return;

    setEnviandoEmail2(true);
    try {
      const payload = {
        destinatario: emailDestinatario2,
        asunto: asuntoEmail2 || undefined,
        incluir_pdf: adjuntarPdf2,
        incluir_excel: adjuntarExcel2,
        fecha_desde: fechaDesde2 || undefined,
        fecha_hasta: fechaHasta2 || undefined,
        causa: filtroCausa2 !== 'Todas' ? filtroCausa2 : undefined,
        causa_rechazo: filtroCausa2 !== 'Todas' ? filtroCausa2 : undefined,
        transportista: filtroTransportista2 !== 'Todos' ? filtroTransportista2 : undefined,
        estado_muestra: filtroEstado2 !== 'Todos' ? filtroEstado2 : undefined,
        estado: filtroEstado2 !== 'Todos' ? filtroEstado2 : undefined
      };

      const res = await fetch('/api/v1/reportes/muestras-rechazadas/enviar-email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Error al enviar correo');

      showToast({
        type: 'success',
        title: 'Correo de Bioseguridad enviado',
        description: `El informe oficial fue enviado con éxito a ${emailDestinatario2}.`
      });
      setModalEmail2Open(false);
    } catch (err) {
      showToast({
        type: 'error',
        title: 'Error de envío SMTP',
        description: err instanceof Error ? err.message : 'No se pudo enviar el correo.'
      });
    } finally {
      setEnviandoEmail2(false);
    }
  };

  const muestrasRechazadasFiltradas = useMemo(() => {
    if (!reporte2Data) return [];
    if (!busquedaTabla2.trim()) return reporte2Data.detalles_auditoria;
    const q = busquedaTabla2.toLowerCase();
    return reporte2Data.detalles_auditoria.filter(d => 
      d.muestra_codigo.toLowerCase().includes(q) ||
      d.paciente_nombre.toLowerCase().includes(q) ||
      d.tutor_nombre.toLowerCase().includes(q) ||
      d.tipo_analisis.toLowerCase().includes(q) ||
      d.remito_numero.toLowerCase().includes(q) ||
      d.transportista.toLowerCase().includes(q) ||
      d.precinto_esperado.toLowerCase().includes(q) ||
      d.precinto_observado.toLowerCase().includes(q) ||
      (d.causa_rechazo && d.causa_rechazo.toLowerCase().includes(q))
    );
  }, [reporte2Data, busquedaTabla2]);

  return (
    <div className="space-y-6">
      <div className="bg-white border border-[#E7E2DA] rounded-xl p-4 shadow-xs flex items-center justify-between">
        <div className="flex items-center gap-3.5">
          <img
            src="/assets/aistudio/Gemini_Generated_Image_o95dgio95dgio95d-removebg-preview_cbe90b76.png"
            alt="Logo Patitas & Co."
            className="w-11 h-11 object-contain"
          />
          <div>
            <h3 className="font-bold text-sm text-[#2D5864] leading-tight">
              PATITAS & CO. — AUDITORÍA DE BIOSEGURIDAD Y CONTROL DE TRANSPORTE
            </h3>
            <p className="text-xs text-neutral-500 mt-0.5">
              Reporte 2: Muestras Biológicas Rechazadas por Fallas en Transporte y Bioseguridad
            </p>
          </div>
        </div>
        <div className="text-right hidden sm:block">
          <span className="text-[10px] font-mono text-neutral-400 block">Sede Central Córdoba</span>
          <span className="text-[10px] text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full font-semibold border border-emerald-200">
            Norma ISO 15189 / Res. SENASA 412/2026
          </span>
        </div>
      </div>

      <div className="bg-white border border-[#E7E2DA] rounded-xl p-4 shadow-xs space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-[#2D5864]" />
            <span className="text-xs font-bold text-neutral-900 uppercase tracking-wider">Filtros de Bioseguridad:</span>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => void descargarArchivo2('excel')}
              className="px-3 py-1.5 text-xs font-semibold text-emerald-800 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 rounded-lg transition-colors flex items-center gap-1.5 shadow-2xs"
              title="Descargar libro Excel con tablas y formato"
            >
              <FileSpreadsheet className="w-3.5 h-3.5" />
              <span>Descargar Excel</span>
            </button>

            <button
              onClick={() => void descargarArchivo2('pdf')}
              className="px-3 py-1.5 text-xs font-semibold text-rose-800 bg-rose-50 hover:bg-rose-100 border border-rose-200 rounded-lg transition-colors flex items-center gap-1.5 shadow-2xs"
              title="Descargar informe oficial en PDF"
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Descargar PDF</span>
            </button>

            <button
              onClick={() => setModalEmail2Open(true)}
              className="px-3 py-1.5 text-xs font-semibold text-white bg-[#2D5864] hover:bg-[#23454f] rounded-lg transition-colors flex items-center gap-1.5 shadow-xs"
            >
              <Mail className="w-3.5 h-3.5" />
              <span>Enviar por Correo</span>
            </button>

            <button
              onClick={() => void cargarReporte2()}
              disabled={cargando2}
              className="p-1.5 text-neutral-500 hover:text-[#2D5864] hover:bg-neutral-100 rounded-lg transition-colors"
              title="Actualizar datos"
            >
              <RefreshCw className={`w-4 h-4 ${cargando2 ? 'animate-spin text-[#2D5864]' : ''}`} />
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 pt-2 border-t border-neutral-100 text-xs">
          <div>
            <label className="block text-neutral-500 font-medium mb-1">Causa de Rechazo</label>
            <select
              value={filtroCausa2}
              onChange={e => setFiltroCausa2(e.target.value)}
              className="w-full p-2 bg-[#FAF8F5] border border-[#E7E2DA] rounded-lg text-neutral-800 font-medium"
            >
              <option value="Todas">Todas las causas</option>
              {reporte2Data?.filtros_disponibles.causas
                .filter(c => c !== 'Todas')
                .map(c => (
                  <option key={c} value={c}>{c}</option>
                ))}
            </select>
          </div>

          <div>
            <label className="block text-neutral-500 font-medium mb-1">Transportista</label>
            <select
              value={filtroTransportista2}
              onChange={e => setFiltroTransportista2(e.target.value)}
              className="w-full p-2 bg-[#FAF8F5] border border-[#E7E2DA] rounded-lg text-neutral-800 font-medium"
            >
              <option value="Todos">Todos los transportistas</option>
              {reporte2Data?.filtros_disponibles.transportistas
                .filter(tr => tr !== 'Todos')
                .map(tr => (
                  <option key={tr} value={tr}>{tr}</option>
                ))}
            </select>
          </div>

          <div>
            <label className="block text-neutral-500 font-medium mb-1">Estado de Muestra</label>
            <select
              value={filtroEstado2}
              onChange={e => setFiltroEstado2(e.target.value)}
              className="w-full p-2 bg-[#FAF8F5] border border-[#E7E2DA] rounded-lg text-neutral-800 font-medium"
            >
              <option value="Todos">Todas las muestras</option>
              <option value="Rechazada">Solo Rechazadas</option>
              <option value="Aceptada">Solo Aceptadas</option>
            </select>
          </div>

          <div>
            <label className="block text-neutral-500 font-medium mb-1">Desde</label>
            <input
              type="date"
              value={fechaDesde2}
              onChange={e => setFechaDesde2(e.target.value)}
              className="w-full p-2 bg-[#FAF8F5] border border-[#E7E2DA] rounded-lg text-neutral-800 font-medium"
            />
          </div>

          <div>
            <label className="block text-neutral-500 font-medium mb-1">Hasta</label>
            <input
              type="date"
              value={fechaHasta2}
              onChange={e => setFechaHasta2(e.target.value)}
              className="w-full p-2 bg-[#FAF8F5] border border-[#E7E2DA] rounded-lg text-neutral-800 font-medium"
            />
          </div>
        </div>
      </div>

      {reporte2Data && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          <div className="bg-white border border-[#E7E2DA] rounded-xl p-3.5 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold text-neutral-500 uppercase tracking-wide">Auditadas</span>
              <FlaskConical className="w-4 h-4 text-[#2D5864]" />
            </div>
            <div className="mt-2 flex items-baseline gap-1.5">
              <span className="text-2xl font-bold text-[#2D5864]">
                {reporte2Data.kpis.total_muestras_auditadas}
              </span>
              <span className="text-[10px] text-neutral-400">muestras</span>
            </div>
            <p className="text-[10px] text-neutral-500 mt-1">100% trazabilidad</p>
          </div>

          <div className="bg-white border border-[#E7E2DA] rounded-xl p-3.5 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold text-neutral-500 uppercase tracking-wide">Conformes</span>
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            </div>
            <div className="mt-2 flex items-baseline gap-1.5">
              <span className="text-2xl font-bold text-emerald-700">
                {reporte2Data.kpis.muestras_aceptadas}
              </span>
              <span className="text-[10px] text-emerald-600 font-medium">
                ({reporte2Data.kpis.tasa_conformidad_porcentaje}%)
              </span>
            </div>
            <p className="text-[10px] text-neutral-500 mt-1">Aprobadas para análisis</p>
          </div>

          <div className="bg-white border border-[#E7E2DA] rounded-xl p-3.5 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold text-neutral-500 uppercase tracking-wide">Rechazadas</span>
              <ShieldAlert className="w-4 h-4 text-rose-600" />
            </div>
            <div className="mt-2 flex items-baseline gap-1.5">
              <span className="text-2xl font-bold text-rose-700">
                {reporte2Data.kpis.muestras_rechazadas}
              </span>
              <span className="text-[10px] text-rose-600 font-medium">
                ({reporte2Data.kpis.tasa_rechazo_global_porcentaje}%)
              </span>
            </div>
            <p className="text-[10px] text-neutral-500 mt-1">Descarte por bioseguridad</p>
          </div>

          <div className="bg-white border border-[#E7E2DA] rounded-xl p-3.5 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold text-neutral-500 uppercase tracking-wide">Tasa Rechazo</span>
              <AlertTriangle className="w-4 h-4 text-amber-600" />
            </div>
            <div className="mt-2 flex items-baseline gap-1.5">
              <span className={`text-2xl font-bold ${
                reporte2Data.kpis.tasa_rechazo_global_porcentaje <= 5.0 ? 'text-amber-600' : 'text-rose-700'
              }`}>
                {reporte2Data.kpis.tasa_rechazo_global_porcentaje}%
              </span>
            </div>
            <p className="text-[10px] text-neutral-500 mt-1">Meta tolerancia: &lt; 5%</p>
          </div>

          <div className="bg-white border border-[#E7E2DA] rounded-xl p-3.5 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold text-neutral-500 uppercase tracking-wide">Precintos</span>
              <Lock className="w-4 h-4 text-sky-600" />
            </div>
            <div className="mt-2 flex items-baseline gap-1.5">
              <span className="text-2xl font-bold text-sky-800">
                {reporte2Data.kpis.integridad_precintos_porcentaje}%
              </span>
              <span className="text-[10px] text-neutral-400 font-medium">íntegros</span>
            </div>
            <p className="text-[10px] text-neutral-500 mt-1">{reporte2Data.kpis.precintos_violados_o_rotos} con alteración</p>
          </div>

          <div className="bg-white border border-[#E7E2DA] rounded-xl p-3.5 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold text-neutral-500 uppercase tracking-wide">Cadena de Frío</span>
              <Thermometer className="w-4 h-4 text-indigo-600" />
            </div>
            <div className="mt-2 flex items-baseline gap-1.5">
              <span className="text-2xl font-bold text-indigo-800">
                {reporte2Data.kpis.conformidad_cadena_frio_porcentaje}%
              </span>
              <span className="text-[10px] text-neutral-400 font-medium">en rango</span>
            </div>
            <p className="text-[10px] text-neutral-500 mt-1">{reporte2Data.kpis.excursiones_termicas} excursiones &gt; 8°C</p>
          </div>
        </div>
      )}

      {reporte2Data && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Gráfico 1: Causas Raíz */}
          <div className="bg-white border border-[#E7E2DA] rounded-xl p-5 shadow-xs space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-rose-600" />
                <h4 className="font-bold text-sm text-[#2D5864]">Distribución por Causa Raíz de Rechazo</h4>
              </div>
              <span className="text-[10px] text-neutral-400">Total: {reporte2Data.kpis.muestras_rechazadas} descartes</span>
            </div>

            <div className="space-y-3.5 pt-2">
              {reporte2Data.distribucion_causas_rechazo.length === 0 ? (
                <p className="text-xs text-neutral-400 italic text-center py-6">
                  No se registraron rechazos para el período o filtros seleccionados.
                </p>
              ) : (
                reporte2Data.distribucion_causas_rechazo.map(item => (
                  <div key={item.causa} className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-neutral-800 flex items-center gap-1.5">
                        {item.causa}
                        <span className={`text-[9px] px-1.5 py-0.2 rounded-full font-bold ${
                          item.severidad === 'Crítica'
                            ? 'bg-rose-100 text-rose-800 border border-rose-200'
                            : 'bg-amber-100 text-amber-800 border border-amber-200'
                        }`}>
                          {item.severidad}
                        </span>
                      </span>
                      <span className="font-bold text-neutral-700">
                        {item.cantidad} ({item.porcentaje}%)
                      </span>
                    </div>
                    <div className="w-full bg-neutral-100 h-2.5 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${
                          item.severidad === 'Crítica' ? 'bg-rose-500' : 'bg-amber-500'
                        }`}
                        style={{ width: `${Math.min(item.porcentaje, 100)}%` }}
                      />
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Gráfico 2: Confiabilidad por Transportista */}
          <div className="bg-white border border-[#E7E2DA] rounded-xl p-5 shadow-xs space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Truck className="w-4 h-4 text-[#5F8E9C]" />
                <h4 className="font-bold text-sm text-[#2D5864]">Confiabilidad y Desempeño Logístico</h4>
              </div>
              <span className="text-[10px] text-neutral-400">Auditoría por chofer / flota</span>
            </div>

            <div className="space-y-3 pt-2">
              {reporte2Data.confiabilidad_transportistas.map(tr => (
                <div key={tr.transportista} className="p-3 bg-[#FAF8F5] border border-[#F2E8D8] rounded-lg space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-neutral-900">{tr.transportista}</span>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold border ${
                      tr.calificacion === 'Excelente'
                        ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                        : tr.calificacion === 'Aceptable'
                        ? 'bg-blue-50 text-blue-800 border-blue-200'
                        : 'bg-rose-50 text-rose-800 border-rose-200'
                    }`}>
                      {tr.calificacion} ({tr.tasa_conformidad_porcentaje}% conforme)
                    </span>
                  </div>
                  
                  <div className="w-full bg-neutral-200 h-2 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        tr.calificacion === 'Excelente'
                          ? 'bg-emerald-500'
                          : tr.calificacion === 'Aceptable'
                          ? 'bg-blue-500'
                          : 'bg-rose-500'
                      }`}
                      style={{ width: `${Math.min(tr.tasa_conformidad_porcentaje, 100)}%` }}
                    />
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-neutral-500 pt-0.5">
                    <span>{tr.muestras_conformes} conformes · {tr.muestras_rechazadas} rechazadas (Total: {tr.total_muestras})</span>
                    <span className="italic truncate max-w-[200px]" title={tr.falla_frecuente}>
                      Incidencia: {tr.falla_frecuente}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* TABLA DE AUDITORÍA Y TRAZABILIDAD SANITARIA */}
      <div className="bg-white border border-[#E7E2DA] rounded-xl shadow-xs overflow-hidden">
        <div className="p-4 border-b border-[#E7E2DA] flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#FAF8F5]">
          <div>
            <h4 className="font-bold text-sm text-[#2D5864]">Registro de Auditoría de Bioseguridad y Precintos</h4>
            <p className="text-[11px] text-neutral-500 mt-0.5">
              Trazabilidad de muestras biológicas, verificación de sellos de seguridad y termometría en conservadora
            </p>
          </div>

          <div className="relative w-full sm:w-72">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400" />
            <input
              type="text"
              placeholder="Buscar por código, paciente, remito..."
              value={busquedaTabla2}
              onChange={e => setBusquedaTabla2(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 bg-white border border-[#E7E2DA] rounded-lg text-xs focus:ring-1 focus:ring-[#2D5864] focus:outline-hidden"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-[#5F8E9C] text-white font-semibold">
                <th className="p-3">Muestra & Análisis</th>
                <th className="p-3">Paciente & Tutor</th>
                <th className="p-3">Transportista / Remito</th>
                <th className="p-3 text-center">Precinto (Esp. / Obs.)</th>
                <th className="p-3 text-center">Cadena de Frío</th>
                <th className="p-3 text-center">Estado Sanitario</th>
                <th className="p-3">Causa de Rechazo & Acción</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100">
              {muestrasRechazadasFiltradas.length === 0 ? (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-neutral-400 italic">
                    No se encontraron registros de auditoría con los filtros aplicados.
                  </td>
                </tr>
              ) : (
                muestrasRechazadasFiltradas.map(d => {
                  const esRechazada = d.estado_muestra === 'Rechazada';
                  return (
                    <tr
                      key={d.muestra_codigo}
                      className={`hover:bg-neutral-50/80 transition-colors ${
                        esRechazada ? 'bg-rose-50/20' : ''
                      }`}
                    >
                      <td className="p-3">
                        <span className="font-mono font-bold text-[#2D5864] block">
                          {d.muestra_codigo}
                        </span>
                        <span className="text-[11px] text-neutral-600 block">{d.tipo_analisis}</span>
                        <span className="text-[10px] text-neutral-400">{d.fecha_evento}</span>
                      </td>
                      <td className="p-3">
                        <span className="font-semibold text-neutral-900 block">{d.paciente_nombre}</span>
                        <span className="text-[11px] text-neutral-500 block">
                          {d.especie} · Tutor: {d.tutor_nombre}
                        </span>
                      </td>
                      <td className="p-3">
                        <span className="font-medium text-neutral-800 block">{d.transportista}</span>
                        <span className="text-[11px] font-mono text-neutral-500 block">
                          Remito: {d.remito_numero} ({d.conservadora_codigo})
                        </span>
                      </td>
                      <td className="p-3 text-center">
                        <div className="inline-flex flex-col items-center">
                          <span className={`inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                            d.estado_precinto === 'Integro'
                              ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                              : d.estado_precinto === 'Roto'
                              ? 'bg-rose-50 text-rose-800 border-rose-200'
                              : 'bg-amber-50 text-amber-800 border-amber-200'
                          }`}>
                            {d.estado_precinto === 'Integro' ? (
                              <Lock className="w-2.5 h-2.5" />
                            ) : (
                              <Unlock className="w-2.5 h-2.5" />
                            )}
                            {d.estado_precinto}
                          </span>
                          <span className="text-[10px] font-mono text-neutral-400 mt-0.5">
                            {d.precinto_esperado} / {d.precinto_observado}
                          </span>
                        </div>
                      </td>
                      <td className="p-3 text-center">
                        <div className="inline-flex flex-col items-center">
                          <span className={`inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded-full border ${
                            d.temperatura_conforme
                              ? 'bg-sky-50 text-sky-800 border-sky-200'
                              : 'bg-rose-50 text-rose-800 border-rose-200'
                          }`}>
                            <Thermometer className="w-3 h-3" />
                            {d.temperatura_llegada_c}°C
                          </span>
                          <span className="text-[10px] text-neutral-400 mt-0.5">
                            Salida: {d.temperatura_salida_c}°C (2-8°C)
                          </span>
                        </div>
                      </td>
                      <td className="p-3 text-center">
                        {esRechazada ? (
                          <span className="inline-flex items-center gap-1 text-[11px] font-bold text-rose-800 bg-rose-100 px-2.5 py-0.5 rounded-full border border-rose-300">
                            <ShieldAlert className="w-3 h-3 text-rose-600" />
                            Rechazada
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-800 bg-emerald-100 px-2.5 py-0.5 rounded-full border border-emerald-300">
                            <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                            Aceptada
                          </span>
                        )}
                      </td>
                      <td className="p-3">
                        {d.causa_rechazo ? (
                          <span className="font-semibold text-rose-700 block">
                            {d.causa_rechazo}
                          </span>
                        ) : (
                          <span className="text-emerald-700 font-medium block">
                            Conforme con protocolo
                          </span>
                        )}
                        <span className="text-[10px] text-neutral-500 mt-0.5 block italic">
                          {d.accion_correctiva}
                        </span>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* MODAL: ENVIAR REPORTE 2 POR EMAIL */}
      {modalEmail2Open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#2D5864]/40 backdrop-blur-xs">
          <div className="bg-white rounded-xl shadow-xl border border-[#E7E2DA] max-w-md w-full overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="px-5 py-4 border-b border-[#F2E8D8] flex items-center justify-between bg-[#FAF8F5]">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-[#2D5864]" />
                <h3 className="font-bold text-sm text-[#2D5864]">Enviar Reporte de Bioseguridad</h3>
              </div>
              <button
                onClick={() => setModalEmail2Open(false)}
                className="text-neutral-400 hover:text-neutral-700 p-1 rounded-md"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleEnviarEmail2} className="p-5 space-y-4 text-xs">
              <div>
                <label className="block text-neutral-700 font-semibold mb-1">
                  Correo Electrónico Destinatario *
                </label>
                <input
                  type="email"
                  required
                  placeholder="ejemplo@veterinaria.com"
                  value={emailDestinatario2}
                  onChange={e => setEmailDestinatario2(e.target.value)}
                  className="w-full p-2.5 border border-[#E7E2DA] rounded-lg text-neutral-900 focus:ring-1 focus:ring-[#2D5864] focus:outline-hidden"
                />
                <span className="text-[10px] text-neutral-400 mt-1 block">
                  Se enviará mediante el servidor SMTP oficial configurado en el sistema.
                </span>
              </div>

              <div>
                <label className="block text-neutral-700 font-semibold mb-1">
                  Asunto del Correo (Opcional)
                </label>
                <input
                  type="text"
                  placeholder="Auditoría de Muestras Rechazadas — Patitas & Co."
                  value={asuntoEmail2}
                  onChange={e => setAsuntoEmail2(e.target.value)}
                  className="w-full p-2.5 border border-[#E7E2DA] rounded-lg text-neutral-900 focus:ring-1 focus:ring-[#2D5864] focus:outline-hidden"
                />
              </div>

              <div className="bg-[#FAF8F5] p-3 rounded-lg border border-[#F2E8D8] space-y-2">
                <span className="font-semibold text-neutral-800 block text-[11px]">Archivos adjuntos a incluir:</span>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={adjuntarPdf2}
                    onChange={e => setAdjuntarPdf2(e.target.checked)}
                    className="w-4 h-4 rounded text-[#2D5864] border-neutral-300 focus:ring-[#2D5864]"
                  />
                  <span className="text-neutral-700 font-medium">Informe Oficial de Bioseguridad en PDF (.pdf)</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={adjuntarExcel2}
                    onChange={e => setAdjuntarExcel2(e.target.checked)}
                    className="w-4 h-4 rounded text-[#2D5864] border-neutral-300 focus:ring-[#2D5864]"
                  />
                  <span className="text-neutral-700 font-medium">Libro de datos detallado en Excel (.xlsx)</span>
                </label>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-neutral-100">
                <button
                  type="button"
                  onClick={() => setModalEmail2Open(false)}
                  disabled={enviandoEmail2}
                  className="px-3.5 py-2 text-neutral-600 hover:bg-neutral-100 rounded-lg transition-colors"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={enviandoEmail2 || !emailDestinatario2}
                  className="px-4 py-2 font-semibold text-white bg-[#2D5864] hover:bg-[#23454f] rounded-lg transition-colors flex items-center gap-1.5 disabled:opacity-50 shadow-xs"
                >
                  {enviandoEmail2 ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Enviando...</span>
                    </>
                  ) : (
                    <>
                      <Send className="w-3.5 h-3.5" />
                      <span>Enviar Informe</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

