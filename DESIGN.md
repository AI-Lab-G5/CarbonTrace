---
name: CarbonTrace
description: Consciência em cada dado — tecnologia ambiental em preto e verde.
colors:
  accent: "#00e599"
  accent-dark: "#00b377"
  accent-hover: "#33ecad"
  bg: "#000000"
  bg-soft: "#0e0e0e"
  card: "#141414"
  line: "#262626"
  control-border: "#626f66"
  control-border-hover: "#84968b"
  text: "#f3f4f6"
  muted: "#9ca3af"
  landing-text-muted: "#9eafa4"
  landing-caption: "#8d9b92"
  landing-border: "#243329"
  selected-bg: "#0b2119"
  selected-border: "#174d3b"
  institution-bg: "#0d1510"
  institution-border: "#26382d"
  topbar-bg: "rgba(0, 0, 0, 0.88)"
  status-loading: "#60a5fa"
  status-loading-bg: "#0f172a"
  status-loading-border: "#1e3a8a"
  status-success: "#00e599"
  status-success-bg: "#052e16"
  status-success-border: "#047857"
  status-error: "#f87171"
  status-error-bg: "#450a0a"
  status-error-border: "#991b1b"
  google-bg: "#131314"
  google-text: "#e3e3e3"
  google-border: "#8e918f"
  google-hover: "#232325"
typography:
  display-max:
    fontFamily: '"Segoe UI", system-ui, -apple-system, Roboto, Arial, sans-serif'
    fontSize: "5rem"
    fontWeight: 650
    lineHeight: 1.06
    letterSpacing: "-0.035em"
  headline-max:
    fontFamily: '"Segoe UI", system-ui, -apple-system, Roboto, Arial, sans-serif'
    fontSize: "3.2rem"
    fontWeight: 650
    lineHeight: 1.12
    letterSpacing: "-0.035em"
  workspace-title-max:
    fontFamily: '"Segoe UI", system-ui, -apple-system, Roboto, Arial, sans-serif'
    fontSize: "2.3rem"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "-0.03em"
  body:
    fontFamily: '"Segoe UI", system-ui, -apple-system, Roboto, Arial, sans-serif'
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.55
  body-copy:
    fontFamily: '"Segoe UI", system-ui, -apple-system, Roboto, Arial, sans-serif'
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.8
  field-label:
    fontFamily: '"Segoe UI", system-ui, -apple-system, Roboto, Arial, sans-serif'
    fontSize: "0.88rem"
    fontWeight: 500
    lineHeight: 1.55
  action:
    fontFamily: '"Segoe UI", system-ui, -apple-system, Roboto, Arial, sans-serif'
    fontSize: "0.95rem"
    fontWeight: 700
  landing-action:
    fontFamily: '"Segoe UI", system-ui, -apple-system, Roboto, Arial, sans-serif'
    fontSize: "0.95rem"
    fontWeight: 650
    lineHeight: 1.55
  eyebrow:
    fontFamily: '"Segoe UI", system-ui, -apple-system, Roboto, Arial, sans-serif'
    fontSize: "0.7rem"
    fontWeight: 700
    letterSpacing: "0.12em"
  google-action:
    fontFamily: '"Google Sans Button", Arial, sans-serif'
    fontSize: "14px"
    fontWeight: 500
    lineHeight: "20px"
rounded:
  nav-action: "6px"
  landing-action: "8px"
  field: "10px"
  navigation: "12px"
  card: "14px"
  access-panel: "20px"
  pill: "999px"
  badge: "9999px"
spacing:
  micro: "0.25rem"
  compact: "0.5rem"
  small: "0.75rem"
  base: "1rem"
  medium: "1.25rem"
  large: "1.5rem"
  card: "1.75rem"
  group: "2rem"
  workspace-gap: "2.5rem"
  section-mobile: "3.5rem"
  section-desktop: "6rem"
