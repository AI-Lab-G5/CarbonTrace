import { useNavigate } from 'react-router';
import { useJornadasContext } from '@/hooks/useJornadasContext';
import { LoadingCards } from '@/components/LoadingCards';
import { FormFeedback } from '@/components/FormFeedback';

export function UnidadesPage() {
  const j = useJornadasContext();
  const navigate = useNavigate();
  return <>
    <section aria-label="Unidades cadastradas" className="units-section">
      <div className="section-heading"><h2>Suas lojas</h2><span className="count-badge">{j.units.length} carregadas</span></div>
      <FormFeedback message={j.unitsError} retry={j.retryUnits} retryLabel="Consultar novamente"/>
      {j.unitsLoading ? <LoadingCards label="Carregando unidades…"/> : !j.units.length && !j.unitsError ? <div className="empty-state"><span className="empty-symbol" aria-hidden="true">⌂</span><h3>Comece pela primeira loja</h3><p>Nenhuma unidade encontrada. Cadastre sua primeira loja.</p><a className="text-link" href="#cadastro-unidade">Cadastrar unidade ↓</a></div> : <ul className="unit-grid">
        {j.units.map(u => <li key={u.id} className={`unit-card ${j.createdId === u.id ? 'just-created' : ''}`}>
          <span className="unit-symbol" aria-hidden="true">⌂</span>
          <h3>{u.nome}</h3><p>{u.cidade} / {u.uf}</p>
          {j.createdId === u.id && <span className="new-label">Recém-cadastrada</span>}
          <div className="unit-actions"><button className="text-link" disabled={j.busy} onClick={() => void j.consultUnit(u.id)}>{j.operation === `unit-${u.id}` ? 'Consultando…' : 'Consultar loja'}</button>
          <button className="btn ghost" disabled={j.busy} onClick={() => { if (j.unit !== u.id) j.selectUnit(u.id); navigate('/consumos'); }}>Registrar consumo →</button></div>
        </li>)}
      </ul>}
      {j.cursor && <button className="btn ghost" disabled={j.busy} onClick={() => void j.moreUnits()}>{j.operation === 'more-units' ? 'Carregando…' : 'Mais unidades'}</button>}
      {j.selectedUnit && <div className="unit-detail feedback" role="region" aria-label="Detalhes da loja"><strong>{j.selectedUnit.nome}</strong><p>{j.selectedUnit.cidade} / {j.selectedUnit.uf}</p></div>}
    </section>
    <section className="card" id="cadastro-unidade" aria-labelledby="unit-form-heading">
      <h2 id="unit-form-heading">Cadastrar unidade</h2><p className="section-description">Adicione uma loja para começar a registrar seus consumos.</p>
      <form onSubmit={event => { event.preventDefault(); const form = event.currentTarget; void j.createUnit(new FormData(form), () => form.reset()); }}>
        <fieldset disabled={j.busy || j.unitsLoading || Boolean(j.unitsError)} className="journey-fields"><div className="grid">
          {(['nome', 'cidade', 'uf'] as const).map(name => <div className="form-field" key={name}>
            <label htmlFor={`unit-${name}`}>{name === 'nome' ? 'Nome' : name === 'cidade' ? 'Cidade' : 'UF'}</label>
            <input id={`unit-${name}`} name={name} required maxLength={name === 'uf' ? 2 : 120} minLength={name === 'uf' ? 2 : undefined} placeholder={name === 'nome' ? 'Ex.: Loja Centro' : name === 'cidade' ? 'Cidade da unidade' : 'Ex.: SP'} autoComplete={name === 'uf' ? 'address-level1' : name === 'cidade' ? 'address-level2' : 'organization'} autoCapitalize={name === 'uf' ? 'characters' : 'words'} value={j.unitDraft[name]} onChange={event => j.updateUnitDraft(name, event.target.value)} aria-invalid={Boolean(j.invalidFields[name]) || undefined} aria-describedby={j.invalidFields[name] ? `unit-${name}-error` : undefined}/>
            {j.invalidFields[name] && <small className="field-error" id={`unit-${name}-error`}>{j.invalidFields[name]}</small>}
          </div>)}
        </div><FormFeedback key={j.attempt} message={j.unitFormError} focus/><button className="btn" disabled={j.busy}>{j.operation === 'unit' ? 'Cadastrando…' : 'Cadastrar'}</button></fieldset>
      </form>
    </section>
  </>;
}
