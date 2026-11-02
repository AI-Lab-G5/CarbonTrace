export function Footer() {
  const anoAtual = new Date().getFullYear();

  return (
    <footer className="wrap site-footer">
      <div className="footer-main">
        <div className="footer-about">
          <p className="eyebrow">Nossa origem, nosso propósito</p>
          <h2>Da UnB, <span>com um olhar para o futuro.</span></h2>
          <p>O CarbonTrace é um projeto desenvolvido pela nossa equipe da Universidade de Brasília, no contexto do AI Lab UnB. Unimos tecnologia e consciência ambiental para tornar o impacto de cada consumo mais claro.</p>
        </div>
        <div className="footer-affiliation">
          <p className="footer-affiliation-label">Conhecimento que conecta a nossa equipe</p>
          <div className="institution-logos" role="group" aria-label="Instituições de origem da equipe">
            <figure>
              <div className="institution-logo-frame"><img src="/brand/unb.png" alt="Logo da UnB" width="300" height="150" loading="lazy" decoding="async"/></div>
              <figcaption>Universidade de Brasília</figcaption>
            </figure>
            <figure>
              <div className="institution-logo-frame"><div className="ai-lab-logo">
                <img src="/brand/ai-lab-unb.png" alt="Logo do AI Lab UnB" width="400" height="138" loading="lazy" decoding="async"/>
                <img className="ai-lab-wordmark" src="/brand/ai-lab-unb.png" alt="" aria-hidden="true" width="400" height="138" loading="lazy" decoding="async"/>
              </div></div>
              <figcaption>AI Lab UnB</figcaption>
            </figure>
          </div>
        </div>
      </div>
      <div className="footer-bottom"><p>Demonstração — CarbonTrace · {anoAtual}</p><p>Da coleta à consciência ambiental.</p></div>
    </footer>
  );
}

