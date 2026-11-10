# Retomada J1–J4 — CP3 (frontend #36)

Data: 10/11/2026. Branch: `feat/front-dashboard-j1-j4-cp3`.
Base: `dce2a46`, mesma revisão de `origin/dev` no início. Branch remota existente reutilizada.
Esta é uma entrega parcial independente. Issue não encerrada; CP2/CP3 não declarados aceitos.

## Entregue agora

- `/dashboard` protegida pela sessão existente, com retorno para login/onboarding. Mostra indisponibilidade e caminhos reais para Unidades/Consumos. Não chama `/v1/consolidado` nem mostra fixtures aos usuários.
- `components/dashboard/DashboardPanel.tsx`: componentes puros para filtros controlados, carregamento/vazio/erro/indisponibilidade, totais por escopo/região/mês, ranking, mediana, comparação e pendências. Estilo preto/verde herdado.
- `Selection`, `DashboardView`, `Comparison` e `DashboardState` são modelos LOCAIS de apresentação, não contrato HTTP aprovado. Sem cálculo de total/mediana/desvio no cliente. Valores recebidos são formatados em três casas HALF_EVEN com o utilitário decimal textual existente.
- Trocar competência limpa snapshot; trocar região limpa unidade no componente de filtro. Combinações válidas, recorte dos totais e elegibilidade dependem da especificação final. Os controles só aparecem no ensaio isolado, não na rota sem integração.
- `apiConfig.ts`: base URL centralizada, normalização de barra final e leitura/sonda com limite de 65 segundos. Escritas mantêm 15 segundos, sem retry automático. Cancelamento existente preservado. Nenhum ambiente externo alterado.
- `.env.example` explica configuração de build e diferença entre proxy local e URL Render. O Dockerfile ainda usa configuração do contexto de build; não há pipeline público pronto nem argumento Docker novo validado.
- Testes de regressão existentes preservados. Não houve nova implementação de J1 porque o contrato atual ainda não entrega código/edição/desativação/fontes esperadas/autoria/data.

## Inspeção das dependências

