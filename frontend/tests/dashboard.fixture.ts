import type { DashboardView } from '../src/components/dashboard/DashboardPanel';
// Fixtures locais de apresentação; não são respostas de #34/#35.
export const dashboardFixture: DashboardView = {
 context:'Outubro de 2026 · Todas as unidades · Todas as regiões · Snapshot de teste',
 coverage:'3 unidades com coleta; 1 fonte pendente', partial:true, total:'400', median:'100',
 scopes:[{label:'Escopo 1',amount:'200'},{label:'Escopo 2',amount:'200'}],
 regions:[{label:'Norte',amount:'200'},{label:'Sul',amount:'200'}], months:[{label:'2026-10',amount:'400'}],
 units:[
 {id:'c',label:'Loja Sul',amount:'200',comparison:{status:'alert',label:'Desvio de +100%',detail:'Acima da faixa de comparação'}},
 {id:'a',label:'Loja Centro',amount:'100',comparison:{status:'within',label:'Na faixa',detail:'Sem desvio em relação à mediana'}},
 {id:'b',label:'Loja Norte',amount:'100',comparison:{status:'within',label:'Na faixa',detail:'Sem desvio em relação à mediana'}},
 ], pending:[{id:'a-diesel',label:'Loja Centro · diesel · outubro de 2026: coleta ausente'}],
};
