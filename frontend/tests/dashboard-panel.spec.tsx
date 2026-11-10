import { fireEvent, render, screen } from '@testing-library/react';
import { expect, test, vi } from 'vitest';
import { DashboardFilters, DashboardPanel } from '../src/components/dashboard/DashboardPanel';
import { dashboardFixture as data } from './dashboard.fixture';

test('mostra agregados recebidos mesmo com apenas uma linha visível',()=>{
 render(<DashboardPanel state={{kind:'ready',data:{...data,units:data.units.slice(0,1)}}} retry={vi.fn()}/>);
 expect(screen.getAllByText('400,000 kgCO₂e')).toHaveLength(2);
 expect(screen.getByText('100,000 kgCO₂e')).toBeVisible();
 expect(screen.getByRole('status')).toHaveTextContent('Resultado parcial');
 for(const name of ['Por escopo','Por região','Por mês']) expect(screen.getByRole('heading',{name})).toBeVisible();
 expect(screen.getByText(data.pending[0].label)).toBeVisible();
});
test('zero não vira coleta ausente e estados de comparação vêm dos dados',()=>{
 render(<DashboardPanel state={{kind:'ready',data:{...data,median:null,medianReason:'Mediana zero',units:[
 {...data.units[0],amount:'0',comparison:{status:'unavailable',label:'Mediana zero',detail:'Sem base para comparação'}},
 {...data.units[1],amount:null},
 ]}}} retry={vi.fn()}/>);
 expect(screen.getByText('0,000 kgCO₂e')).toBeVisible();
 expect(screen.getByText('Coleta ausente')).toBeVisible();
 expect(screen.getByText('Indisponível: Mediana zero')).toBeVisible();
});
test.each(['+50%','-50%'])('fronteira %s é exibida sem alerta quando informada pelo domínio', deviation=>{
 render(<DashboardPanel state={{kind:'ready',data:{...data,units:[{...data.units[0],comparison:{status:'within',label:deviation,detail:'Limite exato'}}]}}} retry={vi.fn()}/>);
 expect(screen.getByText(`Sem alerta: ${deviation} — Limite exato`)).toBeVisible();
});
test.each(['Menos de 3 elegíveis','Mediana zero'])('explica indisponibilidade: %s',reason=>{
 render(<DashboardPanel state={{kind:'unavailable',reason}} retry={vi.fn()}/>);
 expect(screen.getByRole('status')).toHaveTextContent(reason);
});
test('erro permite nova tentativa e vazio/carregamento têm mensagens distintas',()=>{
 const retry=vi.fn(); const view=render(<DashboardPanel state={{kind:'error',message:'Consulta indisponível'}} retry={retry}/>);
 fireEvent.click(screen.getByRole('button',{name:'Tentar novamente'})); expect(retry).toHaveBeenCalledOnce();
 view.rerender(<DashboardPanel state={{kind:'loading'}} retry={retry}/>); expect(screen.getByRole('status')).toHaveTextContent('um minuto');
 view.rerender(<DashboardPanel state={{kind:'empty'}} retry={retry}/>); expect(screen.getByRole('status')).toHaveTextContent('Nenhum consolidado');
});
test('filtros controlados notificam seleção sem fazer chamada HTTP',()=>{
 const change=vi.fn(); render(<DashboardFilters value={{month:'2026-10',unit:'a',region:'n',snapshot:'s'}} onChange={change} units={[{value:'a',label:'Centro'}]} regions={[{value:'n',label:'Norte'},{value:'s',label:'Sul'}]} snapshots={[{value:'s',label:'Fechamento'}]}/>);
 fireEvent.change(screen.getByLabelText('Competência'),{target:{value:'2026-09'}});
 expect(change).toHaveBeenLastCalledWith({month:'2026-09',unit:'a',region:'n',snapshot:''});
 fireEvent.change(screen.getByLabelText('Região'),{target:{value:'s'}});
 expect(change).toHaveBeenLastCalledWith({month:'2026-10',unit:'',region:'s',snapshot:'s'});
});

test('exibe o cenário 100/100/200, regiões 200/200 e total 400 sem somar linhas',()=>{
 render(<DashboardPanel state={{kind:'ready',data}} retry={vi.fn()}/>);
 const total=screen.getByText('Total do recorte').parentElement!;
 expect(total).toHaveTextContent('400,000 kgCO₂e');
 expect(screen.getByText('Mediana').parentElement!).toHaveTextContent('100,000 kgCO₂e');
 const ranking=document.querySelector('ol')!;
 expect(ranking).toHaveTextContent('Loja Sul200,000 kgCO₂e');
 expect(ranking).toHaveTextContent('Loja Centro100,000 kgCO₂e');
 expect(ranking).toHaveTextContent('Loja Norte100,000 kgCO₂e');
 for(const region of ['Norte','Sul']) expect(screen.getByText(region).parentElement!).toHaveTextContent('200,000 kgCO₂e');
});
