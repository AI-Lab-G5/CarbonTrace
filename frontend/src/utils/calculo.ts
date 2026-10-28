import type { FatoresEmissao, ResultadoCalculo } from '@/types/emissao';

export const FATORES_PADRAO: FatoresEmissao = {
  energia: 0.0385,     // kg CO2e por kWh (grid BR, referência)
  combustivel: 2.392,  // kg CO2e por litro (diesel)
  residuos: 0.45,      // kg CO2e por kg de resíduo em aterro
};

export function calcularEmissoes(
  kwhInput: string | number,
  combustivelInput: string | number,
  residuosInput: string | number,
  fatores: FatoresEmissao = FATORES_PADRAO
): ResultadoCalculo {
  const kwhNum = typeof kwhInput === 'number' ? kwhInput : parseFloat(kwhInput);
  const combNum = typeof combustivelInput === 'number' ? combustivelInput : parseFloat(combustivelInput);
  const resNum = typeof residuosInput === 'number' ? residuosInput : parseFloat(residuosInput);

  const kwh = Math.max(0, isNaN(kwhNum) ? 0 : kwhNum);
  const comb = Math.max(0, isNaN(combNum) ? 0 : combNum);
  const res = Math.max(0, isNaN(resNum) ? 0 : resNum);

  const itens = [
    { nome: 'Energia elétrica', emissao: kwh * fatores.energia },
    { nome: 'Frota (combustível)', emissao: comb * fatores.combustivel },
    { nome: 'Resíduos (aterro)', emissao: res * fatores.residuos },
  ];

  const total = itens.reduce((soma, item) => soma + item.emissao, 0);

  return {
    total,
    itens: itens.map((item) => ({
      nome: item.nome,
      emissao: item.emissao,
      percentual: total > 0 ? (item.emissao / total) * 100 : 0,
    })),
  };
}
