# Análise da Migração do Frontend — CarbonTrace

**Data:** 28/10/2026  
**Branch de trabalho:** `feat/frontend-skeleton`  
**Status do repositório:** Limpo, sincronizado com `origin/feat/frontend-skeleton`.

---

## 1. Contexto e Objetivos

Esta análise estabelece o diagnóstico e o planejamento para a substituição do frontend antigo pelo novo modelo de frontend (template/skeleton) disponibilizado (`static-site-nginx`), integrando sua estrutura visual e funcional à arquitetura do projeto **CarbonTrace**.

### Objetivos Principais
- Incorporar o novo modelo visual e estrutural ("Pegada Rede" — Calculadora de Emissões de GEE para varejo).
- Preservar a comunicação com a API backend (FastAPI) e o monitoramento de integridade (`/api/health`).
- Manter o ecossistema com TypeScript e bundler Vite, garantindo tipagem estrita e linting sem warnings.
- Otimizar o servidor Nginx com as diretivas do novo modelo (gzip, cache estático, `server_tokens off`, fallback SPA).
- Garantir que o container frontend continue perfeitamente integrado ao `docker-compose` na porta `3000`.

---

## 2. Comparativo: Frontend Antigo vs. Novo Modelo

| Aspecto | Frontend Antigo | Novo Modelo (`static-site-nginx`) | Decisão de Migração |
| :--- | :--- | :--- | :--- |
| **Identidade Visual** | Minimalista/provisória com card central | Tema dark refinado, gradientes, cards modernos e paleta ecológica | Adotar integralmente a base visual e estilização do novo modelo |
| **Funcionalidades** | Apenas consulta e exibição do `/api/health` | Calculadora de emissões de GEE (kWh, diesel, resíduos) em tempo real com gráfico de barras | Integrar a calculadora de emissões como feature central e incorporar o status da API no novo layout |
| **Estrutura de Código** | Componente monolítico em `App.tsx` | HTML + CSS + JS puro (`app.js`, `style.css`, `index.html`) | Modularizar em componentes estruturados e fortemente tipados em TypeScript |
| **Tecnologia / Runtime** | React 19 + TypeScript + Vite | HTML/JS/CSS estático direto em Nginx | Preservar React + TypeScript + Vite, permitindo expansão futura da plataforma e validação estática no CI |
| **Configuração Nginx** | Proxy reverso básico em porta 80/3000 | Configuração com gzip, cache com `expires 7d`, `server_tokens off` e healthcheck | Fundir as otimizações de performance e segurança do novo modelo com o proxy reverso `/api/` |

---

## 3. Planejamento das Etapas de Execução

1. **Etapa 1 — Análise e Planejamento (Atual):**
   - Diagnóstico das diferenças e mapeamento de componentes.
   - Registro formal da documentação da análise.

2. **Etapa 2 — Substituição da Estrutura Antiga pelo Novo Modelo:**
   - Incorporação do novo design system (variáveis CSS, tipografia, layout responsivo, barra superior, seções hero, calculadora, como funciona e rodapé).
   - Remoção dos estilos legados do esqueleto inicial.

3. **Etapa 3 — Integração à Aplicação Existente:**
   - Implementação tipada da lógica da calculadora em componentes TypeScript.
   - Integração do card/indicador de status da API conectado ao backend (`/api/health`) com suporte aos 3 estados (loading, sucesso, erro com retry).
   - Ajuste dos caminhos de imports, tags e metadados no `index.html`.

4. **Etapa 4 — Atualização de Dependências e Configurações:**
   - Otimização do `nginx.conf` e `nginx.conf.template` incorporando gzip, cabeçalhos de cache, proteção de versão (`server_tokens off`) e healthcheck compatível.
   - Verificação e ajuste de dependências no `package.json` e `package-lock.json`.

5. **Etapa 5 — Correções e Refinamentos:**
   - Ajustes de acessibilidade (ARIA labels, contraste, foco nos formulários).
   - Resolução de quaisquer incompatibilidades de tipagem ou imports.

6. **Etapa 6 — Testes e Validação:**
   - Execução de `npm run lint` (`eslint . --max-warnings 0`).
   - Execução de `npm run build` (`tsc -b && vite build`).
   - Verificação dos artefatos finais e validação de inicialização.
