import { act, render, screen } from '@testing-library/react';
import { afterEach, expect, test, vi } from 'vitest';
import { ApiStatus } from '../src/components/ApiStatus';
afterEach(()=>{vi.useRealTimers();vi.unstubAllGlobals();});
test('sonda não falha aos 10s e mostra erro recuperável aos 65s',async()=>{
 vi.useFakeTimers();
 vi.stubGlobal('fetch',vi.fn((_url,options:RequestInit)=>new Promise((_resolve,reject)=>options.signal?.addEventListener('abort',()=>reject(new DOMException('cancelado','AbortError'))))));
 render(<ApiStatus/>);
 await act(async()=>{await vi.advanceTimersByTimeAsync(10000);});
 expect(screen.getByRole('status')).toHaveTextContent('um minuto');
 expect(screen.queryByText('⚠ Indisponível')).not.toBeInTheDocument();
 await act(async()=>{await vi.advanceTimersByTimeAsync(55000);});
 expect(screen.getByText('⚠ Indisponível')).toBeVisible();
 expect(screen.getByRole('button',{name:'Tentar novamente'})).toBeVisible();
});
