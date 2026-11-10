import React from 'react';
import { useVeterinaria } from '../../context/VeterinariaContext';
import { CheckCircle2, AlertTriangle, AlertCircle, Info, X } from 'lucide-react';

export const Toast: React.FC = () => {
  const { toast, clearToast } = useVeterinaria();

  if (!toast) return null;

  type ToastType = 'success' | 'warning' | 'error' | 'info';

  const icons: Record<ToastType, React.ReactNode> = {
    success: <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />,
    warning: <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0" />,
    error: <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />,
    info: <Info className="w-5 h-5 text-[#2D5864] shrink-0" />
  };

  const borderStyles: Record<ToastType, string> = {
    success: 'border-emerald-200 bg-emerald-50/95 text-emerald-900',
    warning: 'border-amber-200 bg-amber-50/95 text-amber-900',
    error: 'border-rose-200 bg-rose-50/95 text-rose-900',
    info: 'border-[#2D5864]/20 bg-[#FAF8F5]/95 text-[#2D5864]'
  };

  return (
    <div className="fixed bottom-5 right-5 z-50 max-w-sm w-full animate-in fade-in slide-in-from-bottom-3 duration-200 shadow-lg">
      <div className={`p-4 rounded-xl border backdrop-blur-sm flex items-start gap-3 ${borderStyles[toast.type]}`}>
        {icons[toast.type]}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold">{toast.title}</p>
          {toast.description && (
            <p className="text-xs mt-0.5 opacity-90 leading-relaxed">{toast.description}</p>
          )}
        </div>
        <button
          onClick={clearToast}
          aria-label="Cerrar notificación"
          className="text-neutral-400 hover:text-neutral-700 p-1 rounded-md transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
