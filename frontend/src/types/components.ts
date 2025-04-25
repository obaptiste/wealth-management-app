// frontend/src/types/components.ts
import { ReactNode } from 'react';

export interface ProvidersProps {
  children: ReactNode;
}

export interface ErrorFallbackProps {
  error: Error;
}