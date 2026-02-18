// styles/theme.ts
import { ThemeConfig } from '@chakra-ui/theme';
import { extendTheme } from '@chakra-ui/theme-utils';

// Color mode config - supports dark mode
const config: ThemeConfig = {
  initialColorMode: 'dark',
  useSystemColorMode: false,
};

// Distinctive color scheme inspired by financial terminals and modern fintech
// Deep emerald and gold accent instead of generic blues/purples
const colors = {
  brand: {
    50: '#E6F7F1',
    100: '#B8E8D8',
    200: '#8AD9BF',
    300: '#5CCAA6',
    400: '#2EBB8D',
    500: '#00AC74', // Deep emerald - primary brand color
    600: '#008A5D',
    700: '#006746',
    800: '#00452F',
    900: '#002218',
  },
  accent: {
    50: '#FFF8E6',
    100: '#FFEAB8',
    200: '#FFDC8A',
    300: '#FFCE5C',
    400: '#FFC02E',
    500: '#FFB200', // Rich gold accent
    600: '#CC8E00',
    700: '#996B00',
    800: '#664700',
    900: '#332400',
  },
  slate: {
    50: '#F8FAFC',
    100: '#F1F5F9',
    200: '#E2E8F0',
    300: '#CBD5E1',
    400: '#94A3B8',
    500: '#64748B',
    600: '#475569',
    700: '#334155',
    800: '#1E293B',
    900: '#0F172A',
  },
  success: {
    500: '#10B981',
    600: '#059669',
  },
  warning: {
    500: '#F59E0B',
    600: '#D97706',
  },
  danger: {
    500: '#EF4444',
    600: '#DC2626',
  },
};

// Distinctive font pairing - avoiding Inter/Roboto/Arial
// Using Syne (geometric, modern) for headings and Work Sans (elegant, readable) for body
const fonts = {
  heading: '"Syne", "Space Grotesk", "Outfit", -apple-system, system-ui, sans-serif',
  body: '"Work Sans", "Plus Jakarta Sans", "DM Sans", -apple-system, system-ui, sans-serif',
  mono: '"JetBrains Mono", "Fira Code", "Source Code Pro", monospace',
};

const components = {
  Button: {
    baseStyle: {
      fontWeight: '600',
      borderRadius: 'lg',
      transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
      letterSpacing: '0.025em',
    },
    variants: {
      solid: (props: { colorScheme: string; colorMode: string }) => ({
        bg: props.colorScheme === 'brand' ? 'brand.500' : `${props.colorScheme}.500`,
        color: 'white',
        _hover: {
          bg: props.colorScheme === 'brand' ? 'brand.600' : `${props.colorScheme}.600`,
          transform: 'translateY(-2px)',
          boxShadow: 'lg',
        },
        _active: {
          transform: 'translateY(0)',
        },
      }),
      outline: (props: { colorScheme: string; colorMode: string }) => ({
        border: '2px solid',
        borderColor: props.colorScheme === 'brand' ? 'brand.500' : `${props.colorScheme}.500`,
        color: props.colorScheme === 'brand' ? 'brand.500' : `${props.colorScheme}.500`,
        _hover: {
          bg: props.colorMode === 'dark' ? 'whiteAlpha.100' : 'blackAlpha.50',
          transform: 'translateY(-2px)',
        },
      }),
      ghost: (props: { colorMode: string }) => ({
        _hover: {
          bg: props.colorMode === 'dark' ? 'whiteAlpha.100' : 'blackAlpha.50',
        },
      }),
    },
    defaultProps: {
      colorScheme: 'brand',
    },
  },
  Card: {
    baseStyle: (props: { colorMode: string }) => ({
      p: '6',
      bg: props.colorMode === 'dark' ? 'slate.800' : 'white',
      borderRadius: '2xl',
      boxShadow: props.colorMode === 'dark'
        ? '0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.2)'
        : '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
      border: '1px solid',
      borderColor: props.colorMode === 'dark' ? 'slate.700' : 'slate.200',
      transition: 'all 0.3s ease',
      _hover: {
        transform: 'translateY(-4px)',
        boxShadow: props.colorMode === 'dark'
          ? '0 20px 25px -5px rgba(0, 0, 0, 0.4), 0 10px 10px -5px rgba(0, 0, 0, 0.3)'
          : '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
      },
    }),
  },
  Input: {
    baseStyle: {
      field: {
        borderRadius: 'lg',
        transition: 'all 0.2s ease',
      },
    },
    variants: {
      outline: (props: { colorMode: string }) => ({
        field: {
          border: '2px solid',
          borderColor: props.colorMode === 'dark' ? 'slate.600' : 'slate.300',
          bg: props.colorMode === 'dark' ? 'slate.800' : 'white',
          _hover: {
            borderColor: 'brand.400',
          },
          _focus: {
            borderColor: 'brand.500',
            boxShadow: '0 0 0 3px rgba(0, 172, 116, 0.1)',
          },
        },
      }),
      filled: (props: { colorMode: string }) => ({
        field: {
          bg: props.colorMode === 'dark' ? 'slate.700' : 'slate.100',
          border: '2px solid transparent',
          _hover: {
            bg: props.colorMode === 'dark' ? 'slate.600' : 'slate.200',
          },
          _focus: {
            bg: props.colorMode === 'dark' ? 'slate.800' : 'white',
            borderColor: 'brand.500',
          },
        },
      }),
    },
    defaultProps: {
      variant: 'outline',
    },
  },
  Heading: {
    baseStyle: (props: { colorMode: string }) => ({
      fontWeight: '700',
      letterSpacing: '-0.025em',
      color: props.colorMode === 'dark' ? 'white' : 'slate.900',
    }),
  },
  Text: {
    baseStyle: (props: { colorMode: string }) => ({
      color: props.colorMode === 'dark' ? 'slate.300' : 'slate.600',
    }),
  },
};

