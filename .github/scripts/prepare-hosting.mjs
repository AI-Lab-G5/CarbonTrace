import { appendFileSync, mkdirSync, writeFileSync } from 'node:fs';

const env = process.env;
const required = [
  'VITE_AUTH_MODE', 'VITE_FIREBASE_PROJECT_ID', 'VITE_FIREBASE_API_KEY',
  'VITE_FIREBASE_AUTH_DOMAIN', 'VITE_API_BASE_URL',
];

function apiHost(address) {
  const url = new URL(address);
  if (url.protocol !== 'https:' || url.username || url.password || url.search || url.hash) {
    throw new Error('VITE_API_BASE_URL deve ser uma URL HTTPS da API.');
  }
  return url.hostname.toLowerCase().replace(/\.$/, '');
}

const preview = env.HOSTING_TARGET === 'preview';
let directory = 'dist';
if (preview && required.every(name => !env[name])) {
  // Substitui também canais existentes que já receberam um bundle de produção.
  directory = 'preview-indisponivel';
  mkdirSync(directory, { recursive: true });
  writeFileSync(`${directory}/index.html`, `<!doctype html>
<html lang="pt-BR"><meta charset="utf-8"><title>Preview CarbonTrace</title>
<h1>Preview indisponível</h1><p>O ambiente de homologação ainda não foi configurado.</p></html>`);
  console.log('O canal do PR receberá apenas o aviso de homologação indisponível.');
} else if (env.HOSTING_TARGET !== 'ci') {
  for (const name of required) {
    if (!env[name]?.trim() || env[name] !== env[name].trim()) {
      throw new Error(`Configure ${preview ? 'PREVIEW_' : ''}${name} para publicação.`);
    }
  }
  if (env.VITE_AUTH_MODE !== 'firebase' || env.VITE_FIREBASE_PROJECT_ID.startsWith('demo-')) {
    throw new Error('A publicação requer Firebase Auth em um projeto real.');
  }
  const host = apiHost(env.VITE_API_BASE_URL);
  if (preview) {
    const productionHosts = [env.RENDER_API_URL, env.PRODUCTION_API_URL].filter(Boolean).map(apiHost);
    const productionDomains = [env.PRODUCTION_AUTH_DOMAIN,
      `${env.HOSTING_PROJECT}.firebaseapp.com`, `${env.HOSTING_PROJECT}.web.app`];
    if (productionHosts.includes(host) || env.VITE_FIREBASE_PROJECT_ID === env.HOSTING_PROJECT ||
        env.VITE_FIREBASE_PROJECT_ID === env.PRODUCTION_PROJECT_ID ||
        env.VITE_FIREBASE_API_KEY === env.PRODUCTION_API_KEY ||
        productionDomains.includes(env.VITE_FIREBASE_AUTH_DOMAIN.toLowerCase())) {
      throw new Error('O preview requer uma API e um projeto Firebase separados da produção.');
    }
  }
}
appendFileSync(env.GITHUB_OUTPUT, `directory=${directory}\n`);
