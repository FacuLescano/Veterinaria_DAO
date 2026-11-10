import React, { useEffect } from 'react';
import { X } from 'lucide-react';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl';
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  subtitle,
  children,
  maxWidth = 'lg'
}) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.body.style.overflow = 'unset';
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const widthClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-2xl',
    '2xl': 'max-w-4xl'
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overflow-y-auto print:p-0 print:m-0 print:static print:block">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-[#2D5864]/40 backdrop-blur-xs transition-opacity duration-200 print:hidden"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal Dialog */}
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        className={`relative w-full ${widthClasses[maxWidth]} bg-white rounded-2xl shadow-xl border border-[#B8AEA2]/30 overflow-hidden my-auto transition-all transform scale-100 max-h-[90vh] flex flex-col print:shadow-none print:border-none print:m-0 print:p-0 print:bg-transparent print:max-w-full print:max-h-none print:rounded-none`}
      >
        {/* Header */}
        <div className="px-6 py-4.5 border-b border-[#F2E8D8] flex items-start justify-between bg-[#FAF8F5]/80 shrink-0 print:hidden">
          <div>
            <h3 id="modal-title" className="text-base font-semibold text-[#2D5864] tracking-tight">
              {title}
            </h3>
            {subtitle && (
              <p className="text-xs text-[#8C8C91] mt-0.5">{subtitle}</p>
            )}
          </div>
          <button
            onClick={onClose}
            aria-label="Cerrar modal"
            className="text-[#8C8C91] hover:text-[#2D5864] p-1.5 rounded-lg hover:bg-neutral-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-5 overflow-y-auto flex-1 print:p-0 print:overflow-visible">
          {children}
        </div>
      </div>
    </div>
  );
};
