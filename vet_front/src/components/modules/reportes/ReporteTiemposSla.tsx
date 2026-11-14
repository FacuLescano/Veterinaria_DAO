import React, { useState, useEffect, useMemo } from 'react';
import { 
  Clock, 
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
  Check, 
  X,
  Send,
  Loader2
} from 'lucide-react';
import { useVeterinaria } from '../../../context/VeterinariaContext';
import { ReporteTiemposResponse } from './types';

export const ReporteTiemposSla: React.FC = () => {
  const { showToast } = useVeterinaria();

  const [reporteData, setReporteData] = useState<ReporteTiemposResponse | null>(null);
  const [cargando, setCargando] = useState(false);

  // Filtros
  const [fechaDesde, setFechaDesde] = useState('');
  const [fechaHasta, setFechaHasta] = useState('');
  const [filtroTipo, setFiltroTipo] = useState('Todos');
  const [filtroTransportista, setFiltroTransportista] = useState('Todos');
  const [filtroPrioridad, setFiltroPrioridad] = useState('Todas');
  const [busquedaTabla, setBusquedaTabla] = useState('');

  // Modal Enviar por Correo
  const [modalEmailOpen, setModalEmailOpen] = useState(false);
  const [emailDestinatario, setEmailDestinatario] = useState('iswingsistemas@gmail.com');
  const [asuntoEmail, setAsuntoEmail] = useState('');
  const [adjuntarPdf, setAdjuntarPdf] = useState(true);
  const [adjuntarExcel, setAdjuntarExcel] = useState(true);
  const [enviandoEmail, setEnviandoEmail] = useState(false);

  const cargarReporte = async () => {
    setCargando(true);
    try {
      const params = new URLSearchParams();
      if (fechaDesde) params.append('fecha_desde', fechaDesde);
      if (fechaHasta) params.append('fecha_hasta', fechaHasta);
      if (filtroTipo !== 'Todos') params.append('tipo_analisis', filtroTipo);
      if (filtroTransportista !== 'Todos') params.append('transportista', filtroTransportista);
      if (filtroPrioridad !== 'Todas') params.append('prioridad', filtroPrioridad);

      const res = await fetch(`/api/v1/reportes/tiempos-sla?${params.toString()}`);
      if (!res.ok) throw new Error('No se pudo obtener el reporte');
      const data: ReporteTiemposResponse = await res.json();
      setReporteData(data);
    } catch (err) {
      showToast({
        type: 'error',
        title: 'Error al cargar reporte',
        description: err instanceof Error ? err.message : 'Error de comunicación con el backend.'
      });
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    void cargarReporte();
  }, [fechaDesde, fechaHasta, filtroTipo, filtroTransportista, filtroPrioridad]);

  const descargarArchivo = async (formato: 'excel' | 'pdf') => {
    try {
      const params = new URLSearchParams();
      if (fechaDesde) params.append('fecha_desde', fechaDesde);
      if (fechaHasta) params.append('fecha_hasta', fechaHasta);
      if (filtroTipo !== 'Todos') params.append('tipo_analisis', filtroTipo);
      if (filtroTransportista !== 'Todos') params.append('transportista', filtroTransportista);
      if (filtroPrioridad !== 'Todas') params.append('prioridad', filtroPrioridad);

      const endpoint = `/api/v1/reportes/tiempos-sla/${formato}?${params.toString()}`;
      const res = await fetch(endpoint);
      if (!res.ok) throw new Error(`Error al generar ${formato.toUpperCase()}`);

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = formato === 'excel' ? 'reporte_tiempos_sla.xlsx' : 'reporte_tiempos_sla.pdf';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      showToast({
        type: 'success',
        title: `Descarga completada`,
        description: `Se descargó el archivo ${formato.toUpperCase()} exitosamente.`
      });
    } catch (err) {
      showToast({
        type: 'error',
        title: `Fallo en la descarga`,
        description: err instanceof Error ? err.message : 'No se pudo descargar el archivo.'
      });
    }
  };

  const handleEnviarEmail = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!emailDestinatario) return;

    setEnviandoEmail(true);
    try {
      const payload = {
        destinatario: emailDestinatario,
        asunto: asuntoEmail || undefined,
        incluir_pdf: adjuntarPdf,
        incluir_excel: adjuntarExcel,
        fecha_desde: fechaDesde || undefined,
        fecha_hasta: fechaHasta || undefined,
        tipo_analisis: filtroTipo !== 'Todos' ? filtroTipo : undefined,
        transportista: filtroTransportista !== 'Todos' ? filtroTransportista : undefined,
        prioridad: filtroPrioridad !== 'Todas' ? filtroPrioridad : undefined
      };

      const res = await fetch('/api/v1/reportes/tiempos-sla/enviar-email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Error al enviar correo');

      showToast({
        type: 'success',
        title: 'Correo enviado',
        description: `El reporte oficial fue enviado con éxito a ${emailDestinatario}.`
      });
      setModalEmailOpen(false);
    } catch (err) {
      showToast({
        type: 'error',
        title: 'Error de envío SMTP',
        description: err instanceof Error ? err.message : 'No se pudo enviar el correo.'
      });
    } finally {
      setEnviandoEmail(false);
    }
  };

  const muestrasFiltradas = useMemo(() => {
    if (!reporteData) return [];
    if (!busquedaTabla.trim()) return reporteData.detalles_muestras;
    const q = busquedaTabla.toLowerCase();
    return reporteData.detalles_muestras.filter(d => 
      d.muestra_codigo.toLowerCase().includes(q) ||
      d.paciente_nombre.toLowerCase().includes(q) ||
      d.tutor_nombre.toLowerCase().includes(q) ||
      d.tipo_analisis.toLowerCase().includes(q) ||
      d.remito_numero.toLowerCase().includes(q) ||
      d.transportista.toLowerCase().includes(q)
    );
  }, [reporteData, busquedaTabla]);

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
              PATITAS & CO. — AUDITORÍA Y TRAZABILIDAD SANITARIA
            </h3>
            <p className="text-xs text-neutral-500 mt-0.5">
              Reporte 1: Tiempo Promedio de Tránsito y Cumplimiento de SLA Analítico
            </p>
          </div>
        </div>
        <div className="text-right hidden sm:block">
          <span className="text-[10px] font-mono text-neutral-400 block">Sede Central Córdoba</span>
          <span className="text-[10px] text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full font-semibold border border-emerald-200">
            Res. SENASA N° 412/2026
          </span>
        </div>
      </div>

      <div className="bg-white border border-[#E7E2DA] rounded-xl p-4 shadow-xs space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-[#2D5864]" />
            <span className="text-xs font-bold text-neutral-900 uppercase tracking-wider">Filtros de Auditoría:</span>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => void descargarArchivo('excel')}
              className="px-3 py-1.5 text-xs font-semibold text-emerald-800 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 rounded-lg transition-colors flex items-center gap-1.5 shadow-2xs"
              title="Descargar libro Excel con tablas y formato"
            >
              <FileSpreadsheet className="w-3.5 h-3.5" />
              <span>Descargar Excel</span>
            </button>

            <button
              onClick={() => void descargarArchivo('pdf')}
              className="px-3 py-1.5 text-xs font-semibold text-rose-800 bg-rose-50 hover:bg-rose-100 border border-rose-200 rounded-lg transition-colors flex items-center gap-1.5 shadow-2xs"
              title="Descargar informe oficial en PDF"
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Descargar PDF</span>
            </button>

            <button
              onClick={() => setModalEmailOpen(true)}
              className="px-3 py-1.5 text-xs font-semibold text-white bg-[#2D5864] hover:bg-[#23454f] rounded-lg transition-colors flex items-center gap-1.5 shadow-xs"
            >
              <Mail className="w-3.5 h-3.5" />
              <span>Enviar por Correo</span>
            </button>

            <button
              onClick={() => void cargarReporte()}
              disabled={cargando}
              className="p-1.5 text-neutral-500 hover:text-[#2D5864] hover:bg-neutral-100 rounded-lg transition-colors"
              title="Actualizar datos"
            >
              <RefreshCw className={`w-4 h-4 ${cargando ? 'animate-spin text-[#2D5864]' : ''}`} />
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-2 border-t border-neutral-100 text-xs">
          <div>
            <label className="block text-neutral-500 font-medium mb-1">Tipo de Análisis</label>
            <select
              value={filtroTipo}
              onChange={e => setFiltroTipo(e.target.value)}
              className="w-full p-2 bg-[#FAF8F5] border border-[#E7E2DA] rounded-lg text-neutral-800 font-medium"
            >
              <option value="Todos">Todos los estudios</option>
              {reporteData?.filtros_disponibles.tipos_analisis.map(t => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-neutral-500 font-medium mb-1">Transportista</label>
            <select
              value={filtroTransportista}
              onChange={e => setFiltroTransportista(e.target.value)}
              className="w-full p-2 bg-[#FAF8F5] border border-[#E7E2DA] rounded-lg text-neutral-800 font-medium"
            >
              <option value="Todos">Todos los transportistas</option>
              {reporteData?.filtros_disponibles.transportistas.map(tr => (
                <option key={tr} value={tr}>{tr}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-neutral-500 font-medium mb-1">Prioridad Médica</label>
            <select
              value={filtroPrioridad}
              onChange={e => setFiltroPrioridad(e.target.value)}
              className="w-full p-2 bg-[#FAF8F5] border border-[#E7E2DA] rounded-lg text-neutral-800 font-medium"
            >
              <option value="Todas">Todas las prioridades</option>
              <option value="Normal">Normal</option>
              <option value="Urgente">Urgente</option>
            </select>
          </div>

          <div>
            <label className="block text-neutral-500 font-medium mb-1">Búsqueda rápida</label>
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-neutral-400" />
              <input
                type="text"
                placeholder="Muestra, paciente o remito..."
                value={busquedaTabla}
                onChange={e => setBusquedaTabla(e.target.value)}
                className="w-full pl-8 pr-3 py-2 bg-[#FAF8F5] border border-[#E7E2DA] rounded-lg text-neutral-800"
              />
            </div>
          </div>
        </div>
      </div>

      {reporteData && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          <div className="p-3.5 bg-white border border-[#E7E2DA] rounded-xl shadow-2xs">
            <span className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">Muestras Analizadas</span>
            <span className="text-xl font-bold text-neutral-900 mt-1 block">
              {reporteData.kpis.total_muestras_analizadas}
            </span>
            <span className="text-[10px] text-neutral-500 mt-0.5 block">100% con trazabilidad</span>
          </div>

          <div className="p-3.5 bg-white border border-[#E7E2DA] rounded-xl shadow-2xs">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider">Promedio Tránsito</span>
              <Truck className="w-3.5 h-3.5 text-[#5F8E9C]" />
            </div>
            <span className="text-xl font-bold text-[#2D5864] mt-1 block">
              {reporteData.kpis.tiempo_promedio_transito_horas} <span className="text-xs font-normal text-neutral-500">hs</span>
            </span>
            <span className="text-[10px] text-emerald-600 font-medium mt-0.5 block">En rango óptimo</span>
          </div>

          <div className="p-3.5 bg-white border border-[#E7E2DA] rounded-xl shadow-2xs">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider">Proceso Lab</span>
              <FlaskConical className="w-3.5 h-3.5 text-[#5F8E9C]" />
            </div>
            <span className="text-xl font-bold text-[#2D5864] mt-1 block">
              {reporteData.kpis.tiempo_promedio_procesamiento_horas} <span className="text-xs font-normal text-neutral-500">hs</span>
            </span>
            <span className="text-[10px] text-neutral-500 mt-0.5 block">Desde recepción en sede</span>
          </div>

          <div className="p-3.5 bg-white border border-[#E7E2DA] rounded-xl shadow-2xs">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider">Ciclo Total (TAT)</span>
              <Clock className="w-3.5 h-3.5 text-[#2D5864]" />
            </div>
            <span className="text-xl font-bold text-neutral-900 mt-1 block">
              {reporteData.kpis.tiempo_promedio_total_horas} <span className="text-xs font-normal text-neutral-500">hs</span>
            </span>
            <span className="text-[10px] text-neutral-500 mt-0.5 block">Extracción ➔ Informe</span>
          </div>

          <div className="p-3.5 bg-[#FAF6EF] border border-[#F2E8D8] rounded-xl shadow-2xs">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold text-[#2D5864] uppercase tracking-wider">Cumplimiento SLA</span>
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            </div>
            <span className="text-xl font-bold text-emerald-700 mt-1 block">
              {reporteData.kpis.tasa_cumplimiento_sla_porcentaje}%
            </span>
            <div className="w-full bg-neutral-200 h-1.5 rounded-full mt-1.5 overflow-hidden">
              <div
                className="bg-emerald-600 h-full rounded-full transition-all duration-500"
                style={{ width: `${reporteData.kpis.tasa_cumplimiento_sla_porcentaje}%` }}
              />
            </div>
          </div>

          <div className="p-3.5 bg-white border border-[#E7E2DA] rounded-xl shadow-2xs">
            <span className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">Estado de Muestras</span>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-base font-bold text-emerald-700">{reporteData.kpis.muestras_en_plazo} en plazo</span>
            </div>
            <span className={`text-[10px] font-medium block mt-0.5 ${reporteData.kpis.muestras_demoradas > 0 ? 'text-rose-600' : 'text-neutral-400'}`}>
              {reporteData.kpis.muestras_demoradas} demoradas
            </span>
          </div>
        </div>
      )}

      {/* Gráficos Visuales de Gestión */}
      {reporteData && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          <div className="lg:col-span-2 bg-white border border-[#E7E2DA] rounded-xl p-5 shadow-xs space-y-4">
            <div className="flex items-center justify-between border-b border-neutral-100 pb-3">
              <div>
                <h4 className="text-xs font-bold text-neutral-900 uppercase tracking-wider">
                  Tiempos Promedio vs. SLA Objetivo por Tipo de Análisis
                </h4>
                <p className="text-[11px] text-neutral-500">
                  Comparativa de horas de viaje (tránsito) y horas de análisis respecto al compromiso de entrega
                </p>
              </div>
              <div className="flex items-center gap-3 text-[10px]">
                <div className="flex items-center gap-1">
                  <span className="w-2.5 h-2.5 rounded-xs bg-[#5F8E9C]"></span>
                  <span className="text-neutral-600">Tránsito</span>
                </div>
                <div className="flex items-center gap-1">
                  <span className="w-2.5 h-2.5 rounded-xs bg-[#2D5864]"></span>
                  <span className="text-neutral-600">Proceso Lab</span>
                </div>
                <div className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full border border-rose-500 bg-rose-50"></span>
                  <span className="text-neutral-600">Límite SLA</span>
                </div>
              </div>
            </div>

            <div className="space-y-3.5">
              {reporteData.sla_por_tipo_analisis.map(item => {
                const maxScale = Math.max(item.sla_objetivo_horas * 1.15, item.tiempo_total_promedio_horas * 1.15, 30);
                const pctTransito = (item.tiempo_transito_promedio_horas / maxScale) * 100;
                const pctProceso = (item.tiempo_procesamiento_promedio_horas / maxScale) * 100;
                const pctSlaMarker = (item.sla_objetivo_horas / maxScale) * 100;

                return (
                  <div key={item.tipo_analisis} className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-medium text-neutral-800">{item.tipo_analisis}</span>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-[11px] text-neutral-600">
                          Total: <strong>{item.tiempo_total_promedio_horas} hs</strong> / Meta: {item.sla_objetivo_horas} hs
                        </span>
                        <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                          item.cumplimiento_porcentaje >= 85
                            ? 'bg-emerald-50 text-emerald-700'
                            : 'bg-rose-50 text-rose-700'
                        }`}>
                          {item.cumplimiento_porcentaje}% SLA
                        </span>
                      </div>
                    </div>

                    <div className="relative h-4 bg-neutral-100 rounded-md overflow-hidden flex">
                      <div
                        style={{ width: `${pctTransito}%` }}
                        className="bg-[#5F8E9C] h-full"
                        title={`Tránsito: ${item.tiempo_transito_promedio_horas} hs`}
                      />
                      <div
                        style={{ width: `${pctProceso}%` }}
                        className="bg-[#2D5864] h-full"
                        title={`Procesamiento: ${item.tiempo_procesamiento_promedio_horas} hs`}
                      />
                      <div
                        style={{ left: `${pctSlaMarker}%` }}
                        className="absolute top-0 bottom-0 w-0.5 bg-rose-500 z-10"
                        title={`Límite SLA: ${item.sla_objetivo_horas} hs`}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="bg-white border border-[#E7E2DA] rounded-xl p-5 shadow-xs space-y-4 flex flex-col justify-between">
            <div>
              <h4 className="text-xs font-bold text-neutral-900 uppercase tracking-wider border-b border-neutral-100 pb-3">
                Puntualidad por Transportista
              </h4>
              <div className="divide-y divide-neutral-100 mt-3">
                {reporteData.rendimiento_transportistas.map(tr => (
                  <div key={tr.transportista} className="py-3 first:pt-0 last:pb-0 space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-neutral-800">{tr.transportista}</span>
                      <span className="font-bold text-emerald-700">{tr.puntualidad_porcentaje}%</span>
                    </div>
                    <div className="w-full bg-neutral-100 h-2 rounded-full overflow-hidden">
                      <div
                        className="bg-[#2D5864] h-full rounded-full"
                        style={{ width: `${tr.puntualidad_porcentaje}%` }}
                      />
                    </div>
                    <div className="flex items-center justify-between text-[11px] text-neutral-400">
                      <span>{tr.muestras_transportadas} muestras en {tr.envios_realizados} envíos</span>
                      <span>Viaje medio: {tr.tiempo_promedio_viaje_horas} hs</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="p-3 bg-[#FAF6EF] rounded-lg border border-[#F2E8D8] text-[11px] text-[#2D5864]">
              <strong>Criterio de logística:</strong> Se considera entrega puntual cuando el traslado entre clínica solicitante y laboratorio central no excede las 6 horas.
            </div>
          </div>
        </div>
      )}

      {/* Tabla detallada de muestras */}
      <div className="bg-white border border-[#E7E2DA] rounded-xl shadow-xs overflow-hidden">
        <div className="p-4 border-b border-neutral-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h4 className="text-xs font-bold text-neutral-900 uppercase tracking-wider">
              Detalle de Muestras Analizadas ({muestrasFiltradas.length})
            </h4>
            <p className="text-[11px] text-neutral-500">
              Historial trazable de tiempos y verificación de cumplimiento del SLA
            </p>
          </div>

          <span className="text-xs font-medium text-neutral-500 bg-neutral-100 px-2.5 py-1 rounded-md">
            Mostrando {muestrasFiltradas.length} de {reporteData?.detalles_muestras.length || 0} registros
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#FAF8F5] text-neutral-600 border-b border-neutral-200 uppercase font-mono text-[10px] tracking-wider">
              <tr>
                <th className="py-2.5 px-3.5">Muestra</th>
                <th className="py-2.5 px-3.5">Paciente & Tutor</th>
                <th className="py-2.5 px-3.5">Tipo Análisis</th>
                <th className="py-2.5 px-3.5">Prioridad</th>
                <th className="py-2.5 px-3.5">Transportista</th>
                <th className="py-2.5 px-3.5 text-center">Tránsito</th>
                <th className="py-2.5 px-3.5 text-center">Proceso</th>
                <th className="py-2.5 px-3.5 text-center">Total (TAT)</th>
                <th className="py-2.5 px-3.5 text-center">SLA Meta</th>
                <th className="py-2.5 px-3.5 text-center">Estado SLA</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100">
              {muestrasFiltradas.map(d => (
                <tr key={d.muestra_codigo} className="hover:bg-neutral-50/70 transition-colors">
                  <td className="py-2.5 px-3.5 font-mono font-bold text-[#2D5864] whitespace-nowrap">
                    {d.muestra_codigo}
                  </td>
                  <td className="py-2.5 px-3.5">
                    <span className="font-semibold text-neutral-900 block">{d.paciente_nombre}</span>
                    <span className="text-[10px] text-neutral-400 block">{d.especie} · {d.tutor_nombre}</span>
                  </td>
                  <td className="py-2.5 px-3.5 font-medium text-neutral-800">
                    {d.tipo_analisis}
                  </td>
                  <td className="py-2.5 px-3.5">
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      d.prioridad === 'Urgente'
                        ? 'bg-rose-100 text-rose-800'
                        : 'bg-neutral-100 text-neutral-700'
                    }`}>
                      {d.prioridad}
                    </span>
                  </td>
                  <td className="py-2.5 px-3.5 text-neutral-600">
                    <span className="block truncate max-w-[150px]">{d.transportista}</span>
                    <span className="text-[10px] font-mono text-neutral-400">{d.remito_numero}</span>
                  </td>
                  <td className="py-2.5 px-3.5 font-mono text-center text-neutral-700">
                    {d.tiempo_transito_horas} hs
                  </td>
                  <td className="py-2.5 px-3.5 font-mono text-center text-neutral-700">
                    {d.tiempo_procesamiento_horas} hs
                  </td>
                  <td className="py-2.5 px-3.5 font-mono font-bold text-center text-[#2D5864]">
                    {d.tiempo_total_horas} hs
                  </td>
                  <td className="py-2.5 px-3.5 font-mono text-center text-neutral-500">
                    {d.sla_objetivo_horas} hs
                  </td>
                  <td className="py-2.5 px-3.5 text-center whitespace-nowrap">
                    {d.cumple_sla ? (
                      <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
                        <Check className="w-3 h-3 text-emerald-600" />
                        A Tiempo
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-rose-700 bg-rose-50 px-2.5 py-0.5 rounded-full border border-rose-200">
                        <AlertTriangle className="w-3 h-3 text-rose-600" />
                        Demorado (+{d.diferencia_sla_horas}h)
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* MODAL: ENVIAR REPORTE POR EMAIL */}
      {modalEmailOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#2D5864]/40 backdrop-blur-xs">
          <div className="bg-white rounded-xl shadow-xl border border-[#E7E2DA] max-w-md w-full overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="px-5 py-4 border-b border-[#F2E8D8] flex items-center justify-between bg-[#FAF8F5]">
              <div className="flex items-center gap-2">
                <Mail className="w-4 h-4 text-[#2D5864]" />
                <h3 className="font-bold text-sm text-[#2D5864]">Enviar Reporte de Tiempos & SLA</h3>
              </div>
              <button
                onClick={() => setModalEmailOpen(false)}
                className="text-neutral-400 hover:text-neutral-700 p-1 rounded-md"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleEnviarEmail} className="p-5 space-y-4 text-xs">
              <div>
                <label className="block text-neutral-700 font-semibold mb-1">
                  Correo Electrónico Destinatario *
                </label>
                <input
                  type="email"
                  required
                  placeholder="ejemplo@veterinaria.com"
                  value={emailDestinatario}
                  onChange={e => setEmailDestinatario(e.target.value)}
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
                  placeholder="Reporte de Auditoría SLA — Patitas & Co."
                  value={asuntoEmail}
                  onChange={e => setAsuntoEmail(e.target.value)}
                  className="w-full p-2.5 border border-[#E7E2DA] rounded-lg text-neutral-900 focus:ring-1 focus:ring-[#2D5864] focus:outline-hidden"
                />
              </div>

              <div className="bg-[#FAF8F5] p-3 rounded-lg border border-[#F2E8D8] space-y-2">
                <span className="font-semibold text-neutral-800 block text-[11px]">Archivos adjuntos a incluir:</span>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={adjuntarPdf}
                    onChange={e => setAdjuntarPdf(e.target.checked)}
                    className="w-4 h-4 rounded text-[#2D5864] border-neutral-300 focus:ring-[#2D5864]"
                  />
                  <span className="text-neutral-700 font-medium">Informe Oficial en PDF (.pdf)</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={adjuntarExcel}
                    onChange={e => setAdjuntarExcel(e.target.checked)}
                    className="w-4 h-4 rounded text-[#2D5864] border-neutral-300 focus:ring-[#2D5864]"
                  />
                  <span className="text-neutral-700 font-medium">Libro de datos detallado en Excel (.xlsx)</span>
                </label>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-neutral-100">
                <button
                  type="button"
                  onClick={() => setModalEmailOpen(false)}
                  disabled={enviandoEmail}
                  className="px-3.5 py-2 text-neutral-600 hover:bg-neutral-100 rounded-lg transition-colors"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={enviandoEmail || !emailDestinatario}
                  className="px-4 py-2 font-semibold text-white bg-[#2D5864] hover:bg-[#23454f] rounded-lg transition-colors flex items-center gap-1.5 disabled:opacity-50 shadow-xs"
                >
                  {enviandoEmail ? (
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

