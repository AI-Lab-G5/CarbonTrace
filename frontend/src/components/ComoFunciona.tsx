export function ComoFunciona() {
  return (
    <section id="como-funciona" className="wrap" aria-labelledby="como-funciona-heading">
      <h2 id="como-funciona-heading">Como funciona</h2>
      <div className="cols">
        <div className="col">
          <h3>1. Estimativa Didática</h3>
          <p>
            Cálculo instantâneo baseado em fatores de conversão médios para energia elétrica, diesel e resíduos.
          </p>
        </div>
        <div className="col">
          <h3>2. NGINX & Docker</h3>
          <p>
            Arquitetura em containers multi-stage com Nginx servindo assets estáticos e atuando como proxy reverso para o backend.
          </p>
        </div>
        <div className="col">
          <h3>3. Verificação de Saúde</h3>
          <p>
            Conectividade contínua com a API FastAPI através de <code>/api/health</code> na porta 3000 do host.
          </p>
        </div>
      </div>
    </section>
  );
}

