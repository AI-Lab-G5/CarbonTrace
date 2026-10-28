import { useState } from 'react';
import { Topbar } from '@/components/Topbar';
import { Hero } from '@/components/Hero';
import { Calculadora } from '@/components/Calculadora';
import { ApiStatus, type ApiStatusState } from '@/components/ApiStatus';
import { ComoFunciona } from '@/components/ComoFunciona';
import { Footer } from '@/components/Footer';
import './App.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

export default function App() {
  const [apiState, setApiState] = useState<ApiStatusState>({ state: 'loading' });

  return (
    <div className="app-container">
      <Topbar
        apiStatusBadge={
          <span className={`badge badge-${apiState.state}`} style={{ marginLeft: '0.5rem' }}>
            {apiState.state === 'loading' && 'API: ...'}
            {apiState.state === 'success' && 'API: Online'}
            {apiState.state === 'error' && 'API: Off'}
          </span>
        }
      />

      <main>
        <Hero />
        <Calculadora />
        <ApiStatus apiBaseUrl={API_BASE_URL} onStatusChange={setApiState} />
        <ComoFunciona />
      </main>

      <Footer />
    </div>
  );
}
