import React, { useState, useEffect, useMemo } from 'react';
import { 
  Clock, 
  Truck, 
  FlaskConical, 
  CheckCircle2, 
  AlertTriangle, 
  Filter, 
  Search, 
  Check, 
  X 
} from 'lucide-react';
import { useVeterinaria } from '../../../context/VeterinariaContext';
import { ReporteTiemposResponse } from './types';
import { ReporteHeaderBanner, KpiCard, ReporteAccionesBar, ModalEnvioCorreo } from './common';

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

  const handleEnviarEmail = async (destinatario: string, asunto: string, incluirPdf: boolean, incluirExcel: boolean) => {
    setEnviandoEmail(true);
    try {
      const payload = {
        destinatario,
        asunto: asunto || undefined,
        incluir_pdf: incluirPdf,
        incluir_excel: incluirExcel,
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
        description: `El reporte oficial fue enviado con éxito a ${destinatario}.`
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
      {/* Banner Superior Reutilizable */}
      <ReporteHeaderBanner
        titulo="PATITAS & CO. — TIEMPOS DE TRÁNSITO Y CUMPLIMIENTO DE SLA"
        subtitulo="Reporte 1: Monitoreo Logístico y Turnaround Time de Análisis Clínicos"
      />

      {/* Barra de Filtros y Acciones */}
      <div className="bg-white border border-[#E7E2DA] rounded-xl p-4 shadow-xs space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-[#2D5864]" />
            <span className="text-xs font-bold text-neutral-900 uppercase tracking-wider">Filtros de Búsqueda:</span>
          </div>

          <ReporteAccionesBar
            onDescargarExcel={() => void descargarArchivo('excel')}
            onDescargarPdf={() => void descargarArchivo('pdf')}
            onAbrirModalEmail={() => setModalEmailOpen(true)}
            onRecargar={() => void cargarReporte()}
            cargando={cargando}
          />
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

      {/* Tarjetas KPIs Reutilizables */}
      {reporteData && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          <KpiCard
            titulo="Muestras Analizadas"
            valor={reporteData.kpis.total_muestras_analizadas}
            subtexto="100% con trazabilidad"
            icono={FlaskConical}
            colorIcono="text-[#2D5864]"
            colorValor="text-neutral-900"
          />
          <KpiCard
            titulo="Promedio Tránsito"
            valor={`${reporteData.kpis.tiempo_promedio_transito_horas} hs`}
            subtexto="Clínica -> Laboratorio"
            icono={Truck}
            colorIcono="text-[#5F8E9C]"
            colorValor="text-neutral-900"
          />
          <KpiCard
            titulo="Promedio Análisis"
            valor={`${reporteData.kpis.tiempo_promedio_procesamiento_horas} hs`}
            subtexto="Ingreso -> Resultado"
            icono={Clock}
            colorIcono="text-[#5F8E9C]"
            colorValor="text-neutral-900"
          />
          <KpiCard
            titulo="Ciclo Total (TAT)"
            valor={`${reporteData.kpis.tiempo_promedio_total_horas} hs`}
            subtexto="Turnaround time promedio"
            icono={Clock}
            colorIcono="text-[#2D5864]"
            colorValor="text-[#2D5864]"
          />
          <KpiCard
            titulo="Cumplimiento SLA"
            valor={`${reporteData.kpis.tasa_cumplimiento_sla_porcentaje}%`}
            subtexto="Meta comprometida: >= 90%"
            icono={CheckCircle2}
            colorIcono="text-emerald-600"
            colorValor="text-emerald-700"
          />
          <KpiCard
            titulo="En Plazo / Demora"
            valor={`${reporteData.kpis.muestras_en_plazo} / ${reporteData.kpis.muestras_demoradas}`}
            subtexto="Muestras en SLA vs Demora"
            icono={AlertTriangle}
            colorIcono="text-amber-600"
            colorValor="text-neutral-900"
          />
        </div>
      )}

      {/* Gráficos de SLA y Transportistas */}
      {reporteData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Gráfico 1: SLA por Tipo de Análisis */}
          <div className="bg-white border border-[#E7E2DA] rounded-xl p-5 shadow-xs space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-bold text-sm text-[#2D5864]">Cumplimiento de SLA por Tipo de Análisis</h4>
                <p className="text-xs text-neutral-500">Horas reales promedio vs SLA objetivo acordado</p>
              </div>
              <span className="text-[10px] text-neutral-400 font-mono">Meta: 100%</span>
            </div>

            <div className="space-y-3.5 pt-2">
              {reporteData.sla_por_tipo_analisis.map(item => (
                <div key={item.tipo_analisis} className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-neutral-800">{item.tipo_analisis}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-neutral-500 text-[11px]">
                        {item.tiempo_total_promedio_horas}h / {item.sla_objetivo_horas}h
                      </span>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        item.estado_sla === 'Cumplido' 
                          ? 'bg-emerald-100 text-emerald-800' 
                          : item.estado_sla === 'En riesgo'
                          ? 'bg-amber-100 text-amber-800'
                          : 'bg-rose-100 text-rose-800'
                      }`}>
                        {item.cumplimiento_porcentaje}%
                      </span>
                    </div>
                  </div>

                  <div className="w-full bg-neutral-100 h-2 rounded-full overflow-hidden">
                    <div 
                      className={`h-full rounded-full transition-all duration-500 ${
                        item.estado_sla === 'Cumplido' 
                          ? 'bg-emerald-500' 
                          : item.estado_sla === 'En riesgo'
                          ? 'bg-amber-500'
                          : 'bg-rose-500'
                      }`}
                      style={{ width: `${Math.min(item.cumplimiento_porcentaje, 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Gráfico 2: Desempeño de Transportistas */}
          <div className="bg-white border border-[#E7E2DA] rounded-xl p-5 shadow-xs space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-bold text-sm text-[#2D5864]">Rendimiento por Transportista</h4>
                <p className="text-xs text-neutral-500">Tiempos de viaje y puntualidad en entregas a Central</p>
              </div>
              <span className="text-[10px] text-neutral-400 font-mono">Puntualidad</span>
            </div>

            <div className="space-y-4 pt-2">
              {reporteData.rendimiento_transportistas.map(tr => (
                <div key={tr.transportista} className="p-3 bg-[#FAF8F5] rounded-lg border border-[#F2E8D8] space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-neutral-900">{tr.transportista}</span>
                    <span className="text-emerald-700 font-semibold bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                      {tr.puntualidad_porcentaje}% a tiempo
                    </span>
                  </div>

                  <div className="w-full bg-neutral-200 h-1.5 rounded-full overflow-hidden">
                    <div 
                      className="bg-[#2D5864] h-full rounded-full"
                      style={{ width: `${tr.puntualidad_porcentaje}%` }}
                    />
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-neutral-500">
                    <span>{tr.envios_realizados} envíos · {tr.muestras_transportadas} muestras</span>
                    <span>Promedio viaje: <strong className="text-neutral-700">{tr.tiempo_promedio_viaje_horas} hs</strong></span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tabla Detallada con Búsqueda en Vivo */}
      <div className="bg-white border border-[#E7E2DA] rounded-xl shadow-xs overflow-hidden">
        <div className="p-4 border-b border-[#E7E2DA] flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#FAF8F5]">
          <div>
            <h4 className="font-bold text-sm text-[#2D5864]">Detalle Individual de Muestras</h4>
            <p className="text-xs text-neutral-500 mt-0.5">
              Trazabilidad completa con horas de despacho, arribo al laboratorio y emisión del informe
            </p>
          </div>
          <span className="text-xs text-neutral-400 font-medium">
            {muestrasFiltradas.length} de {reporteData?.detalles_muestras.length || 0} muestras
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#FAF8F5] text-neutral-600 font-semibold border-b border-[#E7E2DA]">
              <tr>
                <th className="py-2.5 px-3">Código</th>
                <th className="py-2.5 px-3">Paciente / Tutor</th>
                <th className="py-2.5 px-3">Tipo Análisis</th>
                <th className="py-2.5 px-3">Prioridad</th>
                <th className="py-2.5 px-3">Transportista</th>
                <th className="py-2.5 px-3 text-right">Tránsito</th>
                <th className="py-2.5 px-3 text-right">Proceso</th>
                <th className="py-2.5 px-3 text-right">Total TAT</th>
                <th className="py-2.5 px-3 text-right">SLA Objetivo</th>
                <th className="py-2.5 px-3 text-center">Estado SLA</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E7E2DA]">
              {muestrasFiltradas.length === 0 ? (
                <tr>
                  <td colSpan={10} className="py-8 text-center text-neutral-400 italic">
                    No se encontraron muestras que coincidan con los filtros aplicados.
                  </td>
                </tr>
              ) : (
                muestrasFiltradas.map(d => (
                  <tr key={d.muestra_codigo} className="hover:bg-[#FAF8F5]/80 transition-colors">
                    <td className="py-2.5 px-3 font-mono font-bold text-neutral-800">
                      {d.muestra_codigo}
                    </td>
                    <td className="py-2.5 px-3">
                      <span className="font-semibold text-neutral-900 block">{d.paciente_nombre} ({d.especie})</span>
                      <span className="text-[10px] text-neutral-400">{d.tutor_nombre}</span>
                    </td>
                    <td className="py-2.5 px-3 text-neutral-700">{d.tipo_analisis}</td>
                    <td className="py-2.5 px-3">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        d.prioridad === 'Urgente' 
                          ? 'bg-rose-100 text-rose-800 border border-rose-200' 
                          : 'bg-neutral-100 text-neutral-700 border border-neutral-200'
                      }`}>
                        {d.prioridad}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-neutral-600">
                      <span className="block">{d.transportista}</span>
                      <span className="text-[10px] font-mono text-neutral-400">{d.remito_numero}</span>
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono text-neutral-600">{d.tiempo_transito_horas}h</td>
                    <td className="py-2.5 px-3 text-right font-mono text-neutral-600">{d.tiempo_procesamiento_horas}h</td>
                    <td className="py-2.5 px-3 text-right font-mono font-bold text-neutral-900">{d.tiempo_total_horas}h</td>
                    <td className="py-2.5 px-3 text-right font-mono text-neutral-500">{d.sla_objetivo_horas}h</td>
                    <td className="py-2.5 px-3 text-center">
                      <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                        d.cumple_sla 
                          ? 'bg-emerald-100 text-emerald-800 border border-emerald-200' 
                          : 'bg-rose-100 text-rose-800 border border-rose-200'
                      }`}>
                        {d.cumple_sla ? <Check className="w-3 h-3 text-emerald-600" /> : <X className="w-3 h-3 text-rose-600" />}
                        {d.cumple_sla ? 'En Plazo' : `Demora (+${Math.abs(d.diferencia_sla_horas)}h)`}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal Reutilizable */}
      <ModalEnvioCorreo
        isOpen={modalEmailOpen}
        onClose={() => setModalEmailOpen(false)}
        onEnviar={handleEnviarEmail}
        enviando={enviandoEmail}
        tituloReporte="Reporte de Tiempos y SLA"
        placeholderAsunto="Reporte de Tiempos y SLA — Patitas & Co."
        etiquetaPdf="Informe Oficial de Tiempos y SLA en PDF (.pdf)"
        etiquetaExcel="Libro de datos detallado en Excel (.xlsx)"
      />
    </div>
  );
};
