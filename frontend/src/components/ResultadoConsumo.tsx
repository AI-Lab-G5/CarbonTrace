import { useJornadasContext } from '@/hooks/useJornadasContext';
import { formatDecimal } from '@/utils/decimal';
import { periodName, sourceName } from '@/utils/presentation';
import { FormFeedback } from '@/components/FormFeedback';
import { useEffect, useRef } from 'react';

export function ResultadoConsumo() {
  const j = useJornadasContext();
  const result = j.result;
  const panel = useRef<HTMLElement>(null);
  useEffect(() => { if (result) panel.current?.focus(); }, [result]);
  if (!result) return null;
  return <section ref={panel} tabIndex={-1} key={result.id} className="card result-card route-enter" aria-label="Resultado salvo">
    <h2>Resultado salvo</h2>
    <p className="result-context">{j.units.find(u => u.id === result.unidade_id)?.nome || result.unidade_id} / {periodName(result.competencia)} / {sourceName(result.fonte_id)}</p>
    <p className="emission-total">{formatDecimal(result.emissao_kg_co2e, 3)} <span>kgCO₂e</span></p>
    <p className="nota">CO₂e reúne o impacto dos gases de efeito estufa em uma mesma medida: dióxido de carbono equivalente.</p>
    <p className="nota">Escopo {result.escopo}{result.escopo === '2' ? ' · Emissões indiretas associadas à energia adquirida.' : result.escopo === '1' ? ' · Emissões diretas das operações da empresa.' : ''}</p>
    <dl className="calculation-trail">
      <div><dt>01 · Quantidade original</dt><dd>{formatDecimal(result.quantidade_informada)} {result.unidade_informada}</dd></div>
      <div><dt>02 · Conversão registrada</dt><dd>{formatDecimal(result.quantidade_convertida)} {result.unidade_base}</dd></div>
      <div><dt>03 · Fator aplicado</dt><dd>{formatDecimal(result.fator_valor)} kgCO₂e/{result.unidade_base}</dd></div>
    </dl>
    {j.factorLoading && <p role="status" className="nota">Carregando referência do fator…</p>}
    <FormFeedback message={j.factorError} retry={j.retryFactor} retryLabel="Carregar referência novamente" disabled={j.factorLoading}/>
    <details className="factor-details"><summary>Rastreabilidade do cálculo · {result.fator_versao}</summary><dl>
      <dt>Fator / versão</dt><dd>{formatDecimal(result.fator_valor)} kgCO₂e/{result.unidade_base} · {result.fator_versao}</dd>
      <dt>Status e referência</dt><dd>{j.factor ? `${j.factor.status} — ${j.factor.fonte_referencia}` : j.factorLoading ? 'Carregando referência…' : 'Metadados do fator indisponíveis.'}</dd>
    </dl><p className="nota">Autoria e datas ainda não são fornecidas pela API.</p></details>
    <p className="nota result-disclaimer">Estimativa limitada às fontes previstas. Fatores preliminares não representam inventário homologado.</p>
    <button className="btn ghost" disabled={j.busy} onClick={() => void j.checkOriginal()}>{j.operation === 'check' ? 'Conferindo…' : 'Conferir cálculo original'}</button>
  </section>;
}
