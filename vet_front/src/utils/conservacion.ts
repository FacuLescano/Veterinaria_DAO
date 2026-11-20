const patronTemperatura = /^(?:refrigerad[ao] |refrigerar a |congelad[ao] |temperatura ambiente )?\(? *(-?[0-9]+(?:[.,][0-9]+)?)(?: *(?:° *c?)? *(?:a|y|[-–—]) *(-?[0-9]+(?:[.,][0-9]+)?))? *° *c *\)?$/;

const normalizarCondicion = (condicion: string) =>
  condicion.trim().toLowerCase().replaceAll('º', '°').replaceAll('−', '-').replace(/\s+/g, ' ');

export function rangoConservacion(condicion: string): [number | null, number] | null {
  const texto = normalizarCondicion(condicion);
  if (texto === 'temperatura ambiente' || texto === 'estándar a temperatura ambiente') return [15, 25];
  if (texto === 'congelada (-20°c o menos)' || texto === 'congelada (menos de -20°c)') return [null, -20];
  const coincidencia = texto.match(patronTemperatura);
  if (!coincidencia) return null;
  const [, minima, maxima] = coincidencia;
  const desde = Number(minima.replace(',', '.'));
  const hasta = Number((maxima ?? minima).replace(',', '.'));
  if (maxima === undefined && desde === -20 && /^(congelada|congelado) /.test(texto)) return [null, -20];
  return Number.isFinite(desde) && Number.isFinite(hasta) && desde <= hasta ? [desde, hasta] : null;
}

export function claveConservacion(condicion: string): string {
  const rango = rangoConservacion(condicion);
  return JSON.stringify(rango ?? normalizarCondicion(condicion));
}
