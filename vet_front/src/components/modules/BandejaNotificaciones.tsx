import React, { useCallback, useEffect, useState } from 'react';
import { Bell, Check, ChevronDown, ChevronUp, RefreshCw } from 'lucide-react';

interface Notificacion {
  id: number;
  muestra_id: number;
  estado_nuevo: string;
  mensaje: string;
  motivo?: string | null;
  ocurrido_en: string;
  creada_en: string;
  leida_en?: string | null;
}

export const BandejaNotificaciones: React.FC = () => {
  const [notificaciones, setNotificaciones] = useState<Notificacion[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [detalleId, setDetalleId] = useState<number | null>(null);

  const cargar = useCallback(async () => {
    setCargando(true);
    try {
      const response = await fetch('/api/v1/notificaciones');
      if (!response.ok) throw new Error(`No se pudieron cargar las notificaciones (${response.status})`);
      setNotificaciones(await response.json());
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudieron cargar las notificaciones');
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => { void cargar(); }, [cargar]);

  const marcarLeida = async (id: number) => {
    try {
      const response = await fetch(`/api/v1/notificaciones/${id}/leida`, { method: 'PATCH' });
      if (!response.ok) throw new Error(`No se pudo actualizar la notificación (${response.status})`);
      const actualizada = await response.json();
      setNotificaciones(actuales => actuales.map(n => n.id === id ? actualizada : n));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo actualizar la notificación');
    }
  };

  const formatoFecha = (valor: string) => new Intl.DateTimeFormat('es-AR', {
    dateStyle: 'medium', timeStyle: 'short'
  }).format(new Date(/[zZ]|[+-]\d{2}:?\d{2}$/.test(valor) ? valor : `${valor}Z`));

  return (
    <section className="space-y-5" aria-labelledby="notificaciones-titulo">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 id="notificaciones-titulo" className="text-xl font-bold text-[#2D5864]">Notificaciones</h2>
          <p className="mt-1 text-sm text-neutral-500">Avisos generados al verificar precintos durante la recepción.</p>
        </div>
        <button onClick={() => void cargar()} className="inline-flex items-center gap-2 rounded-lg border border-[#E7E2DA] bg-white px-3 py-2 text-sm text-[#2D5864] hover:bg-[#FAF6EF]" disabled={cargando}>
          <RefreshCw className={`h-4 w-4 ${cargando ? 'animate-spin' : ''}`} /> Actualizar
        </button>
      </div>

      {error && <p role="alert" className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}
      {cargando && <p className="py-8 text-center text-sm text-neutral-500">Cargando notificaciones…</p>}
      {!cargando && !error && notificaciones.length === 0 && (
        <div className="rounded-2xl border border-dashed border-[#D8D0C4] bg-white p-10 text-center text-neutral-500">
          <Bell className="mx-auto mb-3 h-8 w-8 text-[#5F8E9C]" />
          <p className="font-medium text-neutral-700">Todavía no hay notificaciones</p>
          <p className="mt-1 text-sm">Los avisos de recepción aparecerán aquí.</p>
        </div>
      )}

      <div className="space-y-3">
        {notificaciones.map(n => {
          const aceptada = n.estado_nuevo === 'aceptada';
          const rechazada = n.estado_nuevo === 'rechazada';
          const claseEstado = aceptada ? 'bg-emerald-100 text-emerald-800' : rechazada ? 'bg-rose-100 text-rose-800' : 'bg-neutral-100 text-neutral-700';
          const abierta = detalleId === n.id;
          return (
            <article key={n.id} className={`rounded-xl border p-4 shadow-sm ${n.leida_en ? 'border-[#E7E2DA] bg-white' : 'border-[#B8D0D4] bg-[#F1F7F7]'}`}>
              <div className="flex items-start gap-3">
                <span className={`mt-0.5 rounded-full px-2.5 py-1 text-xs font-semibold ${claseEstado}`}>
                  {aceptada ? 'Muestra recibida' : rechazada ? 'Muestra rechazada' : 'Verificación de precinto'}
                </span>
                {!n.leida_en && <span className="mt-2 h-2 w-2 rounded-full bg-sky-600" title="No leída" />}
                <time className="ml-auto shrink-0 pt-1 text-xs text-neutral-500" dateTime={n.ocurrido_en}>{formatoFecha(n.ocurrido_en)}</time>
              </div>
              <p className="mt-3 text-sm font-medium text-neutral-800">{n.mensaje}</p>
              {abierta && <div className="mt-3 rounded-lg bg-white/80 p-3 text-sm text-neutral-600">
                <p><strong>Muestra:</strong> {n.muestra_id}</p>
                {n.motivo && <p className="mt-1"><strong>Condición:</strong> {n.motivo.replace(/^Precinto:\s*/i, '')}</p>}
                <p className="mt-1"><strong>Fecha del evento:</strong> {formatoFecha(n.ocurrido_en)}</p>
                <p className="mt-1"><strong>Notificada:</strong> {formatoFecha(n.creada_en)}</p>
              </div>}
              <div className="mt-3 flex items-center gap-3">
                <button onClick={() => setDetalleId(abierta ? null : n.id)} className="inline-flex items-center gap-1 text-xs font-semibold text-[#2D5864] hover:underline">
                  {abierta ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
                  {abierta ? 'Ocultar detalle' : 'Ver detalle'}
                </button>
                {!n.leida_en && <button onClick={() => void marcarLeida(n.id)} className="inline-flex items-center gap-1 text-xs font-semibold text-[#2D5864] hover:underline">
                  <Check className="h-3.5 w-3.5" /> Marcar como leída
                </button>}
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
};
