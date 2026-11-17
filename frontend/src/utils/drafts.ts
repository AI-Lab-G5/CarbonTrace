type DraftKind = 'consumption' | 'unit';
const key = (uid: string, kind: DraftKind) => `carbontrace:draft:v1:${uid}:${kind}`;

export function readDraft<K extends string>(uid: string, kind: DraftKind, fields: readonly K[]): Partial<Record<K, string>> {
  try {
    const value: unknown = JSON.parse(sessionStorage.getItem(key(uid, kind)) || 'null');
    if (!value || typeof value !== 'object') return {};
    return Object.fromEntries(fields.flatMap(field => {
      const text = (value as Record<string, unknown>)[field];
      return typeof text === 'string' && text.length <= 2048 ? [[field, text]] : [];
    })) as Partial<Record<K, string>>;
  } catch { return {}; }
}

export function writeDraft(uid: string, kind: DraftKind, draft: Record<string, string>) {
  try {
    if (Object.values(draft).some(Boolean)) sessionStorage.setItem(key(uid, kind), JSON.stringify(draft));
    else sessionStorage.removeItem(key(uid, kind));
  } catch { /* Armazenamento bloqueado não impede o preenchimento ou o envio. */ }
}

export function clearDrafts(uid: string) {
  for (const kind of ['consumption', 'unit'] as const) writeDraft(uid, kind, {});
}
