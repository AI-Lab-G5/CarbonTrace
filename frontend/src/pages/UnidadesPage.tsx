import { useNavigate } from 'react-router';
import { useJornadasContext } from '@/hooks/useJornadasContext';
import { LoadingCards } from '@/components/LoadingCards';

export function UnidadesPage() {
  const j = useJornadasContext();
  const navigate = useNavigate();
  return <>
    <section aria-label="Unidades cadastradas" className="units-section">
      <div className="section-heading"><h2>Suas lojas</h2><span className="count-badge">{j.units.length} carregadas</span></div>
      {j.unitsLoading ? <LoadingCards label="Carregando unidades…"/> : !j.units.length ? <div className="empty-state"><span className="empty-symbol" aria-hidden="true">⌂</span><h3>Comece pela primeira loja</h3><p>Nenhuma unidade encontrada. Cadastre sua primeira loja.</p><a className="text-link" href="#cadastro-unidade">Cadastrar unidade ↓</a></div> : <ul className="unit-grid">
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
      <p className="eyebrow">Amplie seu inventário</p><h2 id="unit-form-heading">Cadastrar unidade</h2><p className="section-description">Adicione uma loja para começar a registrar seus consumos.</p>
      <form onSubmit={event => { event.preventDefault(); const form = event.currentTarget; void j.createUnit(new FormData(form), () => form.reset()); }}>
        <fieldset disabled={j.busy || j.unitsLoading} className="journey-fields"><div className="grid">
          <label>Nome<input name="nome" required maxLength={120} placeholder="Ex.: Loja Centro"/></label>
          <label>Cidade<input name="cidade" required maxLength={120} placeholder="Cidade da unidade"/></label>
          <label>UF<input name="uf" required minLength={2} maxLength={2} placeholder="Ex.: SP" autoCapitalize="characters"/></label>
        </div><button className="btn" disabled={j.busy}>{j.operation === 'unit' ? 'Cadastrando…' : 'Cadastrar'}</button></fieldset>
      </form>
    </section>
  </>;
}
