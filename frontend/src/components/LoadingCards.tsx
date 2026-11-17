export function LoadingCards({ label }: { label: string }) {
  return <div role="status" className="loading-cards">
    <span className="sr-only">{label}</span>
    {[0, 1, 2].map(i => <div className="skeleton-card" aria-hidden="true" key={i}><div className="skeleton skeleton-title"/><div className="skeleton"/><div className="skeleton skeleton-short"/></div>)}
  </div>;
}