components:
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.bg}"
    typography: "{typography.action}"
    rounded: "{rounded.pill}"
    padding: "0.78rem 1.5rem"
  button-primary-hover:
    backgroundColor: "{colors.accent-hover}"
    textColor: "{colors.bg}"
    rounded: "{rounded.pill}"
    padding: "0.78rem 1.5rem"
  button-landing:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.bg}"
    typography: "{typography.landing-action}"
    rounded: "{rounded.landing-action}"
    padding: "0.9rem 1.2rem"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.muted}"
    typography: "{typography.action}"
    rounded: "{rounded.pill}"
    padding: "0.78rem 1.5rem"
  button-google:
    backgroundColor: "{colors.google-bg}"
    textColor: "{colors.google-text}"
    typography: "{typography.google-action}"
    rounded: "{rounded.pill}"
    padding: "10px 12px"
  input:
    backgroundColor: "{colors.bg-soft}"
    textColor: "{colors.text}"
    rounded: "{rounded.field}"
    padding: "0.7rem 0.8rem"
  card:
    backgroundColor: "{colors.card}"
    textColor: "{colors.text}"
    rounded: "{rounded.card}"
    padding: "{spacing.card}"
  nav-selected:
    backgroundColor: "{colors.selected-bg}"
    textColor: "{colors.accent}"
    rounded: "{rounded.navigation}"
    padding: "0.9rem 1rem"
  badge-success:
    backgroundColor: "{colors.status-success-bg}"
    textColor: "{colors.status-success}"
    rounded: "{rounded.badge}"
    padding: "0.25rem 0.625rem"
---

# Design System: CarbonTrace

## Overview

**Creative North Star: "Consciência em cada dado"**

A direção verbal vem da própria interface aprovada: tecnologia ambiental com uma presença escura, clara nas ações e humana na apresentação da equipe. O preto organiza o espaço; o verde concentra as chamadas, o foco e os destaques. A esfera com folha conecta visualmente dados e meio ambiente. Esta documentação captura o sistema existente, sem propor uma nova identidade.

A apresentação pública usa títulos expressivos, respiro e ilustração. As telas de trabalho usam a mesma paleta com cards, formulários e hierarquia orientada à coleta e consulta. Essa diferença de densidade é intencional; não transforma o layout de uma página em regra de todas as telas.

Fotografias, nomes e links da equipe preservam a dimensão humana. As marcas da UnB e do AI Lab UnB identificam a origem da equipe. O Google mantém sua identidade própria dentro da variante escura. O painel claro para as instituições foi explicitamente substituído pelo rodapé escuro, com o texto “.lab” branco e o símbolo “A” colorido.

**Key Characteristics:**

- Preto como base, verde como destaque e superfícies escuras com diferenças tonais sutis.
- Tipografia de sistema, títulos de abertura expressivos e informações operacionais mais compactas.
- Cards de cantos suaves, ações de trabalho em cápsula e chamadas públicas com cantos discretos.
- Movimento com pausa e preferência de movimento reduzido respeitada.
- Equipe real, origem acadêmica visível e marcas externas reconhecíveis.

**Escopo e fontes.** Captura inicial em 03/11/2026, atualizada após o refinamento de 04/11/2026, a partir de `frontend/src/index.css`, `App.css`, `workspace.css`, `landing.css` e dos componentes renderizados. A ordem efetiva é: estilos globais, componentes, área de trabalho e página pública. A largura atual do container vem da sobrescrita em `workspace.css`. O código possui tokens semânticos compartilhados para controles, texto de apoio e superfícies selecionadas; os nomes normalizados deste documento também registram medidas existentes.

**Estado da captura.** Os tokens registram a implementação atual. O refinamento corrigiu contraste dos campos e placeholders, textos auxiliares funcionais, alvos de toque, hierarquia do acesso móvel e recuperação dos formulários. A documentação não representa uma certificação de acessibilidade; as limitações remanescentes estão no fim do arquivo.

