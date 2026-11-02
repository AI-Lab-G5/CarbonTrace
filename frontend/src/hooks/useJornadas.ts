import { useEffect, useRef, useState } from 'react';
import type { User } from 'firebase/auth';
import { request } from '@/api';
import type { Consumo, Fator, Pagina, Unidade, Versao } from '@/types/api';
import { decimalInput } from '@/utils/decimal';

export function useJornadas(user: User, expired: () => void) {
  const [units, setUnits] = useState<Unidade[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [unit, setUnit] = useState('');
  const [period, setPeriod] = useState('');
  const [sources, setSources] = useState<Fator[]>([]);
  const [source, setSource] = useState('');
  const [quantity, setQuantity] = useState('');
  const [measure, setMeasure] = useState('');
  const [records, setRecords] = useState<Consumo[]>([]);
  const [result, setResult] = useState<Consumo | null>(null);
  const [factor, setFactor] = useState<Fator | null>(null);
  const [selectedUnit, setSelectedUnit] = useState<Unidade | null>(null);
  const [createdId, setCreatedId] = useState('');
  const [savedId, setSavedId] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [operation, setOperation] = useState('');
  const locked = useRef(false);
  const [reload, setReload] = useState(0);
  const [unitsReload, setUnitsReload] = useState(0);
  const [recordCursor, setRecordCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [unitsLoading, setUnitsLoading] = useState(true);
  const [catalogLoading, setCatalogLoading] = useState(false);
  const [catalogError, setCatalogError] = useState('');
  const query = new URLSearchParams({ limite: '20', ...(unit ? { unidade_id: unit } : {}), ...(period ? { competencia: period } : {}) }).toString();

  async function api<T>(path: string, options?: RequestInit) {
    try { return await request<T>(path, await user.getIdToken(), options); }
    catch (e) { if (e && typeof e === 'object' && 'status' in e && e.status === 401) expired(); throw e; }
  }
  async function action(work: () => Promise<void>, name = '') {
    if (locked.current) return;
    locked.current = true;
    setBusy(true); setOperation(name); setError(''); setMessage('');
    try { await work(); } catch (e) { setError(e instanceof Error ? e.message : 'Falha na operação.'); }
    finally { locked.current = false; setBusy(false); setOperation(''); }
  }
  useEffect(() => {
    const controller = new AbortController();
    user.getIdToken().then(token => request<Pagina<Unidade>>('/v1/unidades?limite=20', token, { signal: controller.signal }))
      .then(u => { if (!controller.signal.aborted) { setUnits(u.itens); setCursor(u.proximo_cursor); } })
      .catch(e => { if (!controller.signal.aborted) { setError(e.message); if (e.status === 401) expired(); } })
      .finally(() => { if (!controller.signal.aborted) setUnitsLoading(false); });
    return () => controller.abort();
  }, [user, unitsReload, expired]);
  useEffect(() => {
    const controller = new AbortController();
    user.getIdToken().then(token => request<Pagina<Consumo>>(`/v1/consumos?${query}`, token, { signal: controller.signal }))
      .then(c => { if (!controller.signal.aborted) { setRecords(c.itens); setRecordCursor(c.proximo_cursor); } })
      .catch(e => { if (!controller.signal.aborted) { setError(e.message); if (e.status === 401) expired(); } })
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
  function selectUnit(value: string) {
    setUnit(value); setRecords([]); setResult(null); setRecordCursor(null); setLoading(true);
  }
  function selectPeriod(value: string) {
    setPeriod(value); setCatalogLoading(Boolean(value)); setCatalogError(''); setSources([]); setSource(''); setMeasure(''); setRecords([]); setResult(null); setRecordCursor(null); setLoading(true);
  }
  function selectSource(value: string) { setSource(value); setMeasure(''); }
  function retry() {
    setError(''); setLoading(true); setUnitsLoading(true); setReload(r => r + 1); setUnitsReload(r => r + 1);
  }
  function retryCatalog() { setCatalogError(''); setCatalogLoading(true); setReload(r => r + 1); }
  function createUnit(data: FormData, reset: () => void) {
    return action(async () => {
      const input = { nome: String(data.get('nome')).trim(), cidade: String(data.get('cidade')).trim(), uf: String(data.get('uf')).trim().toUpperCase() };
      if (!input.nome || !input.cidade || !/^[A-Z]{2}$/.test(input.uf)) throw new Error('Preencha nome, cidade e UF de duas letras.');
      const created = await api<Unidade>('/v1/unidades', { method: 'POST', body: JSON.stringify(input) });
      setUnits(current => [...current, created]); setCreatedId(created.id); setMessage('Unidade cadastrada.'); reset();
    }, 'unit');
  }
  function saveConsumption() {
    return action(async () => {
      const quantidade = decimalInput(quantity);
      if (!unit || !source || !sources.find(f => f.fonte_id === source)?.unidades_aceitas.includes(measure)) throw new Error('Selecione loja, fonte e medida compatível.');
      if (!/^\d{4}-(0[1-9]|1[0-2])$/.test(period)) throw new Error('Informe competência no formato AAAA-MM.');
      const existing = await api<Pagina<Consumo>>(`/v1/consumos?${new URLSearchParams({ unidade_id: unit, competencia: period, limite: '100' })}`);
      if (existing.proximo_cursor) throw new Error('Consulta incompleta: confira os registros antes de salvar.');
      const previous = existing.itens.find(c => c.fonte_id === source);
      if (previous) { await show(previous.id); throw new Error('Este consumo já existe. Consulte o resultado salvo; a API ainda não oferece correção com histórico.'); }
      const saved = await api<Consumo>('/v1/consumos', { method: 'PUT', body: JSON.stringify({ unidade_id: unit, competencia: period, fonte_id: source, quantidade, unidade_medida: measure }) });
      setSavedId(saved.id); await show(saved.id); setLoading(true); setReload(r => r + 1); setMessage('Consumo salvo e consultado pela API.');
    }, 'consumption');
  }
  function moreUnits() {
    return action(async () => {
      const page = await api<Pagina<Unidade>>(`/v1/unidades?limite=20&cursor=${encodeURIComponent(cursor!)}`);
      setUnits(current => [...current, ...page.itens]); setCursor(page.proximo_cursor);
    }, 'more-units');
  }
  function moreRecords() {
    return action(async () => {
      const page = await api<Pagina<Consumo>>(`/v1/consumos?${query}&cursor=${encodeURIComponent(recordCursor!)}`);
      setRecords(current => [...current, ...page.itens]); setRecordCursor(page.proximo_cursor);
    }, 'more-records');
  }
  function consultUnit(id: string) { return action(async () => { setSelectedUnit(await api<Unidade>(`/v1/unidades/${encodeURIComponent(id)}`)); }, `unit-${id}`); }
  function consultRecord(id: string) { return action(() => show(id), `record-${id}`); }
  function checkOriginal() {
    return action(async () => {
      if (!result) return;
      const checked = await api<Consumo>(`/v1/consumos/${encodeURIComponent(result.id)}/recalculo`, { method: 'POST' });
      setResult(checked); setMessage('Reprodução concluída pela API com o fator original.');
    }, 'check');
  }
  return { units, cursor, unit, period, sources, source, quantity, setQuantity, measure, setMeasure,
    records, result, factor, selectedUnit, createdId, savedId, message, error, busy, operation,
    recordCursor, loading, unitsLoading, catalogLoading, catalogError, selectUnit, selectPeriod, selectSource,
    retry, retryCatalog, createUnit, saveConsumption, moreUnits, moreRecords, consultUnit, consultRecord, checkOriginal };
}
