import { Link, useSearchParams } from 'react-router';
import { Login } from '@/components/Login';

export function AuthPage() {
  const [params] = useSearchParams();
  const initialMode = params.get('modo') === 'cadastro' ? 'signup' : 'login';
  return <div className="wrap auth-layout route-enter">
    <Link className="text-link auth-back" to="/">← Voltar ao início</Link>
    <aside className="auth-intro">
      <h2>Cada registro conta.<br/><span>Cada escolha também.</span></h2>
      <p>Organize suas unidades, registre os consumos e entenda as emissões da sua empresa em um só lugar.</p>
      <div className="auth-note"><span aria-hidden="true">↗</span><p>Um espaço para transformar dados do dia a dia em decisões mais conscientes.</p></div>
    </aside>
    <Login key={initialMode} initialMode={initialMode}/>
  </div>;
}
