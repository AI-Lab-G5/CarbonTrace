import { Link } from 'react-router';
import { useState } from 'react';
import { Reveal } from '@/components/Reveal';
import { TeamCard } from '@/components/TeamCard';
import { team } from '@/data/team';

function PlanetIllustration() {
  return <div className="planet-scene" aria-hidden="true">
    <div className="planet-glow"/><div className="planet-orbit orbit-one"/><div className="planet-orbit orbit-two"/>
    <div className="planet-sphere">
      <svg className="planet-lines" viewBox="0 0 360 360" fill="none"><circle cx="180" cy="180" r="172"/><ellipse cx="180" cy="180" rx="90" ry="172"/><ellipse cx="180" cy="180" rx="36" ry="172"/><ellipse cx="180" cy="180" rx="172" ry="72"/><ellipse cx="180" cy="180" rx="172" ry="130"/><path d="M8 180h344M180 8v344"/></svg>
      <svg className="planet-leaf" viewBox="0 0 140 160" fill="none"><path d="M25 115C-8 63 43 18 122 13c3 75-28 130-82 113" fill="url(#leaf-color)"/><path d="M17 148C37 103 69 68 105 38M46 101l-5-36M69 75l29-3" stroke="#002c1d" strokeWidth="4" strokeLinecap="round"/><defs><linearGradient id="leaf-color" x1="20" y1="130" x2="120" y2="10" gradientUnits="userSpaceOnUse"><stop stopColor="#00b377"/><stop offset="1" stopColor="#a4ffb9"/></linearGradient></defs></svg>
    </div>
    <div className="planet-label label-top"><span className="signal-dot"/>Consciência em cada dado</div>
    <div className="planet-label label-bottom"><span className="planet-co2">CO₂e</span><span>Conhecer.<br/><strong>Para transformar.</strong></span></div>
    <span className="planet-coordinate">DADOS LOCAIS. IMPACTO QUE IMPORTA.</span>
  </div>;
}

const features = [
  { number: '01', title: 'Suas unidades, organizadas.', text: 'Reúna as lojas da sua empresa em um espaço de trabalho e mantenha a coleta conectada a cada unidade.', icon: 'units' },
  { number: '02', title: 'Consumos que contam uma história.', text: 'Registre eletricidade, diesel, gasolina e GLP por mês, com quantidades e unidades de medida compatíveis.', icon: 'energy' },
  { number: '03', title: 'Emissões com uma origem clara.', text: 'Consulte a estimativa em CO₂e e acompanhe a quantidade, a conversão e a versão do fator de cada cálculo.', icon: 'trace' },
] as const;

function FeatureIcon({ kind }: { kind: (typeof features)[number]['icon'] }) {
  return <svg viewBox="0 0 32 32" width="30" height="30" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    {kind === 'units' ? <><path d="M5 28V8l11-4 11 4v20M3 28h26M13 28v-7h6v7"/><path d="M10 11h2m8 0h2m-12 5h2m8 0h2"/></> : kind === 'energy' ? <path d="m18 3-12 16h9l-1 10 12-17h-9l1-9Z"/> : <><circle cx="7" cy="23" r="4"/><circle cx="25" cy="9" r="4"/><path d="M11 23h9a5 5 0 0 0 0-10h-8a5 5 0 0 1 0-10h5M7 19v-4m18 0v3"/></>}
  </svg>;
}

