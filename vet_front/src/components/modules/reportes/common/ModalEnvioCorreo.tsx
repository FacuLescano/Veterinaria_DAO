import React, { useState } from 'react';
import { Mail, X, Send, Loader2 } from 'lucide-react';

interface ModalEnvioCorreoProps {
  isOpen: boolean;
  onClose: () => void;
  onEnviar: (destinatario: string, asunto: string, incluirPdf: boolean, incluirExcel: boolean) => Promise<void>;
  enviando: boolean;
  tituloReporte: string;
  placeholderAsunto?: string;
  etiquetaPdf?: string;
  etiquetaExcel?: string;
}

export const ModalEnvioCorreo: React.FC<ModalEnvioCorreoProps> = ({
  isOpen,
  onClose,
  onEnviar,
  enviando,
  tituloReporte,
  placeholderAsunto,
  etiquetaPdf = 'Informe Oficial en PDF (.pdf)',
  etiquetaExcel = 'Libro de datos detallado en Excel (.xlsx)',
}) => {
  const [emailDestinatario, setEmailDestinatario] = useState('');
  const [asuntoEmail, setAsuntoEmail] = useState('');
  const [adjuntarPdf, setAdjuntarPdf] = useState(true);
  const [adjuntarExcel, setAdjuntarExcel] = useState(true);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!emailDestinatario.trim()) return;
    await onEnviar(emailDestinatario.trim(), asuntoEmail.trim(), adjuntarPdf, adjuntarExcel);
  };

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-xs z-50 flex items-center justify-center p-4">
      <div className="bg-white border border-[#E7E2DA] rounded-2xl max-w-lg w-full shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        <div className="p-4 border-b border-[#E7E2DA] flex items-center justify-between bg-[#FAF8F5]">
          <div className="flex items-center gap-2">
            <Mail className="w-4 h-4 text-[#2D5864]" />
            <h4 className="font-bold text-sm text-[#2D5864]">
              Enviar Reporte por Correo Electrónico
            </h4>
          </div>
          <button
            onClick={onClose}
            className="text-neutral-400 hover:text-neutral-700 p-1 rounded-lg transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4 text-xs">
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
              placeholder={placeholderAsunto || `${tituloReporte} — Patitas & Co.`}
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
              <span className="text-neutral-700 font-medium">{etiquetaPdf}</span>
            </label>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={adjuntarExcel}
                onChange={e => setAdjuntarExcel(e.target.checked)}
                className="w-4 h-4 rounded text-[#2D5864] border-neutral-300 focus:ring-[#2D5864]"
              />
              <span className="text-neutral-700 font-medium">{etiquetaExcel}</span>
            </label>
          </div>

          <div className="flex items-center justify-end gap-2 pt-2 border-t border-neutral-100">
            <button
              type="button"
              onClick={onClose}
              disabled={enviando}
              className="px-3.5 py-2 text-neutral-600 hover:bg-neutral-100 rounded-lg transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={enviando || !emailDestinatario.trim()}
              className="px-4 py-2 font-semibold text-white bg-[#2D5864] hover:bg-[#23454f] rounded-lg transition-colors flex items-center gap-1.5 disabled:opacity-50 shadow-xs"
            >
              {enviando ? (
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
  );
};

