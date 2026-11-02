import { Link } from 'react-router';

export interface TopbarProps {
  apiStatusBadge?: React.ReactNode;
  authorized?: boolean;
}

export function Topbar({ apiStatusBadge, authorized = false }: TopbarProps) {
  return (
    <header className="topbar">
      <div className="wrap">
        <Link to="/" className="brand-logo" aria-label="CarbonTrace — início">
          <img src="/logo.png" alt="CarbonTrace" className="logo-img" />
        </Link>
        <nav className="topbar-nav" aria-label="Navegação principal">
          <span className="topbar-caption">Inventário de emissões</span>
          <Link to={authorized ? '/unidades' : '/entrar'}>{authorized ? 'Meu espaço' : 'Acessar plataforma'}</Link>
          {apiStatusBadge}
        </nav>
      </div>
    </header>
  );
}
