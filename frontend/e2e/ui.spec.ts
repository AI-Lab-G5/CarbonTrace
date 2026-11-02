import { test, expect, type Page } from '@playwright/test';

// Contratos simulados para exercitar o navegador sem depender de Docker/Firebase.
// A integração real com persistência continua em real.spec.ts.
async function setupApi(page: Page) {
  const now = Math.floor(Date.now() / 1000);
  const encode = (value: object) => Buffer.from(JSON.stringify(value)).toString('base64url');
  const idToken = `${encode({ alg: 'none', typ: 'JWT' })}.${encode({ sub: 'ui-user', user_id: 'ui-user', email: 'interface@example.test', email_verified: true, tenant_id: 'empresa-a', papel: 'funcionario', aud: 'demo-carbontrace', iss: 'https://securetoken.google.com/demo-carbontrace', iat: now, exp: now + 3600, auth_time: now, firebase: { sign_in_provider: 'password', identities: {} } })}.unsigned`;
  await page.route('**/identitytoolkit.googleapis.com/**', async route => {
    const lookup = route.request().url().includes('accounts:lookup');
    await route.fulfill({ json: lookup ? { users: [{ localId: 'ui-user', email: 'interface@example.test', emailVerified: true, providerUserInfo: [{ providerId: 'password', email: 'interface@example.test', rawId: 'interface@example.test' }] }] } : { localId: 'ui-user', email: 'interface@example.test', idToken, refreshToken: 'ui-refresh', expiresIn: '3600', registered: true } });
  });
  const state = {
    units: [{ id: 'u', nome: 'Loja Centro', cidade: 'Brasília', uf: 'DF' }],
    records: [] as Record<string, string>[],
    unavailable: false,
  };
  const factor = { fonte_id: 'eletricidade', nome: 'Eletricidade', unidades_aceitas: ['kWh', 'MWh'], unidade_base: 'kWh', kg_co2e_por_unidade: '0.0385', teto_mensal: '999999', fonte_referencia: 'Referência do fator original', status: 'preliminar' };
  await page.route('**/api/**', async route => {
    const url = new URL(route.request().url());
    const path = url.pathname.replace('/api', '');
    const method = route.request().method();
    const paginate = (itens: unknown[]) => ({ itens, proximo_cursor: null, limite: 20, total_na_pagina: itens.length });
    let response: unknown = {};
    if (path === '/healthz' || path === '/readyz') {
      if (state.unavailable) { await route.fulfill({ status: 503, json: {} }); return; }
      response = { status: 'ok', servico: 'carbontrace-ui', emulador: true };
    } else if (path === '/v1/unidades') {
      if (method === 'POST') {
        const created = { id: `u-${state.units.length}`, ...route.request().postDataJSON() };
        state.units.push(created); response = created;
      } else response = paginate(state.units);
    } else if (path.startsWith('/v1/unidades/')) response = state.units.find(u => u.id === path.split('/').at(-1));
    else if (path.startsWith('/v1/fontes/versoes')) response = { versao: 'v1', fatores: [factor], status: 'preliminar', vigencia_inicio: '2025-01' };
    else if (path === '/v1/fontes') response = [factor];
    else if (path === '/v1/consumos' && method === 'PUT') {
      const input = route.request().postDataJSON();
      const saved = { id: 'c', unidade_id: input.unidade_id, competencia: input.competencia, fonte_id: input.fonte_id, quantidade_informada: input.quantidade, unidade_informada: input.unidade_medida, quantidade_convertida: '1500', unidade_base: 'kWh', fator_versao: 'v1', fator_valor: '0.0385', emissao_kg_co2e: '57.750', escopo: '2' };
      state.records.push(saved); response = saved;
    } else if (path === '/v1/consumos') response = paginate(state.records.filter(c => (!url.searchParams.has('unidade_id') || c.unidade_id === url.searchParams.get('unidade_id')) && (!url.searchParams.has('competencia') || c.competencia === url.searchParams.get('competencia'))));
    else if (path.startsWith('/v1/consumos/')) response = state.records[0];
    await route.fulfill({ json: response });
  });
  return state;
}

async function login(page: Page, path = '/consumos') {
  await page.goto(path);
  await expect(page).toHaveURL(/\/entrar$/);
  await expect(page.getByRole('heading', { name: 'Coleta mensal' })).toHaveCount(0);
  await page.getByLabel('E-mail').fill('interface@example.test');
  await page.getByLabel('Senha', { exact: true }).fill('teste-interface');
  await page.getByRole('button', { name: 'Entrar', exact: true }).click();
  await expect(page).toHaveURL(new RegExp(`${path}$`));
}

