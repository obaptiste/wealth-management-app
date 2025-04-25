// src/components/Providers.tsx (Simplified)

'use client';

import React, { useEffect } from 'react';
import { NextUIProvider } from '@nextui-org/react';
import { ThemeProvider as NextThemeProvider } from 'next-themes';
import { ChakraProvider } from '@chakra-ui/react';
import { AuthProvider } from '@/contexts/AuthContext';
import { ErrorBoundary } from 'react-error-boundary';
import { ColorModeScript } from '@chakra-ui/color-mode';
import { ErrorFallbackProps } from '@/types/components'; // Adjust the import path as necessary
import { theme } from '@/styles/theme'; // Ensure this path is correct

function ErrorFallback({ error }: ErrorFallbackProps) {
  return (
    <div className='p-4 bg-red-50 text-red-700 rounded'>
      <h2 className="text-lg font-semibold">Something went wrong:</h2>
      <p>{error.message}</p>
    </div>
  );
}

export function Providers({ children }: { children: React.ReactNode }) {
  // Log theme only if debugging is still needed
  // console.log('Imported theme object in Providers.tsx:', theme);

  useEffect(() => {
    // Apply theme attributes to document element
    const savedTheme = typeof window !== 'undefined' ? 
      localStorage.getItem('theme') || 'light' : 'light';
    
    document.documentElement.setAttribute('data-theme', savedTheme);
    document.documentElement.className = savedTheme === 'dark' ? 'dark' : '';
    document.documentElement.style.colorScheme = savedTheme;
  }, []);

  // Check if theme or theme.config is undefined before rendering
  if (!theme || !theme.config) {
    console.error("Theme or theme.config is undefined in Providers.tsx");
    // Render children without providers or a loading/error state
    // to prevent crashing the entire app.
    return <>{children}</>;
    // Or return null, or an error message component
    // return <div>Error: Theme configuration is missing.</div>;
  }

  return (
    <>
      {/* ColorModeScript sets the initial mode */}
      <ColorModeScript initialColorMode={theme.config.initialColorMode} />
      {/* next-themes manages the class on <html> */}
      <ErrorBoundary FallbackComponent={ErrorFallback}>
        <NextThemeProvider attribute={'class'} defaultTheme="system" enableSystem={true}>
          <NextUIProvider>
            {/* In Chakra UI v3.16, you typically pass theme directly */}
            <ChakraProvider theme={theme}>
              <AuthProvider>{children}</AuthProvider>
            </ChakraProvider>
          </NextUIProvider>
        </NextThemeProvider>
      </ErrorBoundary>
    </>
  );
}

