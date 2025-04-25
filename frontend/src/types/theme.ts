
export interface ThemeContextType {
  theme: string | undefined;
  setTheme: (theme: string) => void;
  resolvedTheme?: string;
  isDark: boolean;
  isLight: boolean;
  colorMode: string;
  setColorMode: (colorMode: 'light' | 'dark') => void;
  toggleTheme: () => void;
}

export interface ChakraProviderProps {
  theme: {
    
    // Add other theme properties as needed
    theme?: string | undefined;
    setTheme?: (theme: string) => void;
    resolvedTheme?: string | undefined;
    isDark?: boolean;
    isLight?: boolean;
    fonts?: Record<string, string>;
    fontSizes?: Record<string, string>;
    breakpoints?: Record<string, string>;
    // Add more theme properties based on your theme structure
  };
}
