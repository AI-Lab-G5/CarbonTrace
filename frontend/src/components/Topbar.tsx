export interface TopbarProps {
  apiStatusBadge?: React.ReactNode;
}

export function Topbar({ apiStatusBadge }: TopbarProps) {
  return (
    <header className="topbar">
      <div className="wrap">
        <a href="#" className="brand">
          🌱 Carbon<span>Trace</span>
        </a>
        <nav className="topbar-nav" aria-label="Navegação principal">
          <a href="#calculadora">Calculadora</a>
          <a href="#status-api">Status API</a>
          <a href="#como-funciona">Como funciona</a>
          {apiStatusBadge}
        </nav>
      </div>
    </header>
  );
}

