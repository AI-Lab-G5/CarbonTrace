import { test, expect } from '@playwright/test';
import { mkdirSync } from 'node:fs';
// Apenas apresentação sintética. Nenhum Firebase/API real neste ensaio.
for(const width of [1440,390]) {
 test(`dashboard sintético em ${width}px preserva filtros e estados`,async({page})=>{
  await page.setViewportSize({width,height:950});
  await page.goto('/tests/dashboard-preview.html');
  await expect(page.getByRole('heading',{name:'Dashboard — teste de apresentação'})).toBeVisible();
  await expect(page.getByText('400,000 kgCO₂e')).toHaveCount(2);
  await page.getByLabel('Região').selectOption('s');
  await page.getByLabel('Estado de teste').selectOption('error');
  await expect(page.getByRole('alert')).toContainText('filtros foram mantidos');
  await expect(page.getByLabel('Região')).toHaveValue('s');
  await page.getByRole('button',{name:'Tentar novamente'}).click();
  await expect(page.getByRole('status')).toContainText('Resultado parcial');
  expect(await page.evaluate(()=>document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  mkdirSync('../docs/frontend/evidencias/cp3',{recursive:true});
  await page.screenshot({path:`../docs/frontend/evidencias/cp3/dashboard-sintetico-${width}.png`,fullPage:true});
  await page.getByLabel('Estado de teste').selectOption('loading');
  await expect(page.getByRole('status')).toContainText('um minuto');
  await page.getByLabel('Estado de teste').selectOption('empty');
  await expect(page.getByRole('status')).toContainText('Nenhum consolidado');
  await page.getByLabel('Estado de teste').selectOption('unavailable');
  await expect(page.getByRole('status')).toContainText('Menos de 3 elegíveis');
  await page.getByLabel('Estado de teste').selectOption('ready');
  await page.getByLabel('Competência').fill('2026-09');
  await expect(page.getByText('0,000 kgCO₂e')).toBeVisible();
  await expect(page.getByText('400,000 kgCO₂e')).toHaveCount(0);
  await page.getByLabel('Região').focus(); await page.keyboard.press('Tab');
  await expect(page.getByLabel('Unidade')).toBeFocused();
 });
}
