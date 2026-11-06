import { Link } from 'react-router';
import { useJornadasContext } from '@/hooks/useJornadasContext';
import { LoadingCards } from '@/components/LoadingCards';
import { formatDecimal } from '@/utils/decimal';
import { ResultadoConsumo } from '@/components/ResultadoConsumo';
import { FormFeedback } from '@/components/FormFeedback';
import { periodName, sourceName } from '@/utils/presentation';

export function ConsumosPage() {
  const j = useJornadasContext();
  const contextReady = Boolean(j.unit && j.period);
  return <>
    <ol className="collection-steps" aria-label="Etapas do registro">
      <li className={contextReady || j.result ? 'complete' : 'current'} aria-current={!contextReady && !j.result ? 'step' : undefined}><span aria-hidden="true">{contextReady || j.result ? '✓' : '1'}</span>Loja e mês</li>
      <li className={j.result ? 'complete' : contextReady ? 'current' : ''} aria-current={contextReady && !j.result ? 'step' : undefined}><span aria-hidden="true">{j.result ? '✓' : '2'}</span>Dados do consumo</li>
      <li className={j.result ? 'complete current' : ''} aria-current={j.result ? 'step' : undefined}><span aria-hidden="true">{j.result ? '✓' : '3'}</span>Resultado salvo</li>
    </ol>
    <section className="card" aria-labelledby="consumption-form-heading"><h2 id="consumption-form-heading">Registrar consumo</h2>
      <p className="section-description">Escolha a loja e a competência. As fontes disponíveis seguem o catálogo daquele mês.</p>
      <FormFeedback message={j.unitsError} retry={j.retryUnits} retryLabel="Carregar lojas novamente"/>
      {!j.unitsLoading && !j.unitsError && !j.units.length && <p className="empty-hint">Cadastre uma unidade para registrar consumos. <Link to="/unidades">Ir para Unidades →</Link></p>}
      {j.draftRestored && <p role="status" className="draft-note">Rascunho recuperado nesta aba. Confira os dados antes de salvar.</p>}
      <form onSubmit={event => { event.preventDefault(); void j.saveConsumption(); }}>
        <fieldset disabled={j.busy || j.unitsLoading || Boolean(j.unitsError)} className="journey-fields">
          <div className="grid context-fields">
            <div className="form-field"><label htmlFor="consumption-unit">Loja</label><select id="consumption-unit" required value={j.unit} onChange={e => j.selectUnit(e.target.value)} aria-invalid={Boolean(j.invalidFields.unidade_id) || undefined} aria-describedby={j.invalidFields.unidade_id ? 'consumption-unit-error' : undefined}><option value="">Selecione</option>{j.units.map(u => <option key={u.id} value={u.id}>{u.nome}</option>)}</select>{j.invalidFields.unidade_id && <small id="consumption-unit-error" className="field-error">{j.invalidFields.unidade_id}</small>}</div>
            <div className="form-field"><label htmlFor="consumption-period">Competência</label><input id="consumption-period" type="month" required value={j.period} onChange={e => j.selectPeriod(e.target.value)} aria-invalid={Boolean(j.invalidFields.competencia) || undefined} aria-describedby={j.invalidFields.competencia ? 'period-help period-error' : 'period-help'}/>{j.invalidFields.competencia && <small id="period-error" className="field-error">{j.invalidFields.competencia}</small>}</div>
          </div>
          <p id="period-help" className="nota">Competência é o mês de referência da conta ou do abastecimento.</p>
          {contextReady ? <div className="consumption-fields route-enter"><div className="grid">
            <div className="form-field"><label htmlFor="consumption-source">Fonte</label><select id="consumption-source" required disabled={j.catalogLoading || Boolean(j.catalogError)} value={j.source} onChange={e => j.selectSource(e.target.value)} aria-invalid={Boolean(j.invalidFields.fonte_id) || undefined} aria-describedby={j.invalidFields.fonte_id ? 'source-error' : undefined}><option value="">Selecione</option>{j.sources.map(f => <option key={f.fonte_id} value={f.fonte_id}>{f.nome}</option>)}</select>{j.invalidFields.fonte_id && <small id="source-error" className="field-error">{j.invalidFields.fonte_id}</small>}</div>
            <div className="form-field"><label htmlFor="consumption-quantity">Quantidade</label><input id="consumption-quantity" name="quantidade" inputMode="decimal" required value={j.quantity} onChange={e => { j.setQuantity(e.target.value); j.clearFieldError('quantidade'); }} aria-invalid={Boolean(j.invalidFields.quantidade) || undefined} aria-describedby={j.invalidFields.quantidade ? 'decimal-help quantity-error' : 'decimal-help'}/>{j.invalidFields.quantidade && <small id="quantity-error" className="field-error">{j.invalidFields.quantidade}</small>}</div>
            <div className="form-field"><label htmlFor="consumption-measure">Medida</label><select id="consumption-measure" name="medida" required value={j.measure} onChange={e => { j.setMeasure(e.target.value); j.clearFieldError('unidade_medida'); }} aria-invalid={Boolean(j.invalidFields.unidade_medida) || undefined} aria-describedby={j.invalidFields.unidade_medida ? 'measure-error' : undefined}><option value="">Selecione</option>{j.sources.find(f => f.fonte_id === j.source)?.unidades_aceitas.map(m => <option key={m}>{m}</option>)}</select>{j.invalidFields.unidade_medida && <small className="field-error" id="measure-error">{j.invalidFields.unidade_medida}</small>}</div>
          </div><p id="decimal-help" className="nota">Informe decimal sem separador de milhar. Zero explícito é válido.</p></div> : <p className="empty-hint">Selecione uma loja e um mês para informar o consumo.</p>}
          {j.catalogLoading && <p role="status"><span className="spinner small-spinner" aria-hidden="true"/> Carregando fontes…</p>}
          <FormFeedback message={j.catalogError} retry={j.retryCatalog} retryLabel="Tentar carregar fontes novamente"/>
          {j.period && !j.catalogLoading && !j.catalogError && !j.sources.length && <p>Nenhuma fonte disponível para esta competência.</p>}
          <FormFeedback key={j.attempt} message={j.consumptionError} focus/>
          <div className="form-footer"><span className="nota">Eletricidade · Diesel · Gasolina · GLP</span><button className="btn" disabled={j.busy || !contextReady || j.catalogLoading || Boolean(j.catalogError) || !j.sources.length}>{j.operation === 'consumption' ? 'Salvando consumo…' : 'Salvar consumo'}</button></div>
          {(j.unit || j.period || j.quantity) && <button type="button" className="text-link draft-clear" disabled={j.busy} onClick={j.clearConsumptionDraft}>Limpar preenchimento</button>}
        </fieldset>
      </form>
    </section>
    {j.result && <ResultadoConsumo/>}
    <section className="card" aria-labelledby="saved-heading"><div className="section-heading"><h2 id="saved-heading">Consumos salvos</h2><span className="count-badge">{j.records.length} carregados</span></div>
      <p className="section-description">Os filtros de loja e competência acima também filtram esta consulta.</p>
      <FormFeedback message={j.recordsError} retry={j.retryRecords} retryLabel="Carregar consumos novamente"/>
      {j.loading ? <LoadingCards label="Carregando registros…"/> : !j.records.length && !j.recordsError ? <div className="empty-state compact"><h3>Seu histórico começa aqui</h3><p>Nenhum consumo encontrado. Os registros salvos aparecerão nesta lista.</p></div> : <ul className="record-list">
        {j.records.map(c => <li key={c.id} className={j.savedId === c.id ? 'just-created' : ''}><button className="record-button" disabled={j.busy} onClick={() => void j.consultRecord(c.id)}>
          <span><strong>{sourceName(c.fonte_id)}</strong><small><time dateTime={c.competencia}>{periodName(c.competencia)}</time> · {j.units.find(u => u.id === c.unidade_id)?.nome || c.unidade_id}</small></span>
          <span className="record-value">{formatDecimal(c.emissao_kg_co2e, 3)} <small>kg CO₂e</small><span className="record-action">{j.operation === `record-${c.id}` ? 'Consultando…' : 'Ver resultado →'}</span></span>
        </button></li>)}
      </ul>}
      {j.recordCursor && <button className="btn ghost" disabled={j.busy} onClick={() => void j.moreRecords()}>{j.operation === 'more-records' ? 'Carregando…' : 'Mais consumos'}</button>}
    </section>
  </>;
}
