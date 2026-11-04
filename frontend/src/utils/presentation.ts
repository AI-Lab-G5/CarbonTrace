const sources: Record<string, string> = { eletricidade: 'Eletricidade', diesel: 'Diesel', gasolina: 'Gasolina', glp: 'GLP' };
export const sourceName = (id: string) => sources[id] || id;
export function periodName(value: string) {
  if (!/^\d{4}-(0[1-9]|1[0-2])$/.test(value)) return value;
  // Evita o tratamento especial de anos 00–99 do construtor Date.
  const date = new Date(0);
  date.setUTCFullYear(Number(value.slice(0, 4)), Number(value.slice(5, 7)) - 1, 1);
  return new Intl.DateTimeFormat('pt-BR', { month: 'long', year: 'numeric', timeZone: 'UTC' }).format(date);
}
