import React, { useState, useEffect, useMemo } from 'react';
import { 
  Truck, 
  FlaskConical, 
  CheckCircle2, 
  AlertTriangle, 
  Filter, 
  Search, 
  ShieldAlert, 
  Thermometer,
  Lock,
  Unlock
} from 'lucide-react';
import { useVeterinaria } from '../../../context/VeterinariaContext';
import { ReporteRechazadasResponse } from './types';
import { ReporteHeaderBanner, KpiCard, ReporteAccionesBar, ModalEnvioCorreo } from './common';

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
      if (!res.ok) throw new Error('Error al consultar datos de muestras rechazadas');
      const data: ReporteRechazadasResponse = await res.json();
      setReporte2Data(data);
    } catch (err) {
      showToast({
        type: 'error',
        title: 'Error al cargar reporte 2',
        description: err instanceof Error ? err.message : 'Error al conectar con la API de reportes.'
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

  const handleEnviarEmail2 = async (destinatario: string, asunto: string, incluirPdf: boolean, incluirExcel: boolean) => {
    setEnviandoEmail2(true);
    try {
      const payload = {
        destinatario,
        asunto: asunto || undefined,
        incluir_pdf: incluirPdf,
        incluir_excel: incluirExcel,
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
        description: `El informe oficial fue enviado con éxito a ${destinatario}.`
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
      {/* Banner Superior Reutilizable */}
      <ReporteHeaderBanner
        titulo="PATITAS & CO. — AUDITORÍA DE BIOSEGURIDAD Y CONTROL DE TRANSPORTE"
        subtitulo="Reporte 2: Muestras Biológicas Rechazadas por Fallas en Transporte y Bioseguridad"
      />

      {/* Barra de Filtros y Acciones */}
      <div className="bg-white border border-[#E7E2DA] rounded-xl p-4 shadow-xs space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-[#2D5864]" />
            <span className="text-xs font-bold text-neutral-900 uppercase tracking-wider">Filtros de Bioseguridad:</span>
          </div>

          <ReporteAccionesBar
            onDescargarExcel={() => void descargarArchivo2('excel')}
            onDescargarPdf={() => void descargarArchivo2('pdf')}
            onAbrirModalEmail={() => setModalEmail2Open(true)}
            onRecargar={() => void cargarReporte2()}
            cargando={cargando2}
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 pt-2 border-t border-neutral-100 text-xs">
          <div>
            <label className="block text-[11px] font-semibold text-neutral-600 mb-1">Causa de Rechazo</label>
            <select
              value={filtroCausa2}
              onChange={e => setFiltroCausa2(e.target.value)}
              className="w-full p-2 bg-[#FAF8F5] border border-[#E7E2DA] rounded-lg text-neutral-800 font-medium"
            >
              {(reporte2Data?.filtros_disponibles.causas || ['Todas']).map(c => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-neutral-600 mb-1">Transportista</label>
            <select
              value={filtroTransportista2}
              onChange={e => setFiltroTransportista2(e.target.value)}
              className="w-full p-2 bg-[#FAF8F5] border border-[#E7E2DA] rounded-lg text-neutral-800 font-medium"
            >
              {(reporte2Data?.filtros_disponibles.transportistas || ['Todos']).map(t => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-neutral-600 mb-1">Estado de Muestra</label>
            <select
              value={filtroEstado2}
              onChange={e => setFiltroEstado2(e.target.value)}
              className="w-full p-2 bg-[#FAF8F5] border border-[#E7E2DA] rounded-lg text-neutral-800 font-medium"
            >
              {(reporte2Data?.filtros_disponibles.estados || ['Todos', 'Rechazada', 'Aceptada']).map(est => (
                <option key={est} value={est}>{est}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-neutral-600 mb-1">Desde</label>
            <input
              type="date"
              value={fechaDesde2}
              onChange={e => setFechaDesde2(e.target.value)}
              className="w-full p-2 bg-[#FAF8F5] border border-[#E7E2DA] rounded-lg text-neutral-800 font-medium"
            />
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-neutral-600 mb-1">Hasta</label>
            <input
              type="date"
              value={fechaHasta2}
              onChange={e => setFechaHasta2(e.target.value)}
              className="w-full p-2 bg-[#FAF8F5] border border-[#E7E2DA] rounded-lg text-neutral-800 font-medium"
            />
          </div>
        </div>
      </div>

      {/* Tarjetas KPIs Reutilizables */}
      {reporte2Data && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          <KpiCard
            titulo="Auditadas"
            valor={reporte2Data.kpis.total_muestras_auditadas}
            unidad="muestras"
            subtexto="100% trazabilidad"
            icono={FlaskConical}
            colorIcono="text-[#2D5864]"
            colorValor="text-[#2D5864]"
          />
          <KpiCard
            titulo="Conformes"
            valor={reporte2Data.kpis.muestras_aceptadas}
            unidad={`(${reporte2Data.kpis.tasa_conformidad_porcentaje}%)`}
            subtexto="Aprobadas para análisis"
            icono={CheckCircle2}
            colorIcono="text-emerald-600"
            colorValor="text-emerald-700"
          />
          <KpiCard
            titulo="Rechazadas"
            valor={reporte2Data.kpis.muestras_rechazadas}
            unidad={`(${reporte2Data.kpis.tasa_rechazo_global_porcentaje}%)`}
            subtexto="Descarte por bioseguridad"
            icono={ShieldAlert}
            colorIcono="text-rose-600"
            colorValor="text-rose-700"
          />
          <KpiCard
            titulo="Tasa Rechazo"
            valor={`${reporte2Data.kpis.tasa_rechazo_global_porcentaje}%`}
            subtexto="Meta tolerancia: < 5%"
            icono={AlertTriangle}
            colorIcono="text-amber-600"
            colorValor={reporte2Data.kpis.tasa_rechazo_global_porcentaje <= 5.0 ? 'text-amber-600' : 'text-rose-700'}
          />
          <KpiCard
            titulo="Precintos"
            valor={`${reporte2Data.kpis.integridad_precintos_porcentaje}%`}
            unidad="íntegros"
            subtexto={`${reporte2Data.kpis.precintos_violados_o_rotos} con alteración`}
            icono={Lock}
            colorIcono="text-sky-600"
            colorValor="text-sky-800"
          />
          <KpiCard
            titulo="Cadena de Frío"
            valor={`${reporte2Data.kpis.conformidad_cadena_frio_porcentaje}%`}
            unidad="en rango"
            subtexto={`${reporte2Data.kpis.excursiones_termicas} excursiones > 8°C`}
            icono={Thermometer}
            colorIcono="text-indigo-600"
            colorValor="text-indigo-800"
          />
        </div>
      )}

      {/* Gráficos y Tablas Analíticas */}
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
                      <span className="font-bold text-neutral-900">{item.cantidad} ({item.porcentaje}%)</span>
                    </div>

                    <div className="w-full bg-neutral-100 h-2 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${
                          item.severidad === 'Crítica' ? 'bg-rose-500' : 'bg-amber-500'
                        }`}
                        style={{ width: `${Math.min(item.porcentaje * 2, 100)}%` }}
                      />
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Gráfico 2: Desempeño Logístico */}
          <div className="bg-white border border-[#E7E2DA] rounded-xl p-5 shadow-xs space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Truck className="w-4 h-4 text-[#2D5864]" />
                <h4 className="font-bold text-sm text-[#2D5864]">Confiabilidad y Desempeño Logístico</h4>
              </div>
              <span className="text-[10px] text-neutral-400">Auditoría por chofer / flota</span>
            </div>

            <div className="space-y-3.5 pt-2">
              {reporte2Data.confiabilidad_transportistas.map(tr => (
                <div key={tr.transportista} className="p-3 bg-[#FAF8F5] rounded-lg border border-[#F2E8D8] space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-neutral-900">{tr.transportista}</span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      tr.calificacion === 'Excelente'
                        ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                        : tr.calificacion === 'Aceptable'
                        ? 'bg-amber-100 text-amber-800 border border-amber-200'
                        : 'bg-rose-100 text-rose-800 border border-rose-200'
                    }`}>
                      {tr.calificacion} ({tr.tasa_conformidad_porcentaje}% conforme)
                    </span>
                  </div>

                  <div className="w-full bg-neutral-200 h-2 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        tr.tasa_conformidad_porcentaje >= 95 ? 'bg-emerald-500' : tr.tasa_conformidad_porcentaje >= 80 ? 'bg-amber-500' : 'bg-rose-500'
                      }`}
                      style={{ width: `${tr.tasa_conformidad_porcentaje}%` }}
                    />
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-neutral-500">
                    <span>
                      {tr.muestras_conformes} conformes · {tr.muestras_rechazadas} rechazadas (Total: {tr.total_muestras})
                    </span>
                    <span className="italic">Incidencia: {tr.falla_frecuente}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tabla de Auditoría */}
      <div className="bg-white border border-[#E7E2DA] rounded-xl shadow-xs overflow-hidden">
        <div className="p-4 border-b border-[#E7E2DA] flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#FAF8F5]">
          <div>
            <h4 className="font-bold text-sm text-[#2D5864]">Registro de Seguridad Sanitaria y Control de Precintos</h4>
            <p className="text-xs text-neutral-500 mt-0.5">
              Trazabilidad física de recipientes, cadena de frío y firmas de custodia
            </p>
          </div>

          <div className="relative w-full sm:w-72">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400" />
            <input
              type="text"
              placeholder="Buscar muestra, tutor, precinto o causa..."
              value={busquedaTabla2}
              onChange={e => setBusquedaTabla2(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 bg-white border border-[#E7E2DA] rounded-lg text-xs text-neutral-800 focus:outline-hidden focus:ring-1 focus:ring-[#2D5864]"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#FAF8F5] text-neutral-600 font-semibold border-b border-[#E7E2DA]">
              <tr>
                <th className="py-2.5 px-3">Código</th>
                <th className="py-2.5 px-3">Paciente / Tutor</th>
                <th className="py-2.5 px-3">Tipo Análisis</th>
                <th className="py-2.5 px-3">Transportista / Remito</th>
                <th className="py-2.5 px-3">Precinto</th>
                <th className="py-2.5 px-3">Temperatura</th>
                <th className="py-2.5 px-3">Estado</th>
                <th className="py-2.5 px-3">Causa de Rechazo / Acción</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E7E2DA]">
              {muestrasRechazadasFiltradas.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-neutral-400 italic">
                    No se encontraron registros de auditoría que coincidan con la búsqueda o filtros.
                  </td>
                </tr>
              ) : (
                muestrasRechazadasFiltradas.map(d => {
                  const esRechazada = d.estado_muestra === 'Rechazada';
                  return (
                    <tr key={d.muestra_codigo} className="hover:bg-[#FAF8F5]/80 transition-colors">
                      <td className="py-2.5 px-3 font-mono font-bold text-neutral-800">
                        {d.muestra_codigo}
                      </td>
                      <td className="py-2.5 px-3">
                        <span className="font-semibold text-neutral-900 block">{d.paciente_nombre} ({d.especie})</span>
                        <span className="text-[10px] text-neutral-400">{d.tutor_nombre}</span>
                      </td>
                      <td className="py-2.5 px-3 text-neutral-700">{d.tipo_analisis}</td>
                      <td className="py-2.5 px-3 text-neutral-600">
                        <span className="block">{d.transportista}</span>
                        <span className="text-[10px] font-mono text-neutral-400">{d.remito_numero}</span>
                      </td>
                      <td className="py-2.5 px-3">
                        <span className={`inline-flex items-center gap-1 font-mono text-[10px] px-2 py-0.5 rounded-full font-bold ${
                          d.estado_precinto === 'Integro'
                            ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                            : 'bg-rose-50 text-rose-800 border border-rose-200'
                        }`}>
                          {d.estado_precinto === 'Integro' ? <Lock className="w-2.5 h-2.5" /> : <Unlock className="w-2.5 h-2.5" />}
                          {d.estado_precinto}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 font-mono">
                        <span className={`font-semibold ${d.temperatura_conforme ? 'text-emerald-700' : 'text-rose-700 font-bold'}`}>
                          {d.temperatura_llegada_c}°C
                        </span>
                        <span className="text-[10px] text-neutral-400 block">{d.rango_admitido}</span>
                      </td>
                      <td className="py-2.5 px-3">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold inline-flex items-center gap-1 ${
                          esRechazada
                            ? 'bg-rose-100 text-rose-800 border border-rose-200'
                            : 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                        }`}>
                          {esRechazada ? <AlertTriangle className="w-3 h-3 text-rose-600" /> : <CheckCircle2 className="w-3 h-3 text-emerald-600" />}
                          {d.estado_muestra}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 max-w-xs">
                        {d.causa_rechazo ? (
                          <div>
                            <span className="font-bold text-rose-800 text-[11px] block">{d.causa_rechazo}</span>
                            <span className="text-[10px] text-neutral-500 italic block mt-0.5">{d.accion_correctiva}</span>
                          </div>
                        ) : (
                          <span className="text-emerald-700 font-medium text-[11px]">Conforme sin observaciones</span>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal Reutilizable */}
      <ModalEnvioCorreo
        isOpen={modalEmail2Open}
        onClose={() => setModalEmail2Open(false)}
        onEnviar={handleEnviarEmail2}
        enviando={enviandoEmail2}
        tituloReporte="Auditoría de Muestras Rechazadas"
        placeholderAsunto="Auditoría de Muestras Rechazadas — Patitas & Co."
        etiquetaPdf="Informe Oficial de Bioseguridad en PDF (.pdf)"
        etiquetaExcel="Libro de datos detallado en Excel (.xlsx)"
      />
    </div>
  );
};
