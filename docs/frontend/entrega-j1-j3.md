# Entrega parcial de Frontend J1–J3

Branch: `feat/front-integracao-j1-j3`. Referência de trabalho: 01/11/2026.

Implementados cliente HTTP Bearer, login/logout Firebase, listagem/cadastro/consulta
de unidades, catálogo por competência, coleta decimal, consulta paginada, origem do
resultado e reprodução pela API. O tema preto/verde e a estrutura React foram mantidos.
Não há aceite integral nem prova ponta a ponta nesta entrega.

## Verificações

- `npm ci`: executado com sucesso.
- `npm run build`: aprovado (TypeScript e Vite).
- `npm run lint`: aprovado na primeira execução; repetir na revisão final.
- `node --experimental-strip-types --test frontend/tests/decimal.test.ts`: 2 aprovados.
- `git diff --check`: aprovado.
- `docker info`: falhou por ausência de dockerDesktopLinuxEngine. Iniciar Docker Desktop
  não disponibilizou o engine. Compose limpo, autenticação real, Rules, isolamento,
  captura visual e E2E: **não executados**.
- CI remoto, revisão independente e aceite PO: não comprovados.
- npm reportou 16 vulnerabilidades (12 moderadas, 4 altas) após instalação; triagem
  pendente, sem atualização forçada de versões.

Os testes novos verificam zero/ausência/inválidos e precisão/formatação. Não cobrem
componentes, HTTP, Auth ou Firestore. A suíte histórica da calculadora está preservada,
mas não faz parte do script principal nem comprova as novas jornadas.

## Issue #9

| CA | Entrega / evidência | Situação |
|---|---|---|
| 01 | Login/logout e token SDK implementados; build aprovado | Parcial, Auth real não executado |
| 02 | Cadastro/consulta paginada e catálogo integrados | Parcial; código único/vínculos ausentes no backend |
| 03 | Payload textual, validações e dois testes decimais | Parcial; limites/API real sem prova |
| 04 | Mensagens, loading, vazio, erro, retry e sucesso | Parcial; cobertura de componentes e catálogo loading a completar |
| 05 | Labels, foco, fieldset e mensagens textuais | Parcial; conferência visual/teclado não executada |
| 06 | Consulta inicial busca API após recarga | Parcial; persistência E2E não comprovada |

## Issue #19

| CA | Entrega / evidência | Situação |
|---|---|---|
| 01 | Resultado salvo e versão explícita, metadados da versão original | Parcial; prova real pendente |
| 02 | Fluxo conectado e leitura após montagem | Bloqueado para demonstração por Docker/ambiente |
| 03 | Tratamento HTTP e healthz/readyz | Parcial; testes de indisponibilidade pendentes |
| 04 | Decimal textual e HALF_EVEN testados; campos rotulados | Parcial; acessibilidade manual pendente |
| 05 | Recálculo API por ID e versão original | Não validado com Backend/QA |
| 06 | Este material técnico está preparado | Parcial; evidência integrada, revisão e entrega ao PO/QA pendentes |

## Dependências e limites

Backend #11/#21: `POST /v1/unidades` aceita nome/cidade/uf, sem código único nem
fontes por loja. Contrato esperado: código com 409 por duplicidade no tenant e vínculos
persistidos. Exemplo proposto, não executado: `{ "codigo": "CENTRO", "nome": "Loja Centro" }`.

`PUT /v1/consumos` usa set e sobrescreve a chave loja/mês/fonte. A interface consulta
antes e impede duplicata conhecida, mas não resolve concorrência. Backend precisa
criação atômica/conflito 409. Autoria e datas também faltam no modelo de resposta.
Nenhuma requisição de integração foi executada nesta sessão; estes achados são do código.

DevOps #13/TL #18: alinhar projeto Auth/Firestore/backend/frontend em demo-carbontrace,
preparar contas/catalogo reproduzíveis e fechar Rules. O navegador deve acessar Auth
em 127.0.0.1:9099; nomes de serviço Docker são internos. Rules atuais permitem acessos
incompatíveis com deny-all. QA #24 deve testar cada rota protegida com os quatro casos
pedidos e acesso direto ao banco. Catálogo global exige enquadramento próprio do tenant.

TL/PO: confirmar tetos, faixa de competência e arredondamento por lançamento.
A UI não refaz o motor nem fabrica metadados. Código/vínculos, proteção de concorrência,
Rules e autoria continuam pendentes. Meta de 27 commits era sugestiva; etapas sem
validação real não foram apresentadas como concluídas.

## Reprodução e roteiro pendente

1. Disponibilizar Docker Engine; subir Compose isolado com projeto Firebase alinhado.
2. Preparar contas de duas empresas e catálogo pelo processo acordado com DevOps.
3. No frontend: `npm ci`, `npm test`, `npm run lint`, `npm run build`, `npm run dev`.
4. Entrar com funcionário A; cadastrar e consultar loja.
5. Registrar eletricidade, 2025-10, quantidade textual 1, medida MWh.
6. Conferir 1.000 kWh, fator preliminar v1 0.0385 e 38,500 kgCO2e.
7. Recarregar, abrir resultado e conferir recálculo com v1 mesmo com v2 disponível.
8. Testar entrada inválida sem gravação, indisponibilidade, logout e tentativa entre empresas.

Variáveis em `frontend/.env.example` são resolvidas no build. O Compose padrão usa
os defaults locais; customização exige fornecer variáveis ao build e reconstruir imagem.

## Commits

```text
b6d1c48 docs(frontend): documentar configuração da integração local
ff778fc ci(frontend): executar testes decimais junto do lint
a1ee04e fix(frontend): impedir troca de contexto durante operações
e53bf12 fix(frontend): distinguir saúde e prontidão do backend
59d16b6 test(frontend): validar decimais e configurar Firebase SDK
352d264 feat(frontend): conectar unidades coleta e resultados à API
be37933 feat(frontend): preparar login individual no Auth Emulator
791445b feat(frontend): validar e apresentar decimais sem ponto flutuante
e7eab83 feat(frontend): centralizar transporte autenticado e erros HTTP
21cbb74 fix(frontend): consultar a sonda healthz implementada
507daf5 refactor(frontend): definir tipos do contrato real
```
