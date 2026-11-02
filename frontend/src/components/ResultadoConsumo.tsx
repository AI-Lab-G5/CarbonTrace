import { useJornadasContext } from '@/hooks/useJornadasContext';
import { formatDecimal } from '@/utils/decimal';

export function ResultadoConsumo() {
  const j = useJornadasContext();
  const result = j.result;
  if (!result) return null;
  return <section key={result.id} className="card result-card route-enter" aria-label="Resultado salvo">
    <p className="eyebrow">Consumo registrado</p><h2>Resultado salvo</h2>
    <p className="result-context">{j.units.find(u => u.id === result.unidade_id)?.nome || result.unidade_id} / {result.competencia} / {result.fonte_id}</p>
    <p className="emission-total">{formatDecimal(result.emissao_kg_co2e, 3)} <span>kgCO₂e</span></p><p className="nota">Escopo {result.escopo}</p>
    <dl className="calculation-trail">
      <div><dt>01 · Quantidade original</dt><dd>{formatDecimal(result.quantidade_informada)} {result.unidade_informada}</dd></div>
      <div><dt>02 · Conversão registrada</dt><dd>{formatDecimal(result.quantidade_convertida)} {result.unidade_base}</dd></div>
      <div><dt>03 · Fator aplicado</dt><dd>{formatDecimal(result.fator_valor)} kgCO₂e/{result.unidade_base}</dd></div>
    </dl>
    <details className="factor-details"><summary>Rastreabilidade do cálculo · {result.fator_versao}</summary><dl>
      <dt>Fator / versão</dt><dd>{formatDecimal(result.fator_valor)} kgCO₂e/{result.unidade_base} · {result.fator_versao}</dd>
      <dt>Status e referência</dt><dd>{j.factor ? `${j.factor.status} — ${j.factor.fonte_referencia}` : 'Metadados do fator indisponíveis.'}</dd>
    </dl><p className="nota">Autoria e datas ainda não são fornecidas pela API.</p></details>
    <p className="nota result-disclaimer">Estimativa limitada às fontes previstas. Fatores preliminares não representam inventário homologado.</p>
    <button className="btn ghost" disabled={j.busy} onClick={() => void j.checkOriginal()}>{j.operation === 'check' ? 'Conferindo…' : 'Conferir cálculo original'}</button>
  </section>;
}
