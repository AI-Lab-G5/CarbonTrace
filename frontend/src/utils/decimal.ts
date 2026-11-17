export function decimalInput(value: string): string {
  const text = value.trim();
  if (!/^\d+(?:[.,]\d+)?$/.test(text)) throw new Error('Informe uma quantidade decimal não negativa, sem separador de milhar. Zero é válido.');
  return text.replace(',', '.');
}
export function formatDecimal(value: string, places?: number): string {
  if (!/^\d+(?:\.\d+)?$/.test(value)) return value;
  let [whole, fraction = ''] = value.split('.');
  if (places !== undefined) {
    const kept = fraction.padEnd(places, '0').slice(0, places);
    const tail = fraction.slice(places);
    let scaled = BigInt(whole + kept);
    if (tail && (tail[0] > '5' || (tail[0] === '5' && (/[1-9]/.test(tail.slice(1)) || scaled % 2n === 1n)))) scaled += 1n;
    const digits = scaled.toString().padStart(places + 1, '0');
    whole = places ? digits.slice(0, -places) : digits;
    fraction = places ? digits.slice(-places) : '';
  }
  return whole.replace(/\B(?=(\d{3})+(?!\d))/g, '.') + (fraction ? `,${fraction}` : '');
}
