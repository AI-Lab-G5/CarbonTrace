import { useEffect, useRef } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router';
import type { User } from 'firebase/auth';
import { useJornadas } from '@/hooks/useJornadas';
import { FormFeedback } from '@/components/FormFeedback';

export function Jornadas({ user, expired }: { user: User; expired: () => void }) {
  const jornadas = useJornadas(user, expired);
  const { pathname } = useLocation();
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => { heading.current?.focus(); }, [pathname]);
  return <div className="wrap workspace" id="jornadas">
    <aside className="workspace-sidebar">
      <p className="eyebrow">Seu inventário</p>
      <nav aria-label="Área de trabalho" className="workspace-nav">
        <NavLink to="/unidades"><span aria-hidden="true">01</span><div>Unidades<small>Lojas da sua empresa</small></div></NavLink>
        <NavLink to="/consumos"><span aria-hidden="true">02</span><div>Consumos<small>Coleta e resultados</small></div></NavLink>
      <NavLink to="/dashboard"><div>Dashboard<small>Consolidado da rede</small></div></NavLink>
      </nav>
      <p className="sidebar-note">Cada consumo registrado torna suas emissões mais visíveis.</p>
    </aside>
    <div className="workspace-content">
      <header className="page-heading">
        <h1 ref={heading} tabIndex={-1}>{pathname === '/dashboard' ? 'Dashboard da rede' : pathname === '/unidades' ? 'Unidades da empresa' : 'Coleta mensal'}</h1>
        <p>{pathname === '/dashboard' ? 'Consulte o panorama das emissões e as pendências de coleta.' : pathname === '/unidades' ? 'Organize as lojas que fazem parte do seu inventário.' : 'Registre os consumos e consulte a origem de cada cálculo.'}</p>
      </header>
      {jornadas.message && <p className="feedback success-feedback" role="status">✓ {jornadas.message}</p>}
      <FormFeedback message={jornadas.error} focus retry={jornadas.retry} retryLabel="Consultar novamente" disabled={jornadas.busy}/>
      <div key={pathname} className="route-enter"><Outlet context={jornadas}/></div>
    </div>
  </div>;
}
