import { useState } from 'react';
import type { team } from '@/data/team';

export function TeamCard({ member }: { member: (typeof team)[number] }) {
  const [imageFailed, setImageFailed] = useState(false);
  return <li className="team-card">
    <a href={`https://github.com/${member.login}`} target="_blank" rel="noopener noreferrer" aria-label={`${member.name} no GitHub (abre em nova aba)`}>
      <div className="team-portrait">
        {imageFailed ? <span className="team-initials" aria-hidden="true">{member.initials}</span> : <img src={member.image} alt={`Avatar de ${member.name} no GitHub`} width="104" height="104" loading="lazy" decoding="async" onError={() => setImageFailed(true)}/>}
        <span className="team-profile-arrow" aria-hidden="true">↗</span>
      </div>
      <h3>{member.name}</h3><p>{member.role}</p>
      <span className="team-handle"><svg viewBox="0 0 24 24" width="15" height="15" fill="currentColor" aria-hidden="true"><path d="M12 2a10 10 0 0 0-3.16 19.49c.5.09.68-.22.68-.48v-1.86c-2.78.6-3.37-1.18-3.37-1.18-.45-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.61.07-.61 1 .07 1.53 1.03 1.53 1.03.89 1.53 2.34 1.09 2.91.83.09-.65.35-1.09.64-1.34-2.22-.25-4.56-1.11-4.56-4.94 0-1.09.39-1.98 1.03-2.68-.1-.25-.45-1.27.1-2.65 0 0 .84-.27 2.75 1.02A9.6 9.6 0 0 1 12 6.82c.85 0 1.71.11 2.51.34 1.91-1.29 2.75-1.02 2.75-1.02.55 1.38.2 2.4.1 2.65.64.7 1.03 1.59 1.03 2.68 0 3.84-2.34 4.69-4.58 4.94.36.31.68.92.68 1.85v2.75c0 .27.18.58.69.48A10 10 0 0 0 12 2Z"/></svg>@{member.login}</span>
    </a>
  </li>;
}
