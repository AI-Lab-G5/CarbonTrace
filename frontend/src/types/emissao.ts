export interface FatoresEmissao {
  energia: number;     // kg CO2e por kWh (grid BR, referência)
  combustivel: number; // kg CO2e por litro (diesel)
  residuos: number;    // kg CO2e por kg de resíduo em aterro
}

export interface ItemBreakdown {
  nome: string;
  emissao: number;
  percentual: number;
}

export interface ResultadoCalculo {
  total: number;
  itens: ItemBreakdown[];
}

