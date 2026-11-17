import type { ComponentProps } from 'react';

export function GoogleButton({ children, ...props }: Omit<ComponentProps<'button'>, 'className' | 'type'>) {
  return <button {...props} type="button" className="google-button">
    <span className="google-button-icon" aria-hidden="true"><img src="/brand/google-g.png" alt="" width="20" height="20"/></span>
    <span>{children}</span>
  </button>;
}
