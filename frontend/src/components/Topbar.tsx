import { useRef, useState } from 'react';
import { Link } from 'react-router';

export interface TopbarProps {
  apiStatusBadge?: React.ReactNode;
  authorized?: boolean;
}

export function Topbar({ apiStatusBadge, authorized = false }: TopbarProps) {
  const [open, setOpen] = useState(false);
  const toggle = useRef<HTMLButtonElement>(null);
  const close = () => setOpen(false);
  return <header className="topbar" onKeyDown={event => { if (event.key === 'Escape' && open) { close(); toggle.current?.focus(); } }}>
    <div className="wrap">
      <Link to="/" className="brand-logo" aria-label="CarbonTrace — início" onClick={close}>
        <img src="/logo.png" alt="CarbonTrace" className="logo-img" width="112" height="42"/>
      </Link>
      <button ref={toggle} type="button" className="menu-toggle" aria-label={open ? 'Fechar menu' : 'Abrir menu'} aria-expanded={open} aria-controls="main-navigation" onClick={() => setOpen(!open)}>
        <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" aria-hidden="true">{open ? <path d="m6 6 12 12M18 6 6 18"/> : <path d="M4 6h16M4 12h16M4 18h16"/>}</svg>
      </button>
      <nav id="main-navigation" className={`topbar-nav public-nav ${open ? 'is-open' : ''}`} aria-label="Navegação principal">
        <Link to="/#sobre" onClick={close}>O projeto</Link>
        <Link to="/#como-funciona" onClick={close}>Como funciona</Link>
        <Link to="/#equipe" onClick={close}>Equipe</Link>
        <Link className="nav-access" to={authorized ? '/unidades' : '/entrar'} onClick={close}>{authorized ? 'Abrir meu painel' : 'Entrar'} <span aria-hidden="true">↗</span></Link>
        {apiStatusBadge}
      </nav>
    </div>
  </header>;
}
