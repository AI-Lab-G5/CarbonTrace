import { Link } from 'react-router';
import { useJornadasContext } from '@/hooks/useJornadasContext';
import { LoadingCards } from '@/components/LoadingCards';
import { formatDecimal } from '@/utils/decimal';
import { ResultadoConsumo } from '@/components/ResultadoConsumo';

const sourceNames: Record<string, string> = { eletricidade: 'Eletricidade', diesel: 'Diesel', gasolina: 'Gasolina', glp: 'GLP' };

export function ConsumosPage() {
  const j = useJornadasContext();
  const contextReady = Boolean(j.unit && j.period);
  return <>
    <ol className="collection-steps" aria-label="Etapas do registro">
      <li className={contextReady ? 'complete' : 'current'} aria-current={!contextReady ? 'step' : undefined}><span aria-hidden="true">{contextReady ? '✓' : '1'}</span>Loja e mês</li>
      <li className={contextReady ? 'current' : ''} aria-current={contextReady ? 'step' : undefined}><span aria-hidden="true">2</span>Dados do consumo</li>
      <li className={j.result ? 'complete' : ''}><span aria-hidden="true">{j.result ? '✓' : '3'}</span>Resultado salvo</li>
    </ol>
    <section className="card" aria-labelledby="consumption-form-heading"><h2 id="consumption-form-heading">Registrar consumo</h2>
      <p className="section-description">Escolha a loja e a competência. As fontes disponíveis seguem o catálogo daquele mês.</p>
      {!j.unitsLoading && !j.units.length && <p className="empty-hint">Cadastre uma unidade para registrar consumos. <Link to="/unidades">Ir para Unidades →</Link></p>}
      <form onSubmit={event => { event.preventDefault(); void j.saveConsumption(); }}>
        <fieldset disabled={j.busy || j.unitsLoading} className="journey-fields">
          <div className="grid context-fields">
            <label>Loja<select aria-label="Loja" required value={j.unit} onChange={e => j.selectUnit(e.target.value)}><option value="">Selecione</option>{j.units.map(u => <option key={u.id} value={u.id}>{u.nome}</option>)}</select></label>
            <label>Competência<input type="month" required value={j.period} onChange={e => j.selectPeriod(e.target.value)}/></label>
          </div>
          {contextReady ? <div className="consumption-fields route-enter"><div className="grid">
            <label>Fonte<select aria-label="Fonte" required disabled={j.catalogLoading || Boolean(j.catalogError)} value={j.source} onChange={e => j.selectSource(e.target.value)}><option value="">Selecione</option>{j.sources.map(f => <option key={f.fonte_id} value={f.fonte_id}>{f.nome}</option>)}</select></label>
            <label>Quantidade<input name="quantidade" inputMode="decimal" required value={j.quantity} onChange={e => j.setQuantity(e.target.value)} aria-describedby={j.error ? 'decimal-help journey-error' : 'decimal-help'}/></label>
            <label>Medida<select aria-label="Medida" name="medida" required value={j.measure} onChange={e => j.setMeasure(e.target.value)}><option value="">Selecione</option>{j.sources.find(f => f.fonte_id === j.source)?.unidades_aceitas.map(m => <option key={m}>{m}</option>)}</select></label>
          </div><p id="decimal-help" className="nota">Informe decimal sem separador de milhar. Zero explícito é válido.</p></div> : <p className="empty-hint">Selecione uma loja e um mês para informar o consumo.</p>}
          {j.catalogLoading && <p role="status"><span className="spinner small-spinner" aria-hidden="true"/> Carregando fontes…</p>}
          {j.catalogError && <p role="alert">⚠ {j.catalogError} <button type="button" className="btn ghost" onClick={j.retryCatalog}>Tentar carregar fontes novamente</button></p>}
          {j.period && !j.catalogLoading && !j.catalogError && !j.sources.length && <p>Nenhuma fonte disponível para esta competência.</p>}
          <div className="form-footer"><span className="nota">Eletricidade · Diesel · Gasolina · GLP</span><button className="btn" disabled={j.busy || !contextReady || j.catalogLoading || Boolean(j.catalogError) || !j.sources.length}>{j.operation === 'consumption' ? 'Salvando consumo…' : 'Salvar consumo'}</button></div>
        </fieldset>
      </form>
    </section>
    {j.result && <ResultadoConsumo/>}
    <section className="card" aria-labelledby="saved-heading"><div className="section-heading"><h2 id="saved-heading">Consumos salvos</h2><span className="count-badge">{j.records.length} carregados</span></div>
      <p className="section-description">Os filtros de loja e competência acima também filtram esta consulta.</p>
      {j.loading ? <LoadingCards label="Carregando registros…"/> : !j.records.length ? <div className="empty-state compact"><h3>Seu histórico começa aqui</h3><p>Nenhum consumo encontrado. Os registros salvos aparecerão nesta lista.</p></div> : <ul className="record-list">
        {j.records.map(c => <li key={c.id} className={j.savedId === c.id ? 'just-created' : ''}><button className="record-button" disabled={j.busy} onClick={() => void j.consultRecord(c.id)}>
          <span><strong>{sourceNames[c.fonte_id] || c.fonte_id}</strong><small>{c.competencia} · {j.units.find(u => u.id === c.unidade_id)?.nome || c.unidade_id}</small></span>
          <span className="record-value">{formatDecimal(c.emissao_kg_co2e, 3)} <small>kg CO₂e</small><span className="record-action">{j.operation === `record-${c.id}` ? 'Consultando…' : 'Ver resultado →'}</span></span>
        </button></li>)}
      </ul>}
      {j.recordCursor && <button className="btn ghost" disabled={j.busy} onClick={() => void j.moreRecords()}>{j.operation === 'more-records' ? 'Carregando…' : 'Mais consumos'}</button>}
    </section>
  </>;
}
