export type FieldErrors = Record<string, string>;

export class FormValidationError extends Error {
  fields: FieldErrors;
  constructor(fields: FieldErrors) {
    super(Object.values(fields).join(' '));
    this.fields = fields;
  }
}

export function fieldErrors(error: unknown): FieldErrors {
  if (!error || typeof error !== 'object' || !('fields' in error) || !error.fields || typeof error.fields !== 'object') return {};
  return Object.fromEntries(Object.entries(error.fields).filter((entry): entry is [string, string] => typeof entry[1] === 'string'));
}
