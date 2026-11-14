import React from 'react';
import { LucideIcon } from 'lucide-react';

interface KpiCardProps {
  titulo: string;
  valor: string | number;
  unidad?: string;
  subtexto?: string;
  icono: LucideIcon;
  colorIcono?: string;
  colorValor?: string;
}

export const KpiCard: React.FC<KpiCardProps> = ({
  titulo,
  valor,
  unidad,
  subtexto,
  icono: Icono,
  colorIcono = 'text-[#2D5864]',
  colorValor = 'text-[#2D5864]',
}) => {
  return (
    <div className="bg-white border border-[#E7E2DA] rounded-xl p-3.5 shadow-xs">
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-semibold text-neutral-500 uppercase tracking-wide">
          {titulo}
        </span>
        <Icono className={`w-4 h-4 ${colorIcono}`} />
      </div>
      <div className="mt-2 flex items-baseline gap-1.5">
        <span className={`text-2xl font-bold ${colorValor}`}>
          {valor}
        </span>
        {unidad && <span className="text-[10px] text-neutral-400 font-medium">{unidad}</span>}
      </div>
      {subtexto && <p className="text-[10px] text-neutral-500 mt-1">{subtexto}</p>}
    </div>
  );
};

