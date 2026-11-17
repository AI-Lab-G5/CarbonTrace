import { useOutletContext } from 'react-router';
import type { useJornadas } from './useJornadas';

export function useJornadasContext() {
  return useOutletContext<ReturnType<typeof useJornadas>>();
}
