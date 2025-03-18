'use client';

import { NextUIProvider } from '@nextui-org/react';
import { ThemeProvider as NextThemesProvider } from 'next-themes';
import { AuthProvider } from '../contexts/AuthContext';
import { ErrorBoundary, FallbackProps } from 'react-error-boundary';

function ErrorFallback({ error }: FallbackProps) {
  return (
    <div className="p-4 bg-red-50 text-red-700 rounded">
      <h2 className="text-lg font-semibold">Something went wrong:</h2>
      <p>{error.message}</p>
    </div>
  );
}

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ErrorBoundary FallbackComponent={ErrorFallback}>
        <NextThemesProvider attribute="class" defaultTheme="system">
          <NextUIProvider>
            <AuthProvider>
              {children}
            </AuthProvider>
          </NextUIProvider>
        </NextThemesProvider>
    </ErrorBoundary>
  );
}