import { useEffect, useRef, useState } from 'react';
import type { User } from 'firebase/auth';
import { request } from '@/api';
import type { Consumo, Fator, Pagina, Unidade, Versao } from '@/types/api';
import { decimalInput } from '@/utils/decimal';
import { fieldErrors, FormValidationError, type FieldErrors } from '@/utils/validation';
import { readDraft, writeDraft } from '@/utils/drafts';

export function useJornadas(user: User, expired: () => void) {
  const [draft] = useState(() => readDraft(user.uid, 'consumption', ['unit', 'period', 'source', 'quantity', 'measure']));
  const [unitDraft, setUnitDraft] = useState(() => ({ nome: '', cidade: '', uf: '', ...readDraft(user.uid, 'unit', ['nome', 'cidade', 'uf']) }));
  const [draftRestored, setDraftRestored] = useState(Boolean(Object.values(draft).some(Boolean)));
  const [units, setUnits] = useState<Unidade[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [unit, setUnit] = useState(draft.unit || '');
  const [period, setPeriod] = useState(draft.period || '');
  const [sources, setSources] = useState<Fator[]>([]);
  const [source, setSource] = useState(draft.source || '');
  const [quantity, setQuantity] = useState(draft.quantity || '');
  const [measure, setMeasure] = useState(draft.measure || '');
  const [records, setRecords] = useState<Consumo[]>([]);
  const [result, setResult] = useState<Consumo | null>(null);
  const [factor, setFactor] = useState<Fator | null>(null);
  const [selectedUnit, setSelectedUnit] = useState<Unidade | null>(null);
  const [createdId, setCreatedId] = useState('');
  const [savedId, setSavedId] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [unitsError, setUnitsError] = useState('');
  const [recordsError, setRecordsError] = useState('');
  const [unitFormError, setUnitFormError] = useState('');
  const [consumptionError, setConsumptionError] = useState('');
  const [invalidFields, setInvalidFields] = useState<FieldErrors>({});
  const [factorError, setFactorError] = useState('');
  const [factorLoading, setFactorLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [operation, setOperation] = useState('');
  const locked = useRef(false);
  const recovery = useRef<(() => void) | null>(null);
  const factorGeneration = useRef(0);
  const [attempt, setAttempt] = useState(0);
  const [reload, setReload] = useState(0);
  const [unitsReload, setUnitsReload] = useState(0);
  const [catalogReload, setCatalogReload] = useState(0);
  const [recordCursor, setRecordCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [unitsLoading, setUnitsLoading] = useState(true);
  const [catalogLoading, setCatalogLoading] = useState(/^\d{4}-(0[1-9]|1[0-2])$/.test(draft.period || ''));
  const [catalogError, setCatalogError] = useState('');
  const query = new URLSearchParams({ limite: '20', ...(unit ? { unidade_id: unit } : {}), ...(period ? { competencia: period } : {}) }).toString();
  useEffect(() => { writeDraft(user.uid, 'consumption', { unit, period, source, quantity, measure }); }, [user.uid, unit, period, source, quantity, measure]);
  useEffect(() => { writeDraft(user.uid, 'unit', unitDraft); }, [user.uid, unitDraft]);

  function clearFieldError(name: string) {
    setInvalidFields(current => { const next = { ...current }; delete next[name]; return next; });
  }
  function updateUnitDraft(name: keyof typeof unitDraft, value: string) {
    setUnitDraft(current => ({ ...current, [name]: value })); clearFieldError(name);
  }

  async function api<T>(path: string, options?: RequestInit) {
    try { return await request<T>(path, await user.getIdToken(), options); }
    catch (e) { if (e && typeof e === 'object' && 'status' in e && e.status === 401) expired(); throw e; }
  }
  async function action(work: () => Promise<void>, name = '') {
    if (locked.current) return;
    locked.current = true;
    setBusy(true); setAttempt(value => value + 1); setOperation(name); setError(''); setMessage('');
    if (name === 'unit') setUnitFormError('');
    if (name === 'consumption') setConsumptionError('');
    try { await work(); } catch (e) {
      const message = e instanceof Error ? e.message : 'Não foi possível concluir. Tente novamente.';
      if (name === 'unit' || name === 'consumption') {
        setInvalidFields(current => ({ ...current, ...fieldErrors(e) }));
        if (name === 'unit') setUnitFormError(message); else setConsumptionError(message);
      } else { setError(message); recovery.current = () => { void action(work, name); }; }
    }
    finally { locked.current = false; setBusy(false); setOperation(''); }
  }
  useEffect(() => {
    const controller = new AbortController();
    user.getIdToken().then(token => request<Pagina<Unidade>>('/v1/unidades?limite=20', token, { signal: controller.signal }))
      .then(async u => {
        // A loja recuperada pode estar além da primeira página do catálogo.
        let items = u.itens;
        if (draft.unit && !items.some(item => item.id === draft.unit)) {
          try {
            const restored = await request<Unidade>(`/v1/unidades/${encodeURIComponent(draft.unit)}`, await user.getIdToken(), { signal: controller.signal });
            items = [...items, restored];
          } catch (e) {
            if (controller.signal.aborted) return;
            if (e && typeof e === 'object' && 'status' in e && e.status === 401) expired();
            setUnit(current => current === draft.unit ? '' : current);
            setMessage('A loja do rascunho não pôde ser recuperada. Selecione a loja novamente; os outros dados foram mantidos.');
          }
        }
        if (!controller.signal.aborted) { setUnits(items); setCursor(u.proximo_cursor); setUnitsError(''); }
      })
      .catch(e => { if (!controller.signal.aborted) { setUnitsError(e.message); if (e.status === 401) expired(); } })
      .finally(() => { if (!controller.signal.aborted) setUnitsLoading(false); });
    return () => controller.abort();
  }, [user, unitsReload, expired, draft.unit]);
  useEffect(() => {
    const controller = new AbortController();
    user.getIdToken().then(token => request<Pagina<Consumo>>(`/v1/consumos?${query}`, token, { signal: controller.signal }))
      .then(c => { if (!controller.signal.aborted) { setRecords(c.itens); setRecordCursor(c.proximo_cursor); setRecordsError(''); } })
      .catch(e => { if (!controller.signal.aborted) { setRecordsError(e.message); if (e.status === 401) expired(); } })
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
  }, [user, period, catalogReload, expired]);

  async function loadFactor(versionId: string, sourceId: string) {
    const current = ++factorGeneration.current;
    setFactor(null); setFactorError(''); setFactorLoading(true);
    try {
      const version = await api<Versao>(`/v1/fontes/versoes/${encodeURIComponent(versionId)}`);
      const found = version.fatores.find(f => f.fonte_id === sourceId) || null;
      if (current !== factorGeneration.current) return;
      setFactor(found);
      if (!found) setFactorError('A referência deste fator não está disponível. O resultado salvo foi preservado.');
    } catch (e) { if (current === factorGeneration.current) setFactorError(e instanceof Error ? e.message : 'Não foi possível carregar a referência do fator.'); }
    finally { if (current === factorGeneration.current) setFactorLoading(false); }
  }
  async function show(id: string) {
    const saved = await api<Consumo>(`/v1/consumos/${encodeURIComponent(id)}`);
    setResult(saved);
    await loadFactor(saved.fator_versao, saved.fonte_id);
  }
  function selectUnit(value: string) {
    factorGeneration.current++; setFactorLoading(false); setFactorError('');
    setUnit(value); setRecordsError(''); setConsumptionError(''); clearFieldError('unidade_id'); setRecords([]); setResult(null); setRecordCursor(null); setLoading(true);
  }
  function selectPeriod(value: string) {
    factorGeneration.current++; setFactorLoading(false); setFactorError('');
    setPeriod(value); setCatalogLoading(/^\d{4}-(0[1-9]|1[0-2])$/.test(value)); setCatalogError(''); setRecordsError(''); setConsumptionError(''); clearFieldError('competencia'); setSources([]); setSource(''); setMeasure(''); setRecords([]); setResult(null); setRecordCursor(null); setLoading(true);
  }
  function selectSource(value: string) { setSource(value); setMeasure(''); clearFieldError('fonte_id'); clearFieldError('unidade_medida'); }
  function retryUnits() { setUnitsError(''); setUnitsLoading(true); setUnitsReload(r => r + 1); }
  function retryRecords() { setRecordsError(''); setLoading(true); setReload(r => r + 1); }
  function retry() { recovery.current?.(); }
  function retryCatalog() { setCatalogError(''); setCatalogLoading(true); setCatalogReload(r => r + 1); }
  function createUnit(data: FormData, reset: () => void) {
    return action(async () => {
      const input = { nome: String(data.get('nome')).trim(), cidade: String(data.get('cidade')).trim(), uf: String(data.get('uf')).trim().toUpperCase() };
      const fields: FieldErrors = {};
      if (!input.nome) fields.nome = 'Informe o nome da unidade.';
      if (!input.cidade) fields.cidade = 'Informe a cidade da unidade.';
      if (!/^[A-Z]{2}$/.test(input.uf)) fields.uf = 'Informe a UF com duas letras, como DF ou SP.';
      if (Object.keys(fields).length) throw new FormValidationError(fields);
      const created = await api<Unidade>('/v1/unidades', { method: 'POST', body: JSON.stringify(input) });
      setUnits(current => [...current, created]); setCreatedId(created.id); setMessage('Unidade cadastrada.'); setUnitDraft({ nome: '', cidade: '', uf: '' }); writeDraft(user.uid, 'unit', {}); reset();
    }, 'unit');
  }
  function saveConsumption() {
    return action(async () => {
      const fields: FieldErrors = {};
      let quantidade = '';
      try { quantidade = decimalInput(quantity); } catch (e) { fields.quantidade = (e as Error).message; }
      if (!unit) fields.unidade_id = 'Selecione a loja deste consumo.';
      if (!source) fields.fonte_id = 'Selecione a fonte do consumo.';
      if (!sources.find(f => f.fonte_id === source)?.unidades_aceitas.includes(measure)) fields.unidade_medida = 'Selecione uma medida compatível com a fonte.';
      if (!/^\d{4}-(0[1-9]|1[0-2])$/.test(period)) fields.competencia = 'Informe competência no formato AAAA-MM.';
      if (Object.keys(fields).length) throw new FormValidationError(fields);
      const existing = await api<Pagina<Consumo>>(`/v1/consumos?${new URLSearchParams({ unidade_id: unit, competencia: period, limite: '100' })}`);
      if (existing.proximo_cursor) throw new Error('Consulta incompleta: confira os registros antes de salvar.');
      const previous = existing.itens.find(c => c.fonte_id === source);
      if (previous) { await show(previous.id); throw new Error('Este consumo já existe. Consulte o resultado salvo; a API ainda não oferece correção com histórico.'); }
      const saved = await api<Consumo>('/v1/consumos', { method: 'PUT', body: JSON.stringify({ unidade_id: unit, competencia: period, fonte_id: source, quantidade, unidade_medida: measure }) });
      setSavedId(saved.id); setFactor(null); setFactorError(''); setResult(saved); setLoading(true); setReload(r => r + 1);
      writeDraft(user.uid, 'consumption', {}); setDraftRestored(false);
      try { await show(saved.id); setMessage('Consumo salvo e consultado pela API.'); }
      catch {
        setConsumptionError('Consumo salvo. Não foi possível atualizar a consulta; confira os consumos salvos antes de reenviar.');
        setFactorError('A referência do fator ainda não pôde ser consultada. O resultado salvo foi preservado.');
      }
    }, 'consumption');
  }
  function moreUnits() {
    return action(async () => {
      const page = await api<Pagina<Unidade>>(`/v1/unidades?limite=20&cursor=${encodeURIComponent(cursor!)}`);
      setUnits(current => [...current, ...page.itens.filter(item => !current.some(unit => unit.id === item.id))]); setCursor(page.proximo_cursor);
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
  function clearConsumptionDraft() {
    factorGeneration.current++; setFactorLoading(false); setFactorError('');
    setUnit(''); setPeriod(''); setSource(''); setQuantity(''); setMeasure(''); setResult(null);
    setCatalogLoading(false); setCatalogError(''); setRecordsError(''); setLoading(true); setDraftRestored(false); setConsumptionError(''); setInvalidFields({});
    writeDraft(user.uid, 'consumption', {});
  }
  return { units, cursor, unit, period, sources, source, quantity, setQuantity, measure, setMeasure,
    records, result, factor, selectedUnit, createdId, savedId, message, error, busy, operation,
    unitsError, recordsError, unitFormError, consumptionError, invalidFields, clearFieldError, factorError, factorLoading, unitDraft, updateUnitDraft, draftRestored, clearConsumptionDraft, attempt,
    recordCursor, loading, unitsLoading, catalogLoading, catalogError, selectUnit, selectPeriod, selectSource,
    retry, retryUnits, retryRecords, retryCatalog, retryFactor: () => { if (result) void loadFactor(result.fator_versao, result.fonte_id); }, createUnit, saveConsumption, moreUnits, moreRecords, consultUnit, consultRecord, checkOriginal };
}
