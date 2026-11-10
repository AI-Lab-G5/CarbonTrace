import { Link } from 'react-router';

export function DashboardPage() {
  return <section className="card" aria-labelledby="dashboard-pending">
    <h2 id="dashboard-pending">Consolidado ainda não disponível</h2>
    <p role="status">A visão da rede estará disponível quando a integração dos dados consolidados estiver concluída.</p>
    <p>Você pode continuar cadastrando lojas e registrando os consumos mensais.</p>
    <div className="auth-actions"><Link className="btn" to="/consumos">Registrar consumo</Link><Link className="btn ghost" to="/unidades">Consultar unidades</Link></div>
  </section>;
}