## Colors

Uma paleta de preto, cinzas e verdes profundos sustenta um único acento verde vivo. Os valores canônicos estão no frontmatter; as descrições abaixo explicam seu uso.

### Primary

- **Verde de consciência — `accent`:** ações principais, foco, navegação selecionada, números de emissão e ênfases dos títulos.
- **Verde profundo — `accent-dark`:** apoio ao acento em barras e indicadores.
- **Verde de interação — `accent-hover`:** resposta visual dos botões principais.

### Neutral

- **Preto de base — `bg`:** fundo integral e texto sobre o botão verde.
- **Preto suave — `bg-soft`:** campos, conteúdo recolhível e áreas internas de suporte.
- **Grafite de superfície — `card`:** base dos cards; algumas áreas recebem gradiente verde-escuro por cima.
- **Linha de grafite — `line`:** bordas de superfícies e divisórias discretas, sem servir como único indicador de um campo.
- **Contorno de controle — `control-border` e `control-border-hover`:** limites distinguíveis dos campos e ações secundárias, com reforço de interação. Placeholders usam o cinza auxiliar, sem opacidade reduzida.
- **Branco de leitura — `text`:** títulos e informação prioritária.
- **Cinza auxiliar — `muted`:** rótulos e informações secundárias na área de trabalho.
- **Cinzas esverdeados — `landing-text-muted` e `landing-caption`:** apoio editorial na página pública e no rodapé.
- **Verde de seleção — `selected-bg` e `selected-border`:** navegação ativa e confirmações contextuais.
- **Superfície institucional — `institution-bg` e `institution-border`:** apresentação escura das logos de origem da equipe.
- **Preto translúcido — `topbar-bg`:** barra superior fixa, com desfoque do conteúdo ao fundo.

### Estados e exceções de marca

- `status-loading*` usa azul para carregamento; `status-success*` usa verde; `status-error*` usa vermelho. A informação também possui texto ou ícone.
- `google-*` documenta a variante escura do acesso Google. A fonte Google Sans Button e o “G” colorido são exclusivos desse controle.
- As cores das fotos e dos símbolos institucionais não são novos acentos de interface. Preservar os assets locais e as proporções das marcas.

**The Black and Green Rule.** Preservar a base preta e o acento verde ao ampliar a interface. Não introduzir uma nova paleta de marca como efeito colateral de um refinamento.

**The Brand Exception Rule.** Manter as cores de identidade de Google, UnB e AI Lab UnB. No rodapé, a adaptação branca se aplica ao texto “.lab”; o símbolo “A” conserva suas cores.

## Typography

**Display Font:** a mesma pilha de sistema utilizada no corpo, com Segoe UI preferencial no Windows.

**Body Font:** a pilha `typography.body`, sem carregamento de uma fonte externa para o texto geral.

**Label/Mono Font:** rótulos usam a família do corpo. Detalhes técnicos da conexão utilizam `ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace`.

**Character:** títulos fortes e compactos conduzem a apresentação; corpo e rótulos dão suporte à leitura e aos formulários. A exceção tipográfica do Google não se estende aos demais componentes.

### Hierarchy

- **Display:** abertura pública, com `clamp(3rem, 5.7vw, 5rem)`. O token `display-max` registra o limite superior, não um tamanho fixo para todas as telas.
- **Headline:** títulos de seção públicos, com `clamp(2rem, 3.5vw, 3.2rem)` e o limite documentado em `headline-max`.
- **Title:** título de trabalho, com `clamp(1.7rem, 3vw, 2.3rem)`. Cards gerais usam títulos menores, enquanto os componentes públicos possuem ajustes próprios.
- **Body:** texto corrente com a altura de linha do token `body`; descrições de abertura usam `body-copy` e comprimento aproximado de 47 caracteres de largura (`47ch`). Textos institucionais usam linhas mais curtas que o container.
- **Label:** campos seguem `field-label`; pequenos rótulos editoriais usam `eyebrow`, caixa alta e espaçamento entre letras.
- **Valores:** números de emissão usam algarismos tabulares, tamanho fluido e acento verde. A formatação decimal pertence à lógica do componente, não ao design token.
- **Ações:** botões nativos e links com aparência de botão compartilham a família do corpo. O controle Google mantém sua família exclusiva.

