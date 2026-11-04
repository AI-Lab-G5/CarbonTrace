# CarbonTrace — critique, polish e harden

Refinamento de 04/11/2026, na branch `feat/router-mudancas-front`.

## Avaliação inicial

Método: duas avaliações independentes, `/root/design_review` (design) e `/root/detector_review` (detector e navegador). A terminou antes de os resultados do detector entrarem na síntese principal.

| Heurística | Nota inicial |
| --- | ---: |
| Visibilidade do estado | 3/4 |
| Linguagem familiar | 3/4 |
| Controle e liberdade | 2/4 |
| Consistência | 3/4 |
| Prevenção de erros | 3/4 |
| Reconhecimento | 3/4 |
| Eficiência | 2/4 |
| Hierarquia e simplicidade | 3/4 |
| Recuperação de erros | 2/4 |
| Ajuda contextual | 2/4 |
| **Total** | **26/40** |

Não foi atribuída uma nova nota depois das correções. A verificação posterior comprova comportamentos e medidas específicos, sem apresentar a nota inicial como nota do resultado final.

A esfera ambiental, o preto e verde, a equipe real e a origem acadêmica constituem a identidade a preservar. A navegação com dois destinos e a trilha do cálculo já reduzem a carga cognitiva. A maior dificuldade estava na recuperação de erros: feedback fora da tela e uma ação de consulta oferecida para corrigir preenchimento. Quem usa celular também precisava atravessar outra apresentação antes do login e perdia o preenchimento ao recarregar.

## Correções implementadas

| Prioridade inicial | Problema | Resultado |
| --- | --- | --- |
| P1 | Validação longe do campo e falha de consulta apresentada como lista vazia | Erros locais com descrição, `aria-invalid` e foco; falha, carregamento e vazio distintos; consultas com recuperação própria |
| P2 | Perda do preenchimento após interrupção | Rascunhos de unidade e consumo por usuário na mesma aba, preservados na navegação e na recarga, removidos ao salvar ou encerrar a sessão |
| P2 | Formulário de entrada começava tarde no celular | Retorno e formulário primeiro; apresentação complementar depois |
| P2 | Competência, fonte, CO₂e e escopo pouco explicados | Ajuda contextual, mês em português, fontes com nomes familiares e metadados mantidos |
| P2 | Texto pequeno, controles compactos e placeholders com baixo contraste | Texto auxiliar funcional ampliado, controles de 44 px e contornos/placeholder reforçados |

Falhas de referência do fator têm recuperação própria. Se o envio foi confirmado e a consulta seguinte falhar, o resultado retornado pela gravação permanece visível, com orientação para conferir os registros. Nenhuma escrita é repetida automaticamente. A API tem limite de 15 segundos e mantém cancelamento externo.

Senhas e convites não entram nos rascunhos. Armazenamento bloqueado não impede o formulário de funcionar em memória. A loja selecionada no rascunho pode ser recuperada mesmo quando está além da primeira página da lista.

As animações, a pausa, o movimento reduzido, os perfis da equipe, o acesso Google e as logos institucionais foram preservados. Títulos ficaram sem sobrerrótulos redundantes. O rodapé completo permanece no início e usa apresentação compacta nas telas de acesso e operação.

## Validação

- ESLint sem avisos e build de produção concluídos, incluindo build no Docker.
- 52 testes de componente/API e 2 testes de decimais passaram.
- 8 testes de navegador passaram. O fluxo de rotas/cálculo foi executado novamente após o ajuste final da indicação de etapa.
- Layout verificado em 320, 390, 768 e 1440 px; texto longo e ampliação de fonte a 200%.
- Menu por teclado/Escape, olho da senha, pausa, movimento reduzido, rotas protegidas, retorno do login, cadastro, cálculo e rastreabilidade verificados.
- Novos cenários cobrem quantidade inválida com foco, recarga do rascunho, isolamento por usuário, armazenamento bloqueado, falha de consulta e falhas após gravação confirmada.
- Em produção local, login real da conta de demonstração e navegação entre Unidades e Consumos funcionaram, sem erros de JavaScript observados. Cenários de gravação da suíte usam API simulada; não foram criados registros de negócio no ambiente de demonstração.
- Medidas finais no Chromium: menu e olho da senha 44 × 44 px; botão Entrar com altura aproximada de 44,94 px. Contorno do campo: 3,66:1 contra seu preenchimento e 3,50:1 contra o card. Placeholder de cadastro: `#9ca3af` sobre `#0e0e0e`, opacidade 1, contraste 7,60:1.
- Oito amostras de componentes do complemento Impeccable renderizadas em shadow DOM; frontmatter, referências e narrativa da documentação validados.

## Proveniência e limites

Alvo da crítica: `frontend/src`; slug `frontend-src`; nenhuma lista de exceções anterior encontrada. Detector estático: `[]`, exit 0. Overlay: 7 ocorrências no início, 5 no login, 8 em unidades e 5 em consumos, com repetição entre telas. Os nove nomes de regras distintos foram interpretados com a inspeção visual. O brilho temático não foi tratado como defeito; overflow provocado pelo próprio overlay desapareceu sem ele.

O navegador nativo não estava disponível: inventário sem browsers, Edge retornou “Browser is not available: edge”. A inspeção usou Chromium do Playwright em páginas próprias. O preflight de mutação e a injeção do detector funcionaram em quatro telas; o overlay foi apresentado durante a inspeção e encerrado depois. O helper na porta 8400 foi parado com `live-server stop --keep-inject`. Servidores Vite dos testes foram encerrados pelo Playwright. O frontend Docker atualizado permanece em `http://localhost:3000`.

O snapshot inicial está em `.impeccable/critique/2026-11-04T15-39-06Z__frontend-src.md`; é o primeiro registro desse alvo, sem tendência comparativa. O helper `latest` encerrou o registro ao tratar o diretório como alvo de arquivo; o snapshot foi preservado como histórico, sem alegar fechamento por uma nova pontuação. O corpo temporário foi removido. Capturas B foram removidas; capturas A e finais foram preservadas fora do projeto, na pasta temporária do usuário.

Questions skipped: o usuário já definiu o escopo completo e autorizou critique, polish e harden preservando a identidade.

Os testes usam Chromium com viewport emulado. Dispositivo físico, NVDA e Safari não foram testados. Otimização das imagens locais permanece como oportunidade posterior. A lógica de cálculo, permissões e contratos do backend permanece a mesma.

Alterações versionadas na branch `feat/router-mudancas-front`. O envio ao remoto é uma etapa separada.