export function HomePage({ authorized = false }: { authorized?: boolean }) {
  const [effectsPaused, setEffectsPaused] = useState(false);
  return <div className={`landing-page ${effectsPaused ? 'effects-paused' : ''}`}>
    <section className="landing-hero wrap" aria-labelledby="home-title">
      <div className="hero-copy">
        <h1 id="home-title">Conheça o impacto.<br/><span>Transforme<br className="hero-line-break"/> o futuro.</span></h1>
        <p className="hero-description">O primeiro passo para reduzir emissões é entender de onde elas vêm. Conecte os consumos da sua rede a uma visão mais consciente do meio ambiente.</p>
        <div className="hero-actions"><Link className="btn" to={authorized ? '/unidades' : '/entrar'}>{authorized ? 'Abrir meu painel' : 'Acessar plataforma'} <span aria-hidden="true">↗</span></Link><Link className="landing-secondary" to="/#sobre">Conhecer o projeto <span aria-hidden="true">↓</span></Link></div>
        <p className="hero-footnote">Inventário de emissões para redes de varejo e franquias.</p>
      </div>
      <div className="hero-art"><PlanetIllustration/><button className="motion-control" type="button" aria-pressed={effectsPaused} onClick={() => setEffectsPaused(!effectsPaused)}>{effectsPaused ? 'Retomar efeitos' : 'Pausar efeitos'} <span aria-hidden="true">{effectsPaused ? '▷' : 'Ⅱ'}</span></button></div>
    </section>

    <div className="source-strip"><div className="wrap"><span>Quatro fontes.<br/><strong>Um olhar mais consciente.</strong></span><ul aria-label="Fontes de consumo contempladas"><li><span aria-hidden="true">↯</span>Eletricidade</li><li><span aria-hidden="true">◈</span>Diesel</li><li><span aria-hidden="true">◈</span>Gasolina</li><li><span aria-hidden="true">◉</span>GLP</li></ul></div></div>

    <section id="sobre" className="wrap landing-section about-section" tabIndex={-1} aria-labelledby="about-title">
      <Reveal><div className="about-grid"><div><h2 id="about-title">Cuidar do amanhã<br/>começa por <span>entender o hoje.</span></h2></div><div className="about-copy"><p>O CarbonTrace é um projeto de tecnologia em desenvolvimento para ajudar redes de varejo e franquias a organizar seus consumos e compreender as emissões de gases de efeito estufa associadas às suas operações.</p><p>Da energia que mantém uma loja funcionando aos combustíveis usados no dia a dia, cada registro ajuda a construir uma visão mais clara do impacto da empresa.</p><div className="about-principle"><span aria-hidden="true">↗</span><p>Dados mais claros.<br/><strong>Escolhas mais conscientes.</strong></p></div></div></div></Reveal>
    </section>

    <section id="como-funciona" className="wrap landing-section how-section" tabIndex={-1} aria-labelledby="how-title">
      <Reveal><div className="landing-section-heading"><div><h2 id="how-title">Um caminho simples.<br/><span>Uma visão mais clara.</span></h2></div><p>Organize, registre e entenda.<br/>Acompanhe a origem de cada resultado.</p></div></Reveal>
      <div className="feature-grid">{features.map(feature => <Reveal key={feature.number}><article className="landing-feature"><div className="feature-top"><FeatureIcon kind={feature.icon}/><span>{feature.number}</span></div><h3>{feature.title}</h3><p>{feature.text}</p></article></Reveal>)}</div>
      <p className="method-note">As estimativas consideram as fontes previstas e os fatores disponíveis para cada período. Fatores preliminares não representam um inventário homologado.</p>
    </section>

    <section id="equipe" className="landing-section team-section" tabIndex={-1} aria-labelledby="team-title"><div className="wrap">
      <Reveal><div className="landing-section-heading"><div><h2 id="team-title">Pessoas por trás<br/><span>de cada conexão.</span></h2></div><p>Uma equipe que une produto, desenvolvimento<br/>e qualidade em torno de uma mesma ideia.</p></div></Reveal>
      <Reveal><ul className="team-grid">{team.map(member => <TeamCard key={member.login} member={member}/>)}</ul></Reveal>
      <p className="team-caption">Conheça os perfis e acompanhe o trabalho da equipe no GitHub.</p>
    </div></section>

    <section className="wrap landing-section access-section" aria-labelledby="access-title"><Reveal><div className="access-panel"><div className="access-copy"><h2 id="access-title">O futuro que queremos<br/>começa com o que<br/><span>fazemos agora.</span></h2><p>Comece pelos dados da sua empresa.<br/>Um registro de cada vez.</p></div><div className="access-card"><span className="access-symbol" aria-hidden="true">↗</span><h3>{authorized ? 'Seu inventário está aqui.' : 'Seu espaço no CarbonTrace.'}</h3><p>{authorized ? 'Continue a coleta e consulte os resultados das suas unidades.' : 'Entre para organizar suas unidades, registrar consumos e consultar suas emissões.'}</p><Link className="btn" to={authorized ? '/unidades' : '/entrar'}>{authorized ? 'Abrir meu painel' : 'Entrar na conta'} <span aria-hidden="true">→</span></Link>{!authorized && <><Link className="access-signup" to="/entrar?modo=cadastro">Primeiro acesso? <strong>Criar conta</strong></Link><p className="access-invite">O acesso às lojas depende de convite da sua empresa.</p></>}</div></div></Reveal></section>
  </div>;
}
