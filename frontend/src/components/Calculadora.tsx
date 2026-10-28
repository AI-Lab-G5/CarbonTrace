import { useState } from 'react';
import type { FatoresEmissao, ResultadoCalculo } from '../types/emissao';

const FATORES_PADRAO: FatoresEmissao = {
  energia: 0.0385,     // kg CO2e por kWh (grid BR, referência)
  combustivel: 2.392,  // kg CO2e por litro (diesel)
  residuos: 0.45,      // kg CO2e por kg de resíduo em aterro
};

const fmtInteiro = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 });
const fmtDecimal = new Intl.NumberFormat('pt-BR', {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

export function Calculadora() {
  const [energia, setEnergia] = useState<string>('12000');
  const [combustivel, setCombustivel] = useState<string>('800');
  const [residuos, setResiduos] = useState<string>('1500');
  const [resultado, setResultado] = useState<ResultadoCalculo | null>(null);

  const calcularEmissoes = (kwhStr: string, combStr: string, resStr: string): ResultadoCalculo => {
    const kwh = Math.max(0, parseFloat(kwhStr) || 0);
    const comb = Math.max(0, parseFloat(combStr) || 0);
    const res = Math.max(0, parseFloat(resStr) || 0);

    const itens = [
      { nome: 'Energia elétrica', emissao: kwh * FATORES_PADRAO.energia },
      { nome: 'Frota (combustível)', emissao: comb * FATORES_PADRAO.combustivel },
      { nome: 'Resíduos (aterro)', emissao: res * FATORES_PADRAO.residuos },
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
  };

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setResultado(calcularEmissoes(energia, combustivel, residuos));
  };

  const handleLimpar = () => {
    setEnergia('12000');
    setCombustivel('800');
    setResiduos('1500');
    setResultado(null);
  };

  const handleInputChange = (
    setter: React.Dispatch<React.SetStateAction<string>>,
    valor: string,
    tipo: 'energia' | 'combustivel' | 'residuos'
  ) => {
    setter(valor);
    if (resultado !== null) {
      const novosValores = {
        energia: tipo === 'energia' ? valor : energia,
        combustivel: tipo === 'combustivel' ? valor : combustivel,
        residuos: tipo === 'residuos' ? valor : residuos,
      };
      setResultado(
        calcularEmissoes(novosValores.energia, novosValores.combustivel, novosValores.residuos)
      );
    }
  };

  return (
    <section id="calculadora" className="wrap card" aria-labelledby="calc-heading">
      <h2 id="calc-heading">Calculadora de Emissões</h2>

      <form id="form-emissoes" onSubmit={handleSubmit} autoComplete="off">
        <div className="grid">
          <label htmlFor="input-energia">
            Energia elétrica (kWh/mês)
            <input
              id="input-energia"
              type="number"
              min="0"
              step="1"
              value={energia}
              onChange={(e) => handleInputChange(setEnergia, e.target.value, 'energia')}
            />
          </label>

          <label htmlFor="input-combustivel">
            Combustível da frota (litros/mês)
            <input
              id="input-combustivel"
              type="number"
              min="0"
              step="1"
              value={combustivel}
              onChange={(e) => handleInputChange(setCombustivel, e.target.value, 'combustivel')}
            />
          </label>

          <label htmlFor="input-residuos">
            Resíduos enviados a aterro (kg/mês)
            <input
              id="input-residuos"
              type="number"
              min="0"
              step="1"
              value={residuos}
              onChange={(e) => handleInputChange(setResiduos, e.target.value, 'residuos')}
            />
          </label>
        </div>

        <button type="submit" className="btn">
          Calcular emissões
        </button>
        <button type="button" className="btn ghost" onClick={handleLimpar}>
          Limpar
        </button>
      </form>

      {resultado !== null && (
        <div id="resultado" className="resultado" aria-live="polite">
          <div className="total">
            <span className="total-valor">{fmtInteiro.format(resultado.total)}</span>
            <small>kg CO₂e / mês</small>
          </div>

          <ul className="breakdown">
            {resultado.itens.map((item) => (
              <li key={item.nome}>
                <span>{item.nome}</span>
                <b>
                  {fmtInteiro.format(item.emissao)} kg ({fmtDecimal.format(item.percentual)}%)
                </b>
                <div className="bar" aria-hidden="true">
                  <i style={{ width: `${item.percentual.toFixed(1)}%` }} />
                </div>
              </li>
            ))}
          </ul>

          <p className="nota">
            Fatores usados: 0,0385 kg CO₂e/kWh · 2,392 kg CO₂e/L de diesel · 0,45 kg CO₂e/kg de resíduo.
            Valores de referência didáticos baseados em médias nacionais.
          </p>
        </div>
      )}
    </section>
  );
}

