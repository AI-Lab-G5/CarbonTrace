import { test, describe } from 'node:test';
import assert from 'node:assert/strict';
import { calcularEmissoes, FATORES_PADRAO } from '../src/utils/calculo.ts';

describe('Calculadora de Emissões de GEE', () => {
  test('fatores padrão conferem com a especificação didática', () => {
    assert.equal(FATORES_PADRAO.energia, 0.0385);
    assert.equal(FATORES_PADRAO.combustivel, 2.392);
    assert.equal(FATORES_PADRAO.residuos, 0.45);
  });

  test('calcula emissões corretamente para valores de referência padrão', () => {
    // 12.000 kWh * 0.0385 = 462 kg
    // 800 L * 2.392 = 1913.6 kg
    // 1.500 kg * 0.45 = 675 kg
    // Total = 462 + 1913.6 + 675 = 3050.6 kg
    const resultado = calcularEmissoes('12000', '800', '1500');

    assert.equal(Math.round(resultado.total), 3051);
    assert.equal(resultado.itens.length, 3);

    const [energia, combustivel, residuos] = resultado.itens;

    assert.equal(energia.nome, 'Energia elétrica');
    assert.equal(energia.emissao, 462);
    assert.ok(Math.abs(energia.percentual - 15.1) < 0.2);

    assert.equal(combustivel.nome, 'Frota (combustível)');
    assert.equal(combustivel.emissao, 1913.6);
    assert.ok(Math.abs(combustivel.percentual - 62.7) < 0.2);

    assert.equal(residuos.nome, 'Resíduos (aterro)');
    assert.equal(residuos.emissao, 675);
    assert.ok(Math.abs(residuos.percentual - 22.1) < 0.2);
  });

  test('trata entradas vazias ou inválidas como zero sem quebrar', () => {
    const resultado = calcularEmissoes('', '-50', 'invalid');

    assert.equal(resultado.total, 0);
    resultado.itens.forEach((item) => {
      assert.equal(item.emissao, 0);
      assert.equal(item.percentual, 0);
    });
  });
});
