import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { BarChart3, CheckCircle2, Clock3, FlaskConical, Microscope } from 'lucide-react';
import { useVeterinaria } from '../../../context/VeterinariaContext';
import { KpiCard, ModalEnvioCorreo, ReporteAccionesBar, ReporteHeaderBanner } from './common';

type Filtro = { parametro: string; etiqueta: string; opciones: string; inicial: string };
type Serie = { titulo: string; clave: string; categoria: string; valor: string };
type Props = {
  endpoint: string; titulo: string; subtitulo: string; filename: string; filtros?: Filtro[];
  indicadores: { etiqueta: string; clave: string; formato?: 'porcentaje' | 'horas'; subclave?: string; subformato?: 'porcentaje' | 'horas'; subetiqueta?: string }[];
  series: Serie[];
};

export const ReporteGestion: React.FC<Props> = ({ endpoint, titulo, subtitulo, filename, filtros = [], indicadores, series }) => {
  const { showToast } = useVeterinaria();
  const [datos, setDatos] = useState<any>(null);
  const [desde, setDesde] = useState('');
  const [hasta, setHasta] = useState('');
  const [seleccion, setSeleccion] = useState<Record<string, string>>(() => Object.fromEntries(filtros.map(f => [f.parametro, f.inicial])));
  const [cargando, setCargando] = useState(false);
  const [modal, setModal] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const params = useMemo(() => {
    const query = new URLSearchParams();
    if (desde) query.set('fecha_desde', desde);
    if (hasta) query.set('fecha_hasta', hasta);
    for (const filtro of filtros) {
      const valor = seleccion[filtro.parametro];
      if (valor && valor !== filtro.inicial) query.set(filtro.parametro, valor);
    }
    return query;
  }, [desde, hasta, seleccion, filtros]);
  const cargar = useCallback(async () => {
    setCargando(true);
    try {
      const response = await fetch(`${endpoint}?${params.toString()}`);
      if (!response.ok) throw new Error('No se pudo cargar el reporte.');
      setDatos(await response.json());
    } catch (error) {
      showToast({ type: 'error', title: 'Error al cargar el reporte', description: error instanceof Error ? error.message : 'Error de conexión.' });
    } finally { setCargando(false); }
  }, [endpoint, params, showToast]);
  useEffect(() => { void cargar(); }, [cargar]);

  const descargar = async (formato: 'excel' | 'pdf') => {
    try {
      const response = await fetch(`${endpoint}/${formato}?${params.toString()}`);
      if (!response.ok) throw new Error('No se pudo generar el archivo.');
      const url = URL.createObjectURL(await response.blob());
      const link = document.createElement('a'); link.href = url; link.download = `${filename}.${formato === 'excel' ? 'xlsx' : 'pdf'}`; link.click(); URL.revokeObjectURL(url);
    } catch (error) { showToast({ type: 'error', title: 'Error de exportación', description: error instanceof Error ? error.message : 'No se pudo descargar.' }); }
  };
  const enviar = async (destinatario: string, asunto: string, incluirPdf: boolean, incluirExcel: boolean) => {
    setEnviando(true);
    try {
      const payload = Object.fromEntries(params.entries());
      const response = await fetch(`${endpoint}/enviar-email`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ...payload, destinatario, asunto: asunto || undefined, incluir_pdf: incluirPdf, incluir_excel: incluirExcel }) });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || 'No se pudo enviar el correo.');
      showToast({ type: 'success', title: 'Reporte enviado', description: `Se envió el reporte a ${destinatario}.` }); setModal(false);
    } catch (error) { showToast({ type: 'error', title: 'Error de envío', description: error instanceof Error ? error.message : 'No se pudo enviar el correo.' }); }
    finally { setEnviando(false); }
  };
  const formatos = (clave: string, formato?: string) => {
    const valor = datos?.kpis?.[clave];
    if (valor === null || valor === undefined) return 'Sin información suficiente';
    if (formato === 'porcentaje') return `${valor}%`;
    if (formato === 'horas') return `${valor} h`;
    return String(valor);
  };
  return <div className="space-y-5">
    <ReporteHeaderBanner titulo={titulo} subtitulo={subtitulo} />
    <div className="bg-white border border-[#E7E2DA] rounded-xl p-4 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <span className="text-xs font-bold text-neutral-800">Período y filtros</span>
        <ReporteAccionesBar onDescargarExcel={() => void descargar('excel')} onDescargarPdf={() => void descargar('pdf')} onAbrirModalEmail={() => setModal(true)} onRecargar={() => void cargar()} cargando={cargando} />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <label className="text-xs text-neutral-600">Desde<input aria-label="Fecha desde" type="date" value={desde} onChange={e => setDesde(e.target.value)} className="mt-1 w-full p-2 border border-[#E7E2DA] rounded-lg" /></label>
        <label className="text-xs text-neutral-600">Hasta<input aria-label="Fecha hasta" type="date" value={hasta} onChange={e => setHasta(e.target.value)} className="mt-1 w-full p-2 border border-[#E7E2DA] rounded-lg" /></label>
        {filtros.map(filtro => <label key={filtro.parametro} className="text-xs text-neutral-600">{filtro.etiqueta}<select value={seleccion[filtro.parametro]} onChange={e => setSeleccion(prev => ({ ...prev, [filtro.parametro]: e.target.value }))} className="mt-1 w-full p-2 border border-[#E7E2DA] rounded-lg bg-white"><option value={filtro.inicial}>{filtro.inicial}</option>{(datos?.filtros_disponibles?.[filtro.opciones] || []).filter((x: string) => x !== filtro.inicial).map((opcion: string) => <option key={opcion} value={opcion}>{opcion}</option>)}</select></label>)}
      </div>
    </div>
    {datos && <>
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
        {indicadores.map((indicador, index) => <KpiCard key={indicador.clave} titulo={indicador.etiqueta} valor={formatos(indicador.clave, indicador.formato)} icono={[FlaskConical, CheckCircle2, Clock3, Microscope][index % 4]} subtexto={indicador.subclave ? `${indicador.subetiqueta || 'Porcentaje'}: ${formatos(indicador.subclave, indicador.subformato)}` : datos.kpis[indicador.clave] == null ? 'No hay registros suficientes para calcular este indicador.' : undefined} />)}
      </div>
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {series.map(serie => {
          const filas: any[] = datos[serie.clave] || [];
          const maximo = Math.max(1, ...filas.map(f => Number(f[serie.valor]) || 0));
          return <section key={serie.clave} className="bg-white border border-[#E7E2DA] rounded-xl p-4">
            <h3 className="font-bold text-sm text-[#2D5864] flex items-center gap-2"><BarChart3 className="w-4 h-4" />{serie.titulo}</h3>
            {!filas.length ? <p className="text-xs text-neutral-500 py-8 text-center">No hay datos para mostrar en el período seleccionado.</p> : <div className="mt-4 space-y-3">{filas.slice(0, 12).map((fila, index) => <div key={`${fila[serie.categoria]}-${index}`} className="grid grid-cols-[minmax(90px,1fr)_3fr_auto] gap-3 items-center text-xs"><span className="truncate text-neutral-700">{fila[serie.categoria]}</span><div className="h-3 rounded-full bg-[#F0EEE9] overflow-hidden"><div className="h-full rounded-full bg-[#5F8E9C]" style={{ width: `${Math.max(2, (Number(fila[serie.valor]) || 0) / maximo * 100)}%` }} /></div><strong className="text-neutral-800">{fila[serie.valor] ?? '—'}</strong></div>)}</div>}
          </section>;
        })}
      </div>
    </>}
    <ModalEnvioCorreo isOpen={modal} onClose={() => setModal(false)} onEnviar={enviar} enviando={enviando} tituloReporte={titulo} />
  </div>;
};