### Ajustes responsivos observados

O título de abertura passa por um ajuste de 3,6 rem até 1050 px, uma regra fluida até 760 px e 2,8 rem até 390 px. Identificadores do GitHub, legendas institucionais e informações auxiliares funcionais usam ao menos 0,875 rem. Textos decorativos da esfera, ocultos da árvore de acessibilidade, têm escala própria.

## Layout

O container compartilhado tem largura `min(1240px, 92vw)`, centralizado. A página pública usa seções com respiro; formulários e resultados usam agrupamento em cards e grids automáticos. As medidas do grupo `spacing` foram extraídas de usos recorrentes, sem impor uma escala matemática que o código ainda não possui.

- **Página pública:** abertura em duas colunas de proporção 1,15:1; cards de funções em três colunas; equipe em cinco colunas. Seções têm o espaçamento vertical documentado em `section-desktop`.
- **Acesso:** introdução e formulário em duas colunas de proporção 0,9:1; formulário com campos empilhados. No celular, o retorno ao início vem primeiro, seguido do formulário e da apresentação complementar.
- **Área de trabalho:** coluna lateral de 220 px, conteúdo flexível e intervalo de `workspace-gap`. A navegação lateral permanece fixa durante a rolagem em desktop.
- **Grids de dados:** cards de unidade usam mínimo de 260 px quando há espaço; campos das jornadas, mínimo de 180 px com proteção contra overflow.
- **Rodapé:** texto de origem e painel institucional lado a lado; as duas logos permanecem agrupadas, com legendas e divisor sutil. A página inicial mantém a apresentação completa; acesso e operação usam uma versão compacta com origem da equipe e as mesmas marcas.

### Breakpoints atuais

| Largura máxima | Comportamento observado |
| --- | --- |
| 1050 px | Abrevia a escala de abertura, reduz intervalos e leva a equipe para três colunas |
| 850 px | Navegação de trabalho vira duas opções horizontais; trilha de cálculo vira uma coluna |
| 760 px | Menu público recolhível; abertura, apresentação, acesso e rodapé empilhados; equipe em duas colunas |
| 560 px | Sessão e ações se empilham; etapas de coleta e lista de registros ficam mais compactas |
| 400 px | Proteção de largura do grid de autenticação |
| 390 px | Ajustes finos de abertura, avatares e textos auxiliares |

A última pessoa da equipe fica centralizada quando o grid de duas colunas deixa uma posição sem par. Âncoras públicas reservam espaço para a barra fixa. Preservar o comportamento de teclado e a ordem de leitura ao reorganizar as colunas.

## Elevation & Depth

A profundidade vem principalmente de diferenças tonais, bordas e gradientes discretos. A sombra global dos cards existe na base, mas a área de trabalho e os cards de acesso a removem. A ilustração ambiental é a principal exceção expressiva, com iluminação verde, órbitas e uma esfera em camadas.

### Shadow Vocabulary

- **Card de base:** `0 18px 40px rgba(0, 0, 0, 0.45)`, com as exceções de contexto descritas acima.
- **Etiqueta da esfera:** `0 10px 35px #0008` para destacar as pequenas placas sobre a ilustração.
- **Menu mobile:** `0 15px 30px #000a` para separar a navegação do conteúdo.
- **Esfera:** sombras internas e halo verde suaves, restritos à ilustração ambiental.
- **Foco:** contorno verde de 3 px e deslocamento de 3 px. Não trocar o indicador de foco por uma sombra decorativa.

