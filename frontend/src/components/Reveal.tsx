import { useEffect, useRef } from 'react';
import type { ReactNode } from 'react';

export function Reveal({ children, className = '' }: { children: ReactNode; className?: string }) {
  const element = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const target = element.current;
    if (!target || !('IntersectionObserver' in window) || window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) return;
    const observer = new IntersectionObserver(entries => {
      if (entries.some(entry => entry.isIntersecting)) {
        target.classList.remove('reveal-pending');
        observer.disconnect();
      }
    }, { threshold: 0.08 });
    // Conteúdo começa visível; só oculta depois de registrar o observador.
    observer.observe(target);
    target.classList.add('reveal-pending');
    return () => { observer.disconnect(); target.classList.remove('reveal-pending'); };
  }, []);
  return <div ref={element} className={`reveal ${className}`}>{children}</div>;
}