Consultadas por leitura na API pública do GitHub em 10/11: [#34](https://github.com/AI-Lab-G5/CarbonTrace/issues/34), [#35](https://github.com/AI-Lab-G5/CarbonTrace/issues/35) e [#37](https://github.com/AI-Lab-G5/CarbonTrace/issues/37), todas abertas na consulta. Estado aberto não prova ausência de trabalho em outras branches; o código avaliado é a base acima.

`backend/app/routers/consolidado.py` recebe somente competência, varre consumos, soma por unidade e calcula mediana a cada leitura. Não entrega snapshot persistido, região, escopo filtrável, cursor ou pendências. Não foi usado como substituto da API J4. `Unidade` ainda contém id/nome/cidade/UF; consumo não fornece autoria/data. Nenhuma mudança de backend realizada.

Foram lidos o escopo fornecido, código/contratos atuais, registro de entrega J1–J3, rastreabilidade e FinOps. O PDF do Guia CP3 e o documento externo completo CT-M08/CT-M12 não foram obtidos nesta etapa; as regras aplicadas são as transcritas nas issues. Conferir os originais com PO/TL na retomada.

## Critério → resultado desta etapa

| CA | Situação | Evidência | Falta para aceite |
|---|---|---|---|
| 01 | Dependente; regressão frontend testada | Suíte existente de API/auth/jornadas; rota protegida | Operações/metadados #35, contrato #34 e J1–J3 públicos #37 |
| 02 | Apresentação parcialmente preparada | dashboard-panel.spec.tsx e dashboard.visual.spec.ts | Cliente/adaptador real, região/snapshot/escopo e cursores 20/100 #34/#35 |
| 03 | Apresentação testada; domínio não comprovado | Fixture 100/100/200, total 400, regiões 200/200, mediana 100; total preservado com só uma linha | Seed determinístico real 3 unidades/2 regiões/2 meses, frações, snapshots e isolamento #35 |
| 04 | Apresentação testada | Zero x ausência, parcial, ±50% sem alerta fornecido como status, mediana zero/menos de 3 | Regra real de domínio/eligibilidade/ranking e fonte esperada #34/#35 |
| 05 | Local parcialmente comprovado | Leitura >10s e timeout65s com relógio controlado; testes/capturas desktop e celular | Cold start real após dormir, tempo observado e fluxo público #37 |
| 06 | Configuração local preparada | Base centralizada e exemplo de variáveis | Build real com config Firebase/Render, CORS, preview de PR, produção e provas #34/#37 |

## Contrato a receber e ações de retomada

| Insumo / dúvida concreta | Dono por issue | Ação do frontend quando disponível |
|---|---|---|
| Rotas/métodos/JSON de código único, editar/desativar loja e fontes esperadas; estrutura de 409; UID/data no consumo | Backend #35, alinhamento TL #34 | Integrar formulários e metadados sem recriar histórico; testar 409, desativação e preservação dos campos |
| Contrato OpenAPI do dashboard: região (incluindo sem região), escopo, competência, snapshot, filtros e erros | TL #34 + Backend #35 | Criar DTOs reais/adaptador para DashboardView e ajustar Selection; não tratar o modelo local como contrato |
| Totais e mediana do snapshot autorizado completo, paginação20/100 e semântica de recorte | #34/#35 | Conectar filtros/página, limpar cursor, abortar consultas e descartar respostas antigas por geração/empresa; testar total independente da página |
| Snapshot imutável, momento de produção, fator/versão, origem regional preservada | #35 | Mostrar identificação/metadados; seleção consistente; recuperar após recarga e testar snapshot anterior |
| Completude, revisões válidas, unidade/fonte desativada e ranking com desempate por código | #35, decisão #34 | Mapear parcialidade/pendências/status sem calcular mediana/desvio no cliente |
| Seed determinístico com 3 lojas/2 regiões/2 meses, 400/200/200/100 e frações | #35, cenários PO #33 | Rodar E2E real; conferir números exibidos; mês/filtro/página/empresa sem vazamento |
| URL Render, projeto Spark/Auth real, domínios autorizados, CORS produção/preview e config de build | #34/#37 | Validar login/logout/onboarding e J1–J4 em pelo menos um preview e em produção; API pública sem Auth Emulator |
| PR/CI/preview publicado, deploy e smoke com versão identificada | #37 | Vincular URL, SHA, CI e data aos testes manuais curtos; revisão independente |
| Inicialização Render após dormir e prazo de espera real | #37 | Medir tempo observado; conferir espera/erro/retry sem apagar formulário; não afirmar meta Cloud Run10s |
| ADR/adaptações aprovadas, prova de exceções pelo professor e runbook rollback | TL #34, PO #33 e DevOps #37 | Vincular provas; não criar runbook fictício nem executar rollback nesta etapa |

Exemplo de pergunta pendente: qual requisição consulta o snapshot escolhido com região/unidade/escopo e cursor, e quais campos identificam o recorte do total versus o da página? Não há payload HTTP novo proposto aqui: aguardar o contrato para não inventá-lo.

## Encaixe técnico e roteiro

1. Atualizar esta branch a partir da dev preservando mudanças; conferir contratos #34/#35 entregues e decisões PO.
2. Criar camada de consulta real usando `request`/ID token, cancelamento e guarda de geração para mudanças de filtros e empresa. Não repetir escritas automaticamente.
3. Integrar as operações pendentes de J1; mostrar autoria/data reais em `ResultadoConsumo`.
4. Substituir o conteúdo de `DashboardPage` por filtros e painel ligados à API. Não importar fixtures. Confirmar recorte total/mediana, cursor padrão20/máximo100, unidade sem região e snapshot por competência.
5. Testar respostas atrasadas/invertidas, troca de empresa/logout, cursor inválido, 401/403/409/422, recarga e dados históricos. Os testes puros atuais não comprovam isolamento da API nem concorrência de consultas J4.
6. Executar seed determinístico e E2E real de J1–J4 no Compose, incluindo 400/200/200/100, frações, ±50% exatos e >50%, zero, ausência e elegibilidade insuficiente.
7. Com #37, validar preview e produção, login real, CORS e cold start após dormir; guardar tempos/URLs/SHA/CI/data. Suítes pesadas continuam locais.
8. Solicitar revisão por outra pessoa e aceite PO #33. Atualizar matriz/bugs por reteste, sem retroagir aprovação. J5 e ensaio de rollback ficam fora.

## Evidências locais e reprodução

Na pasta frontend:

```powershell
npm test
npm run lint
npm run build
npm run test:ui
```

Ensaio de componentes: `npm run dev -- --host 127.0.0.1 --port 3100` e abrir `/tests/dashboard-preview.html`. Página identificada como sintética, fora do build Vite de produção (entrada única index.html). Não é rota da aplicação publicada. Filtros exercitam estado controlado; totais são fixtures, não dados filtrados de uma API. Não publicar essa página como produto.

Capturas: `evidencias/cp3/dashboard-sintetico-1440.png` e `dashboard-sintetico-390.png`, inspecionadas visualmente. Campos/valores legíveis e sem overflow horizontal nesses tamanhos. Teste de teclado usa tabulação entre seletores; o campo month possui segmentos nativos do navegador.

Resultados finais desta etapa:
- npm test: 65 Vitest + 2 testes decimais aprovados.
- Lint e build: aprovados após correção do export da entrada isolada de teste.
- Navegador: 8 cenários existentes aprovados; 2 novos cenários sintéticos J4 aprovados após corrigir a expectativa de tabulação do campo month. Proteção da rota J4 verificada em teste adicional.
- Sonda/API: resposta de 11s aceita; aos10s mantém espera; aos65s erro recuperável; escrita15s sem retry.
- Detector mecânico da skill Impeccable nos componentes J4: nenhum achado. Não equivale a auditoria completa de acessibilidade.
- E2E Compose real não reexecutado: projeto carbontrace-front-test sem containers ativos nesta sessão. Backend/Rules não alterados. Provas antigas J1–J3 não são prova da integração nova.
- CI remoto, revisão independente, preview, produção, cold start real e aceite PO: não executados nesta etapa. Sem push/deploy/PR publicado.

Falhas intermediárias de seletor duplicado, diretório da execução Vitest, lint da página de ensaio e tabulação foram corrigidas e retestadas; não foram contadas como aprovação.

## Histórico e documentos anteriores

`entrega-j1-j3.md` conserva números e limitações da revisão antiga (13 testes e Rules ainda permissivas). A dev já contém deny-all e registros QA posteriores; este relatório não apaga o histórico nem certifica que CP2 foi aceito. A rastreabilidade antiga avalia outra revisão. Nenhuma aprovação CI/PO nova é inferida desses textos.

## Commits e proposta de PR em rascunho

- 81c90dc: rota protegida e indisponibilidade J4.
- e8cfa61: componentes de agregados/comparação e testes de apresentação.
- 3e9c1b9: URL centralizada, leitura65s e escrita15s.
- Os commits posteriores de ensaio/evidências/documentação podem ser identificados pelo log desta branch; sem ciclo de atualização do próprio hash.

Título sugerido: `feat(frontend): preparar apresentação J4 e espera de inicialização — CP3 parcial`.

Descrição sugerida: Prepara navegação protegida e componentes de dashboard com apresentação de totais/ranking/completude, mantendo a rota sem números até o contrato J4 estar entregue. Centraliza URL e amplia a espera de leitura/sondas. Testes e capturas locais anexados; dados de J4 são exclusivamente sintéticos no ensaio. A issue #36 permanece aberta: integração #34/#35 e validação pública #37 pendentes. Revisão/CI remoto e aceite PO ainda necessários. Não autoriza publicação desta etapa como J4 concluída.