**The Tonal Depth Rule.** Em interfaces operacionais, usar a hierarquia de superfícies e bordas existente. Reservar o brilho ambiental para os elementos que já exercem esse papel na identidade.

## Shapes

Os tokens de `rounded` distinguem funções existentes: cápsulas para ações de trabalho e Google; cantos discretos para chamadas públicas; curvas suaves para campos, navegação e cards; círculo para fotos e símbolos auxiliares.

As bordas são finas e normalmente contínuas. Estados vazios usam borda tracejada. A linha da marca e a composição da esfera são parte de seus assets ou componentes, não uma regra geométrica aplicável a todos os controles.

## Components

### Buttons

**Ação destacada, forma dependente do contexto.** O primário usa verde e texto preto. O hover clareia o verde e desloca o botão um pixel para cima; o estado pressionado retorna à posição inicial. A página pública usa a variante de cantos discretos; as ações operacionais usam cápsulas.

O secundário mantém fundo transparente, texto auxiliar e borda sutil; o hover reforça texto e borda. O foco segue o contorno compartilhado. Controles desabilitados reduzem a opacidade para 0,6 e usam cursor de espera.

Ações e campos têm altura mínima de 44 px. O menu móvel e os controles de senha também reservam essa área de toque. Títulos carregam a hierarquia sem sobrerrótulos redundantes; a numeração permanece nas etapas em que comunica uma sequência.

### Google access

**Marca reconhecível integrada ao fundo escuro.** Usar a variante `button-google`, o “G” colorido sobre um pequeno círculo branco e fonte local Google Sans Button. A mesma aparência serve para entrar e vincular a conta. Evitar transformar esse controle em um botão verde genérico.

### Cards / Containers

**Superfícies escuras de contorno suave.** O card geral usa `card`, `line`, `rounded.card` e `spacing.card`. Na área de trabalho, um gradiente discreto substitui a sombra pesada; em mobile, há redução de padding. O painel de chamada pública usa uma curva maior e contém um card de acesso com função clara.

Cards de unidade possuem nome, cidade/UF e ações; o hover eleva levemente o card e reforça a borda. Cadastros novos recebem destaque temporário. Esses estados comunicam contexto sem introduzir uma nova cor de marca.

### Inputs / Fields

**Campos escuros com rótulo persistente.** Usar o preenchimento `bg-soft`, texto `text`, borda `control-border`, forma `rounded.field` e padding do componente `input`. O hover reforça a borda; o foco usa o contorno compartilhado.

Campos de senha têm um olho dentro do campo, ação identificada por nome acessível e estado pressionado. Senha e confirmação têm visibilidade independente. Preservar o valor digitado e o autocomplete ao alternar a visibilidade.

Erros de preenchimento aparecem perto do campo, com `aria-invalid`, descrição associada e foco no primeiro erro. Avisos gerais de formulário ficam junto da ação. Falha de consulta, carregamento e lista vazia têm apresentações distintas; repetir a consulta não reenvia uma gravação.

### Chips / Status

**Estado com texto e cor.** Badges de carregamento, sucesso e erro usam suas famílias `status-*`, cápsula e rótulo curto. Contagens indicam itens carregados, sem aparentar um total completo quando existe paginação. Manter também ícone ou texto; não depender apenas da cor.

### Navigation

**Apresentação e trabalho compartilham a identidade, com organização própria.** A barra superior é fixa e translúcida, com a logo à esquerda e links públicos à direita. O menu mobile usa botão com nome, `aria-expanded`, fechamento com Escape e retorno do foco.

Na área de trabalho, a navegação usa cards horizontais ou verticais conforme o breakpoint; a seleção recebe o verde e a superfície contextual. A mudança de rota tem entrada suave. Preservar o atalho para o conteúdo e o tratamento de foco.

### Team and institutional identity

**Pessoas e origem reconhecíveis.** Fotos circulares, nome, função e identificador formam o card da equipe. O card inteiro leva ao GitHub, com aviso de nova aba e alternativa por iniciais quando a foto falha. Preservar nomes e perfis da configuração existente.