// Customize breakpoints
const breakpoints = {
  sm: '30em',   // 480px
  md: '48em',   // 768px
  lg: '62em',   // 992px
  xl: '80em',   // 1280px
  '2xl': '96em', // 1536px
};

const styles = {
  global: (props: { colorMode: string }) => ({
    body: {
      bg: props.colorMode === 'dark'
        ? 'slate.900'
        : 'slate.50',
      color: props.colorMode === 'dark' ? 'slate.100' : 'slate.800',
      // Subtle noise texture for depth
      backgroundImage: props.colorMode === 'dark'
        ? `radial-gradient(circle at 25% 25%, rgba(0, 172, 116, 0.08) 0%, transparent 50%),
           radial-gradient(circle at 75% 75%, rgba(255, 178, 0, 0.05) 0%, transparent 50%)`
        : `radial-gradient(circle at 25% 25%, rgba(0, 172, 116, 0.04) 0%, transparent 50%),
           radial-gradient(circle at 75% 75%, rgba(255, 178, 0, 0.03) 0%, transparent 50%)`,
      backgroundAttachment: 'fixed',
    },
    '*::selection': {
      bg: 'brand.500',
      color: 'white',
    },
    // Smooth scrolling
    html: {
      scrollBehavior: 'smooth',
    },
  }),
};

// Add semantic tokens for better color management
const semanticTokens = {
  colors: {
    'bg-canvas': {
      default: 'slate.50',
      _dark: 'slate.900',
    },
    'bg-surface': {
      default: 'white',
      _dark: 'slate.800',
    },
    'bg-subtle': {
      default: 'slate.100',
      _dark: 'slate.700',
    },
    'text-primary': {
      default: 'slate.900',
      _dark: 'white',
    },
    'text-secondary': {
      default: 'slate.600',
      _dark: 'slate.300',
    },
    'text-muted': {
      default: 'slate.500',
      _dark: 'slate.400',
    },
    'border-primary': {
      default: 'slate.200',
      _dark: 'slate.700',
    },
    'border-accent': {
      default: 'brand.500',
      _dark: 'brand.500',
    },
  },
};

export const theme = extendTheme({
  colors,
  fonts,
  components,
  breakpoints,
  styles,
  config,
  semanticTokens,
});