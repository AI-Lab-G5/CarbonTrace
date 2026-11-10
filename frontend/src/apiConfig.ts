// VITE_* é resolvido no build; URL pública é fornecida pela implantação.
export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/+$/, '');
export const READ_TIMEOUT_MS = 65000;
export const WRITE_TIMEOUT_MS = 15000;
