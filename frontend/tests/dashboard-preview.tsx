// Entrada exclusiva do servidor de desenvolvimento; fora do build de produção.
import { useState } from 'react';
import { createRoot } from 'react-dom/client';
import { DashboardFilters, DashboardPanel, type DashboardState, type Selection } from '../src/components/dashboard/DashboardPanel';
import { dashboardFixture } from './dashboard.fixture';
import '../src/index.css';
import '../src/App.css';
import '../src/workspace.css';
export function Preview() {
 const [selection,setSelection]=useState<Selection>({month:'2026-10',unit:'',region:'',snapshot:'test'});
 const [kind,setKind]=useState<DashboardState['kind']>('ready');
 const state:DashboardState=kind==='ready' ? {kind,data:selection.month==='2026-10' ? dashboardFixture : {...dashboardFixture,context:'Setembro de 2026 · cenário sintético',total:'0',median:null,medianReason:'Menos de 3 elegíveis',scopes:[],regions:[],months:[],units:[],pending:[]}} : kind==='error' ? {kind,message:'Não foi possível carregar o consolidado. Seus filtros foram mantidos.'} : kind==='unavailable' ? {kind,reason:'Menos de 3 elegíveis'} : {kind};
 return <main className="wrap"><h1>Dashboard — teste de apresentação</h1><p>Dados sintéticos de apresentação. Os filtros exercitam os controles; os totais são fixtures. Esta página não comprova integração com API ou Firebase.</p><section className="card"><DashboardFilters value={selection} onChange={setSelection} units={[{value:'a',label:'Loja Centro'}]} regions={[{value:'n',label:'Norte'},{value:'s',label:'Sul'}]} snapshots={[{value:'test',label:'Snapshot sintético'}]}/><label>Estado de teste<select value={kind} onChange={e=>setKind(e.target.value as DashboardState['kind'])}>{['ready','loading','error','empty','unavailable'].map(item=><option key={item}>{item}</option>)}</select></label><DashboardPanel state={state} retry={()=>setKind('ready')}/></section></main>;
}
createRoot(document.getElementById('root')!).render(<Preview/>);