test('rotas protegidas, histórico, rascunho, cálculo e layout responsivo', async ({ page }, testInfo) => {
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await setupApi(page); await login(page);
  await page.getByLabel('Loja', { exact: true }).selectOption('u');
  await page.getByLabel('Competência').fill('2025-10');
  await page.getByLabel('Fonte', { exact: true }).selectOption('eletricidade');
  await page.getByLabel('Quantidade').fill('1,5');
  await page.getByLabel('Medida', { exact: true }).selectOption('MWh');
  await page.getByRole('link', { name: /Unidades Lojas/ }).click();
  await expect(page.getByRole('heading', { name: 'Unidades da empresa' })).toBeVisible();
  await page.goBack();
  await expect(page.getByLabel('Quantidade')).toHaveValue('1,5');
  await expect(page.getByLabel('Medida', { exact: true })).toHaveValue('MWh');
  await page.goForward();
  await expect(page).toHaveURL(/\/unidades$/);
  await page.getByRole('link', { name: /Consumos Coleta/ }).click();
  await page.getByLabel('Quantidade').fill('-1');
  await page.getByRole('button', { name: 'Salvar consumo' }).click();
  await expect(page.getByRole('alert')).toContainText('decimal não negativa');
  await page.getByLabel('Quantidade').fill('1,5');
  await page.getByRole('button', { name: 'Salvar consumo' }).click();
  await expect(page.getByRole('region', { name: 'Resultado salvo' })).toContainText('57,750 kgCO₂e');
  await page.getByText('Rastreabilidade do cálculo', { exact: false }).click();
  await expect(page.getByText('preliminar — Referência do fator original')).toBeVisible();
  await page.getByRole('button', { name: 'Conferir cálculo original' }).click();
  await expect(page.getByRole('status').filter({ hasText: 'Reprodução concluída' })).toBeVisible();
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
  await page.screenshot({ path: testInfo.outputPath('consumos-desktop.png'), fullPage: true, animations: 'disabled' });
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.getByRole('link', { name: /Consumos Coleta/ })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.emulateMedia({ reducedMotion: 'reduce' });
  expect(await page.locator('.route-enter').first().evaluate(el => getComputedStyle(el).animationName)).toBe('none');
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
  await page.screenshot({ path: testInfo.outputPath('consumos-mobile.png'), fullPage: true, animations: 'disabled' });
  await page.reload();
  await expect(page).toHaveURL(/\/consumos$/);
  await page.getByRole('button', { name: /Eletricidade.*2025-10/ }).click();
  await expect(page.getByRole('region', { name: 'Resultado salvo' })).toContainText('57,750');
  await page.getByRole('link', { name: 'CarbonTrace — início' }).click();
  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByRole('heading', { name: /Conheça o impacto/ })).toBeVisible();
  await page.getByRole('button', { name: 'Abrir menu' }).click();
  await page.getByRole('navigation', { name: 'Navegação principal' }).getByRole('link', { name: /Abrir meu painel/ }).click();
  await expect(page.getByRole('heading', { name: 'Unidades da empresa' })).toBeVisible();
  await page.getByRole('button', { name: 'Sair', exact: true }).click();
  await expect(page).toHaveURL(/\/entrar$/);
  await page.goto('/consumos');
  await expect(page).toHaveURL(/\/entrar$/);
  expect(errors).toEqual([]);
});

test('cadastro destaca unidade e abre coleta na loja selecionada', async ({ page }, testInfo) => {
  await setupApi(page); await login(page, '/unidades');
  await page.getByLabel('Nome', { exact: true }).fill('Loja Norte');
  await page.getByLabel('Cidade', { exact: true }).fill('São Paulo');
  await page.getByLabel('UF', { exact: true }).fill('sp');
  await page.getByRole('button', { name: 'Cadastrar', exact: true }).click();
  await expect(page.getByText('✓ Unidade cadastrada.')).toBeVisible();
  const card = page.getByRole('listitem').filter({ hasText: 'Loja Norte' });
  await expect(card).toContainText('São Paulo / SP');
  await expect(card).toContainText('Recém-cadastrada');
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
  await page.screenshot({ path: testInfo.outputPath('unidades-desktop.png'), fullPage: true, animations: 'disabled' });
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
  await page.screenshot({ path: testInfo.outputPath('unidades-mobile.png'), fullPage: true, animations: 'disabled' });
  await card.getByRole('button', { name: 'Registrar consumo →' }).click();
  await expect(page).toHaveURL(/\/consumos$/);
  await expect(page.getByLabel('Loja', { exact: true })).toHaveValue('u-1');
});