No rodapé, apresentar UnB e AI Lab UnB em superfície escura. Os arquivos originais são locais. A camada visual que torna “.lab” branco é decorativa e não é anunciada novamente por leitores de tela. Não apresentar a origem da equipe como certificação, resultado ambiental ou parceria comercial.

### Calculation trail and feedback

**Número com origem verificável.** O resultado salvo destaca a emissão e apresenta quantidade, conversão e fator em uma trilha de três blocos, empilhada em mobile. A rastreabilidade fica em uma área expansível. Preservar os avisos de estimativa preliminar e os dados versionados.

Confirmações usam texto e superfície verde-escura. Erros usam texto e superfície vermelha. Carregamento pode usar spinner ou skeleton, mantendo a geometria aproximada do conteúdo. Uma gravação confirmada permanece visível se a consulta ou os metadados falharem. A referência possui nova tentativa própria.

Competência recebe uma explicação do mês de referência. Mês e fonte usam nomes familiares; versão e valores originais continuam disponíveis na rastreabilidade. CO₂e e escopo recebem explicações breves junto ao resultado.

### Motion

Transições comuns ficam entre 150 e 220 ms, com `ease`. A entrada de rotas usa 220 ms e deslocamento vertical de 8 px. A abertura pública e a revelação das seções usam 650 ms; as seções observadas entram apenas quando se aproximam da área visível.

A esfera flutua e respira em ciclos de 8 s; uma órbita gira em 40 s. O visitante pode pausar os efeitos. O sistema desativa animações e transições com movimento reduzido, mantém as seções visíveis e conserva os indicadores textuais de estado. O skeleton usa ciclo de 1,6 s; o destaque de cadastro novo, 1,2 s.

**The Motion Choice Rule.** Conservar a pausa dos efeitos e o suporte a movimento reduzido ao reutilizar ou ampliar as animações.

## Do's and Don'ts

### Do

- **Do** preservar preto, verde, esfera ambiental, fotos da equipe e origem na UnB/AI Lab.
- **Do** usar os tokens como referência visual e conferir o contexto real antes de reutilizar uma variante.
- **Do** distinguir apresentação pública, acesso e telas de trabalho pela densidade, mantendo a identidade compartilhada.
- **Do** preservar o olho da senha, a identidade Google, o foco visível, o menu por teclado e as alternativas de movimento.
- **Do** manter nomes, perfis, logos, avisos metodológicos e origem dos resultados fiéis aos dados existentes.
- **Do** validar legibilidade, contraste e área de toque ao criar componentes novos.

### Don't

- **Don't** trocar a paleta ou a fonte geral durante uma correção pontual.
- **Don't** recolocar um painel branco atrás das logos institucionais nem tornar o símbolo “A” monocromático.
- **Don't** recolorir o “G” do Google para o verde da interface.
- **Don't** remover animações, rótulos numerados ou agrupamentos apenas por um alerta genérico do detector.
- **Don't** transformar limitações da captura atual em padrões a repetir.
- **Don't** alterar fluxos de acesso, regras de cálculo ou fatos do projeto como parte da documentação visual.

### Pendências conhecidas

A auditoria de 03/11/2026 e a crítica de 04/11/2026 orientaram os refinamentos registrados acima. Permanecem oportunidades de otimizar imagens locais e consolidar valores decorativos específicos da esfera. As verificações cobrem Chromium com viewports emulados; não substituem testes em dispositivo físico, NVDA ou Safari.

### Uso do complemento Impeccable

`.impeccable/design.json` complementa este arquivo com sombras, movimento, breakpoints, metadados e amostras de componentes em HTML/CSS. As rampas tonais do complemento são visualizações derivadas; não introduzem cores autorizadas para a interface. As amostras não substituem os componentes React, não executam requisições e não alteram o site.
