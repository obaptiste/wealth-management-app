'use client';

import React from 'react';
import { useTheme as useNextTheme } from 'next-themes';
import { useColorMode } from '@chakra-ui/color-mode';
import { ThemeContextType } from '../types/theme'; // Adjust the import path as necessary

export function useTheme():ThemeContextType {
  const { theme, setTheme, resolvedTheme } = useNextTheme();
  const { colorMode, setColorMode } = useColorMode();
  
  // Synchronize Chakra's colorMode with Next.js theme
  React.useEffect(() => {
    if (resolvedTheme === 'dark' && colorMode !== 'dark') {
      setColorMode('dark');
    } else if (resolvedTheme === 'light' && colorMode !== 'light') {
      setColorMode('light');
    }
  }, [resolvedTheme, colorMode, setColorMode]);

  // Enhanced theme changer that updates both systems
  const changeTheme = React.useCallback((newTheme: 'light' | 'dark' | 'system') => {
    setTheme(newTheme);
    if (newTheme !== 'system') {
      setColorMode(newTheme);
    }
  }, [setTheme, setColorMode]);
  
  return {
    // Original properties
    theme, 
    setTheme,
    resolvedTheme,
    isDark: resolvedTheme === 'dark',
    isLight: resolvedTheme === 'light',
    
    // Additional properties for Chakra integration
    colorMode,
    setColorMode,
    
    // Helper for toggling between light and dark
    toggleTheme: () => {
      const newTheme = resolvedTheme === 'dark' ? 'light' : 'dark';
      changeTheme(newTheme);
    }
  };
}