test('falha de conexão abre detalhes e permite tentar novamente', async ({ page }) => {
  const state = await setupApi(page); state.unavailable = true;
  await page.goto('/entrar');
  await expect(page.getByText('⚠ Indisponível', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Tentar novamente', exact: true })).toBeVisible();
  state.unavailable = false;
  await page.getByRole('button', { name: 'Tentar novamente', exact: true }).click();
  await expect(page.getByText('Pronta', { exact: true })).toBeVisible();
});

test('início público, fotos da equipe, efeitos, menu mobile e cadastro separado', async ({ page }, testInfo) => {
  const apiRequests: string[] = [];
  await page.route('**/api/**', async route => { apiRequests.push(route.request().url()); await route.abort(); });
  await page.goto('/');
  await expect(page.getByRole('heading', { name: /Conheça o impacto/ })).toBeVisible();
  await expect(page.getByLabel('E-mail')).toHaveCount(0);
  await expect(page).toHaveURL(/\/$/);
  await page.getByRole('button', { name: 'Pausar efeitos' }).click();
  await expect(page.getByRole('button', { name: 'Retomar efeitos' })).toHaveAttribute('aria-pressed', 'true');
  expect(await page.locator('.planet-sphere').evaluate(el => getComputedStyle(el).animationPlayState)).toBe('paused');
  await page.getByRole('button', { name: 'Retomar efeitos' }).click();
  await page.getByRole('link', { name: 'Equipe', exact: true }).click();
  await expect(page).toHaveURL(/\/#equipe$/);
  await expect(page.getByRole('heading', { name: /Pessoas por trás/ })).toBeInViewport();
  for (const [name, login] of [['Thomas Augusto', 'Thomas4ugust0'], ['Luís Davi', 'pontesluis'], ['Heitor Monteiro', 'heitormontt'], ['Felipe C. Duque', 'felipecduque7'], ['Felipe Moreira', 'Bipelipe']]) {
    const link = page.getByRole('link', { name: `${name} no GitHub (abre em nova aba)` });
    await expect(link).toHaveAttribute('href', `https://github.com/${login}`);
    await expect(link).toHaveAttribute('rel', 'noopener noreferrer');
    await expect.poll(() => link.locator('img').evaluate(image => (image as HTMLImageElement).complete && (image as HTMLImageElement).naturalWidth > 0)).toBe(true);
  }
  expect(apiRequests).toEqual([]);
  for (const reveal of await page.locator('.reveal').all()) {
    await reveal.scrollIntoViewIfNeeded();
    await expect(reveal).not.toHaveClass(/reveal-pending/);
  }
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
  await page.screenshot({ path: testInfo.outputPath('inicio-desktop.png'), fullPage: true, animations: 'disabled' });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole('button', { name: 'Abrir menu' }).click();
  await page.getByRole('link', { name: 'Como funciona', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Abrir menu' })).toHaveAttribute('aria-expanded', 'false');
  await expect(page.getByRole('heading', { name: /Um caminho simples/ })).toBeInViewport();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.emulateMedia({ reducedMotion: 'reduce' });
  expect(await page.locator('.planet-sphere').evaluate(el => getComputedStyle(el).animationName)).toBe('none');
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
  await expect.poll(() => page.evaluate(() => window.scrollY)).toBe(0);
  await page.screenshot({ path: testInfo.outputPath('inicio-mobile.png'), fullPage: true, animations: 'disabled' });
  await page.getByRole('link', { name: /Primeiro acesso/ }).click();
  await expect(page).toHaveURL(/\/entrar\?modo=cadastro$/);
  await expect(page.getByRole('heading', { name: 'Criar conta', exact: true })).toBeVisible();
  await expect(page.getByLabel('Nome', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Voltar para entrar' }).click();
  await expect(page.getByRole('heading', { name: 'Entrar no CarbonTrace' })).toBeVisible();
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
  await page.screenshot({ path: testInfo.outputPath('login-mobile.png'), fullPage: true, animations: 'disabled' });
});

test('perfil da equipe permanece acessível quando uma foto falha', async ({ page }) => {
  await page.route('**/team/heitormontt.jpg', route => route.abort());
  await page.goto('/#equipe');
  const member = page.getByRole('link', { name: 'Heitor Monteiro no GitHub (abre em nova aba)' });
  await member.scrollIntoViewIfNeeded();
  await expect(member.locator('.team-initials')).toHaveText('HM');
  await expect(member).toHaveAttribute('href', 'https://github.com/heitormontt');
});
