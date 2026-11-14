import React from 'react';
import { LucideIcon } from 'lucide-react';

interface ReportePlaceholderProps {
  titulo: string;
  descripcion: string;
  icono: LucideIcon;
  badge: string;
  colorScheme?: 'blue' | 'emerald' | 'amber';
}

export const ReportePlaceholder: React.FC<ReportePlaceholderProps> = ({
  titulo,
  descripcion,
  icono: Icon,
  badge,
  colorScheme = 'blue',
}) => {
  const colorStyles = {
    blue: {
      bgIcon: 'bg-blue-50 text-blue-700',
      badge: 'bg-blue-50 text-blue-800 border-blue-200',
    },
    emerald: {
      bgIcon: 'bg-emerald-50 text-emerald-700',
      badge: 'bg-emerald-50 text-emerald-800 border-emerald-200',
    },
    amber: {
      bgIcon: 'bg-amber-50 text-amber-700',
      badge: 'bg-amber-50 text-amber-800 border-amber-200',
    },
  }[colorScheme];

  return (
    <div className="p-8 bg-white border border-[#E7E2DA] rounded-xl shadow-xs text-center space-y-4">
      <div className={`w-12 h-12 rounded-full flex items-center justify-center mx-auto ${colorStyles.bgIcon}`}>
        <Icon className="w-6 h-6" />
      </div>
      <div className="max-w-md mx-auto">
        <h3 className="font-bold text-base text-neutral-900">{titulo}</h3>
        <p className="text-xs text-neutral-500 mt-1">{descripcion}</p>
      </div>
      <span className={`inline-block px-3 py-1 rounded-full text-xs font-semibold border ${colorStyles.badge}`}>
        {badge}
      </span>
    </div>
  );
};

