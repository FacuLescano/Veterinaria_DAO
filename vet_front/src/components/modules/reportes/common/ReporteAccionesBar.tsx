import React from 'react';
import { FileSpreadsheet, FileText, Mail, RefreshCw } from 'lucide-react';

interface ReporteAccionesBarProps {
  onDescargarExcel: () => void;
  onDescargarPdf: () => void;
  onAbrirModalEmail: () => void;
  onRecargar: () => void;
  cargando?: boolean;
}

export const ReporteAccionesBar: React.FC<ReporteAccionesBarProps> = ({
  onDescargarExcel,
  onDescargarPdf,
  onAbrirModalEmail,
  onRecargar,
  cargando = false,
}) => {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <button
        onClick={onDescargarExcel}
        disabled={cargando}
        className="px-3 py-1.5 text-xs font-semibold text-emerald-800 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 rounded-lg transition-colors flex items-center gap-1.5 shadow-2xs disabled:opacity-50"
        title="Descargar libro Excel con tablas y formato"
      >
        <FileSpreadsheet className="w-3.5 h-3.5" />
        <span>Descargar Excel</span>
      </button>

      <button
        onClick={onDescargarPdf}
        disabled={cargando}
        className="px-3 py-1.5 text-xs font-semibold text-rose-800 bg-rose-50 hover:bg-rose-100 border border-rose-200 rounded-lg transition-colors flex items-center gap-1.5 shadow-2xs disabled:opacity-50"
        title="Descargar informe oficial en PDF"
      >
        <FileText className="w-3.5 h-3.5" />
        <span>Descargar PDF</span>
      </button>

      <button
        onClick={onAbrirModalEmail}
        disabled={cargando}
        className="px-3 py-1.5 text-xs font-semibold text-white bg-[#2D5864] hover:bg-[#23454f] rounded-lg transition-colors flex items-center gap-1.5 shadow-xs disabled:opacity-50"
      >
        <Mail className="w-3.5 h-3.5" />
        <span>Enviar por Correo</span>
      </button>

      <button
        onClick={onRecargar}
        disabled={cargando}
        className="p-1.5 text-neutral-500 hover:text-[#2D5864] hover:bg-neutral-100 rounded-lg transition-colors disabled:opacity-50"
        title="Actualizar datos"
      >
        <RefreshCw className={`w-4 h-4 ${cargando ? 'animate-spin text-[#2D5864]' : ''}`} />
      </button>
    </div>
  );
};

