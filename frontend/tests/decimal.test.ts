import { test } from 'node:test';
import assert from 'node:assert/strict';
import { decimalInput, formatDecimal } from '../src/utils/decimal.ts';
test('#9 CA-03: zero explícito e decimal textual', () => {
 assert.equal(decimalInput('0'), '0'); assert.equal(decimalInput('1,25'), '1.25');
 for (const value of ['', ' ', '-1', 'NaN', 'Infinity', '1.000,25', '1e3']) assert.throws(() => decimalInput(value));
 assert.equal(decimalInput('12345678901234567890.123456'), '12345678901234567890.123456');
});
test('#19 CA-04: apresentação HALF_EVEN sem perda binária', () => {
 assert.equal(formatDecimal('38.500', 3), '38,500');
 assert.equal(formatDecimal('1.2345', 3), '1,234');
 assert.equal(formatDecimal('1.2355', 3), '1,236');
 assert.equal(formatDecimal('9.9995', 3), '10,000');
 assert.equal(formatDecimal('0.0385'), '0,0385');
});
