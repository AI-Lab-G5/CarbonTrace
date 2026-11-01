import { useEffect, useState } from 'react';
import type { User } from 'firebase/auth';
import { request } from '@/api';
import type { Consumo, Fator, Pagina, Unidade, Versao } from '@/types/api';
import { decimalInput, formatDecimal } from '@/utils/decimal';

export function Jornadas({ user, expired }: { user: User; expired: () => void }) {
  const [units, setUnits] = useState<Unidade[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [unit, setUnit] = useState('');
  const [period, setPeriod] = useState('');
  const [sources, setSources] = useState<Fator[]>([]);
  const [source, setSource] = useState('');
  const [records, setRecords] = useState<Consumo[]>([]);
  const [result, setResult] = useState<Consumo | null>(null);
  const [factor, setFactor] = useState<Fator | null>(null);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [reload, setReload] = useState(0);
  const [recordCursor, setRecordCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [catalogLoading, setCatalogLoading] = useState(false);
  const [catalogError, setCatalogError] = useState('');
  const query = new URLSearchParams({ limite: '20', ...(unit ? { unidade_id: unit } : {}), ...(period ? { competencia: period } : {}) }).toString();
  async function api<T>(path: string, options?: RequestInit) {
    try { return await request<T>(path, await user.getIdToken(), options); }
    catch (e) { if (e && typeof e === 'object' && 'status' in e && e.status === 401) expired(); throw e; }
  }
  async function action(work: () => Promise<void>) {
    setBusy(true); setError(''); setMessage('');
    try { await work(); } catch (e) { setError(e instanceof Error ? e.message : 'Falha na operação.'); }
    finally { setBusy(false); }
  }
  useEffect(() => {
    const controller = new AbortController();
    user.getIdToken().then(token => Promise.all([
      request<Pagina<Unidade>>('/v1/unidades?limite=20', token, { signal: controller.signal }),
      request<Pagina<Consumo>>(`/v1/consumos?${query}`, token, { signal: controller.signal }),
    ])).then(([u, c]) => {
      if (!controller.signal.aborted) { setUnits(u.itens); setCursor(u.proximo_cursor); setRecords(c.itens); setRecordCursor(c.proximo_cursor); }
    }).catch(e => { if (!controller.signal.aborted) { setError(e.message); if (e.status === 401) expired(); } })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [user, query, reload, expired]);
  useEffect(() => {
    if (!/^\d{4}-(0[1-9]|1[0-2])$/.test(period)) return;
    const controller = new AbortController();
    user.getIdToken().then(token => request<Fator[]>(`/v1/fontes?competencia=${period}`, token, { signal: controller.signal }))
      .then(data => { if (!controller.signal.aborted) { setSources(data.filter(f => ['eletricidade', 'diesel', 'gasolina', 'glp'].includes(f.fonte_id))); setCatalogLoading(false); } })
      .catch(e => { if (!controller.signal.aborted) { setCatalogError(e.message); setCatalogLoading(false); if (e.status === 401) expired(); } });
    return () => controller.abort();
  }, [user, period, reload, expired]);
  async function show(id: string) {
    const saved = await api<Consumo>(`/v1/consumos/${encodeURIComponent(id)}`);
    setResult(saved); setFactor(null);
    const version = await api<Versao>(`/v1/fontes/versoes/${encodeURIComponent(saved.fator_versao)}`);
    setFactor(version.fatores.find(f => f.fonte_id === saved.fonte_id) || null);
  }
  return <div className="wrap" id="jornadas">
    <h1>Unidades e coleta mensal</h1><fieldset disabled={busy} className="journey-fields"><legend className="nota">Cadastro, coleta e consulta</legend>
    {loading && <p role="status">◌ Carregando registros…</p>}
    {busy && <p role="status">◌ Processando…</p>}
    {message && <p role="status">✓ {message}</p>}
    {error && <div role="alert" className="error-box">⚠ {error} <button type="button" className="btn ghost" disabled={busy} onClick={() => { setError(''); setLoading(true); setReload(r => r + 1); }}>Consultar novamente</button></div>}
    <section className="card"><h2>Unidades da empresa</h2>
      {!loading && !units.length && <p>Nenhuma unidade encontrada. Cadastre sua primeira loja.</p>}
      <ul>{units.map(u => <li key={u.id}>{u.nome} — {u.cidade}/{u.uf} <button type="button" className="btn ghost" disabled={busy} onClick={() => void action(async () => { const detail = await api<Unidade>(`/v1/unidades/${encodeURIComponent(u.id)}`); setMessage(`${detail.nome} — ${detail.cidade}/${detail.uf}`); })}>Consultar loja</button></li>)}</ul>
      {cursor && <button className="btn ghost" disabled={busy} onClick={() => void action(async () => { const page = await api<Pagina<Unidade>>(`/v1/unidades?limite=20&cursor=${encodeURIComponent(cursor)}`); setUnits(current => [...current, ...page.itens]); setCursor(page.proximo_cursor); })}>Mais unidades</button>}
      <form onSubmit={event => { event.preventDefault(); const form = event.currentTarget; const data = new FormData(form); void action(async () => {
        const input = { nome: String(data.get('nome')).trim(), cidade: String(data.get('cidade')).trim(), uf: String(data.get('uf')).trim().toUpperCase() };
        if (!input.nome || !input.cidade || !/^[A-Z]{2}$/.test(input.uf)) throw new Error('Preencha nome, cidade e UF de duas letras.');
        const created = await api<Unidade>('/v1/unidades', { method: 'POST', body: JSON.stringify(input) });
        setUnits(current => [...current, created]); setMessage('Unidade cadastrada.'); form.reset();
      }); }}><h3>Cadastrar unidade</h3><div className="grid">
        <label>Nome<input name="nome" required maxLength={120} /></label><label>Cidade<input name="cidade" required maxLength={120} /></label><label>UF<input name="uf" required minLength={2} maxLength={2} /></label>
      </div><button className="btn" disabled={busy}>Cadastrar</button></form>
      <p className="nota">Código único e vínculo de fontes por loja aguardam suporte da API. O catálogo abaixo é global.</p>
    </section>
    <section className="card"><h2>Registrar consumo</h2><form onSubmit={event => {
      event.preventDefault(); const data = new FormData(event.currentTarget); void action(async () => {
        const quantidade = decimalInput(String(data.get('quantidade')));
        if (!unit || !source || !sources.find(f => f.fonte_id === source)?.unidades_aceitas.includes(String(data.get('medida')))) throw new Error('Selecione loja, fonte e medida compatível.');
        if (!/^\d{4}-(0[1-9]|1[0-2])$/.test(period)) throw new Error('Informe competência no formato AAAA-MM.');
        const existing = await api<Pagina<Consumo>>(`/v1/consumos?${new URLSearchParams({ unidade_id: unit, competencia: period, limite: '100' })}`);
        if (existing.proximo_cursor) throw new Error('Consulta incompleta: confira os registros antes de salvar.');
        const previous = existing.itens.find(c => c.fonte_id === source);
        if (previous) { await show(previous.id); throw new Error('Este consumo já existe. Consulte o resultado salvo; a API ainda não oferece correção com histórico.'); }
        const saved = await api<Consumo>('/v1/consumos', { method: 'PUT', body: JSON.stringify({ unidade_id: unit, competencia: period, fonte_id: source, quantidade, unidade_medida: data.get('medida') }) });
        await show(saved.id); setReload(r => r + 1); setMessage('Consumo salvo e consultado pela API.');
      });
    }}><div className="grid">
      <label>Loja<select required value={unit} onChange={e => { setUnit(e.target.value); setRecords([]); setResult(null); setLoading(true); }}><option value="">Selecione</option>{units.map(u => <option key={u.id} value={u.id}>{u.nome}</option>)}</select></label>
      <label>Competência<input type="month" required value={period} onChange={e => { setPeriod(e.target.value); setCatalogLoading(Boolean(e.target.value)); setCatalogError(''); setSources([]); setSource(''); setRecords([]); setResult(null); setLoading(true); }} /></label>
      <label>Fonte<select required value={source} onChange={e => setSource(e.target.value)}><option value="">Selecione</option>{sources.map(f => <option key={f.fonte_id} value={f.fonte_id}>{f.nome}</option>)}</select></label>
      <label>Quantidade<input name="quantidade" inputMode="decimal" required aria-describedby="decimal-help" /></label>
      <label>Medida<select name="medida" key={source} required><option value="">Selecione</option>{sources.find(f => f.fonte_id === source)?.unidades_aceitas.map(m => <option key={m}>{m}</option>)}</select></label>
    </div><p id="decimal-help">Informe decimal sem separador de milhar. Zero explícito é válido.</p>
    {catalogLoading && <p role="status">◌ Carregando fontes…</p>}
    {catalogError && <p role="alert">⚠ {catalogError} <button type="button" className="btn ghost" onClick={() => { setCatalogError(''); setCatalogLoading(true); setReload(r => r + 1); }}>Tentar carregar fontes novamente</button></p>}
    {period && !catalogLoading && !catalogError && !sources.length && <p>Nenhuma fonte disponível para esta competência.</p>}
    <button className="btn" disabled={busy || catalogLoading || Boolean(catalogError) || !sources.length}>Salvar consumo</button></form></section>
    <section className="card"><h2>Consumos salvos</h2><p>Os filtros de loja e competência acima também filtram esta consulta.</p>
      {!loading && !records.length && <p>Nenhum consumo encontrado.</p>}
      <ul>{records.map(c => <li key={c.id}><button className="btn ghost" disabled={busy} onClick={() => void action(() => show(c.id))}>{c.competencia} · {c.fonte_id} · {formatDecimal(c.emissao_kg_co2e, 3)} kgCO₂e</button></li>)}</ul>
      {recordCursor && <button className="btn" disabled={busy} onClick={() => void action(async () => { const page = await api<Pagina<Consumo>>(`/v1/consumos?${query}&cursor=${encodeURIComponent(recordCursor)}`); setRecords(current => [...current, ...page.itens]); setRecordCursor(page.proximo_cursor); })}>Mais consumos</button>}
    </section>
    {result && <section className="card" aria-label="Resultado salvo"><h2>Resultado salvo</h2><dl>
      <dt>Loja / competência / fonte</dt><dd>{units.find(u => u.id === result.unidade_id)?.nome || result.unidade_id} / {result.competencia} / {result.fonte_id}</dd>
      <dt>Quantidade original</dt><dd>{formatDecimal(result.quantidade_informada)} {result.unidade_informada}</dd>
      <dt>Conversão registrada</dt><dd>{formatDecimal(result.quantidade_convertida)} {result.unidade_base}</dd>
      <dt>Fator / versão</dt><dd>{formatDecimal(result.fator_valor)} kgCO₂e/{result.unidade_base} · {result.fator_versao}</dd>
      <dt>Emissão / escopo</dt><dd>{formatDecimal(result.emissao_kg_co2e, 3)} kgCO₂e · Escopo {result.escopo}</dd>
      <dt>Status e referência</dt><dd>{factor ? `${factor.status} — ${factor.fonte_referencia}` : 'Metadados do fator indisponíveis.'}</dd>
    </dl><p>Estimativa limitada às fontes previstas. Fatores preliminares não representam inventário homologado. Autoria e datas ainda não são fornecidas pela API.</p>
      <button className="btn" disabled={busy} onClick={() => void action(async () => { const checked = await api<Consumo>(`/v1/consumos/${encodeURIComponent(result.id)}/recalculo`, { method: 'POST' }); setResult(checked); setMessage('Reprodução concluída pela API com o fator original.'); })}>Conferir cálculo original</button>
    </section>}
  </fieldset></div>;
}
