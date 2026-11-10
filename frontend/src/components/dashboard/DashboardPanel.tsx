import { formatDecimal } from '@/utils/decimal';
import { FormFeedback } from '@/components/FormFeedback';
import './dashboard.css';

// Modelo LOCAL de apresentação. Não representa o contrato HTTP de #34/#35.
export type Selection = { month: string; unit: string; region: string; snapshot: string };
export type Choice = { value: string; label: string };
export function DashboardFilters({ value, onChange, units, regions, snapshots, disabled = false }: {
  value: Selection; onChange: (value: Selection) => void; units: Choice[]; regions: Choice[]; snapshots: Choice[]; disabled?: boolean;
}) {
  return <fieldset className="journey-fields" disabled={disabled}><legend>Recorte da consulta</legend><div className="grid">
    <label>Competência<input type="month" value={value.month} onChange={e => onChange({...value, month:e.target.value, snapshot:''})}/></label>
    {([{key:'region', label:'Região', options:regions}, {key:'unit', label:'Unidade', options:units}, {key:'snapshot', label:'Snapshot', options:snapshots}] as const).map(({key,label,options}) => <label key={key}>{label}<select value={value[key]} onChange={e => onChange({...value, [key]:e.target.value, ...(key === 'region' ? {unit:''} : {})})}><option value="">{key === 'snapshot' ? 'Selecione' : 'Todas'}</option>{options.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}</select></label>)}
  </div></fieldset>;
}
export type AmountRow = { label: string; amount: string };
export type Comparison = { label: string; detail: string; status: 'within' | 'alert' | 'unavailable' };
export type DashboardView = {
  context: string; coverage: string; partial: boolean;
  total: string; median: string | null; medianReason?: string;
  scopes: AmountRow[]; regions: AmountRow[]; months: AmountRow[];
  units: { id: string; label: string; amount: string | null; comparison: Comparison }[];
  pending: { id: string; label: string }[];
};
export type DashboardState = { kind:'loading' } | { kind:'empty' } | { kind:'unavailable'; reason:string } | { kind:'error'; message:string } | { kind:'ready'; data:DashboardView };
function Amount({value}: {value:string}) { return <>{formatDecimal(value,3)} kgCO₂e</>; }
function Totals({title, rows}: {title:string; rows:AmountRow[]}) {
  return <section className="dashboard-group"><h3>{title}</h3><dl className="dashboard-values">{rows.map(row => <div key={row.label}><dt>{row.label}</dt><dd><Amount value={row.amount}/></dd></div>)}</dl></section>;
}
export function DashboardPanel({state, retry}: {state:DashboardState; retry:()=>void}) {
  if(state.kind === 'loading') return <p role="status"><span className="spinner small-spinner" aria-hidden="true"/> Preparando o consolidado. A primeira conexão pode levar cerca de um minuto.</p>;
  if(state.kind === 'error') return <FormFeedback message={state.message} retry={retry}/>;
  if(state.kind === 'empty') return <p role="status">Nenhum consolidado encontrado para este recorte. Escolha outra competência ou ajuste os filtros.</p>;
  if(state.kind === 'unavailable') return <p role="status">Comparação indisponível: {state.reason}</p>;
  const {data} = state;
  return <div className="dashboard-panel">
    <p className="feedback" role="status"><StatusIcon/>{data.partial ? 'Resultado parcial' : 'Resultado disponível'} — {data.coverage}</p>
    <p>{data.context}</p>
    <dl className="dashboard-summary"><div><dt>Total do recorte</dt><dd><Amount value={data.total}/></dd></div><div><dt>Mediana</dt><dd>{data.median === null ? `Indisponível: ${data.medianReason || 'base insuficiente para comparação'}` : <Amount value={data.median}/>}</dd></div></dl>
    <div className="dashboard-breakdown"><Totals title="Por escopo" rows={data.scopes}/><Totals title="Por região" rows={data.regions}/><Totals title="Por mês" rows={data.months}/></div>
    <section className="dashboard-group"><h3>Ranking informado para o recorte</h3><p className="nota">Ordem e valores fornecidos pelo consolidado. Coleta ausente não equivale a zero.</p>
      <ol className="dashboard-ranking">{data.units.map(unit => <li key={unit.id}><strong>{unit.label}</strong><span>{unit.amount === null ? 'Coleta ausente' : <Amount value={unit.amount}/>}</span><p><StatusIcon/>{unit.comparison.status === 'alert' ? 'Atenção' : unit.comparison.status === 'unavailable' ? 'Comparação indisponível' : 'Sem alerta'}: {unit.comparison.label} — {unit.comparison.detail}</p></li>)}</ol>
    </section>
    <section className="dashboard-group"><h3>Pendências de coleta</h3>{data.pending.length ? <ul>{data.pending.map(item => <li key={item.id}>{item.label}</li>)}</ul> : <p>Nenhuma pendência informada para este recorte.</p>}</section>
  </div>;
}
function StatusIcon() { return <svg className="dashboard-status-icon" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v6m0 3v1"/></svg>; }
