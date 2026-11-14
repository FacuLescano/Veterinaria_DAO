import React from 'react';

interface ReporteHeaderBannerProps {
  titulo: string;
  subtitulo: string;
  badgeTexto?: string;
  sedeTexto?: string;
  logoSrc?: string;
}

export const ReporteHeaderBanner: React.FC<ReporteHeaderBannerProps> = ({
  titulo,
  subtitulo,
  badgeTexto,
  sedeTexto,
  logoSrc = '/assets/aistudio/Gemini_Generated_Image_o95dgio95dgio95d-removebg-preview_cbe90b76.png',
}) => {
  return (
    <div className="bg-white border border-[#E7E2DA] rounded-xl p-4 shadow-xs flex items-center justify-between">
      <div className="flex items-center gap-3.5">
        <img
          src={logoSrc}
          alt="Logo Patitas & Co."
          className="w-11 h-11 object-contain"
        />
        <div>
          <h3 className="font-bold text-sm text-[#2D5864] leading-tight">
            {titulo}
          </h3>
          <p className="text-xs text-neutral-500 mt-0.5">
            {subtitulo}
          </p>
        </div>
      </div>
      {(sedeTexto || badgeTexto) && (
        <div className="text-right hidden sm:block">
          {sedeTexto && <span className="text-[10px] font-mono text-neutral-400 block">{sedeTexto}</span>}
          {badgeTexto && (
            <span className="text-[10px] text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full font-semibold border border-emerald-200">
              {badgeTexto}
            </span>
          )}
        </div>
      )}
    </div>
  );
};

