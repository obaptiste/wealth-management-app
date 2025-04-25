// styles/theme.ts
import { ThemeConfig } from '@chakra-ui/theme';
import { extendTheme } from '@chakra-ui/theme-utils';

// Color mode config - supports dark mode
const config: ThemeConfig = {
  initialColorMode: 'light',
  useSystemColorMode: false,
};

const colors = {
  primary: {
    50: '#E6F0FF',
    100: '#CCE0FF',
    200: '#99C2FF',
    300: '#66A3FF',
    400: '#3385FF',
    500: '#0066FF', // Primary color
    600: '#0052CC',
    700: '#003D99',
    800: '#002966',
    900: '#001433',
  },
  secondary: {
    50: '#F0F9FF',
    100: '#E1F4FF',
    200: '#BFE9FF',
    300: '#80D5FF',
    400: '#40C2FF',
    500: '#00AEEF', // Secondary color
    600: '#008BC0',
    700: '#006892',
    800: '#004563',
    900: '#002331',
  },
  success: {
    50: '#E6F8F0',
    100: '#C7EDD9',
    200: '#96E0B8',
    300: '#65D396',
    400: '#34C673',
    500: '#28A05C', // Success color
    600: '#208049',
    700: '#186037',
    800: '#104024',
    900: '#082012',
  },
  warning: {
    50: '#FFF8E6',
    100: '#FFEFC4',
    200: '#FFE599',
    300: '#FFDA6D',
    400: '#FFD042',
    500: '#FFC107', // Warning color
    600: '#CC9A06',
    700: '#997304',
    800: '#664D03',
    900: '#332601',
  },
  danger: {
    50: '#FEE8E8',
    100: '#FDD0D0',
    200: '#FBA0A1',
    300: '#F97172',
    400: '#F84243',
    500: '#E41E25', // Danger color
    600: '#B6181D',
    700: '#881215',
    800: '#5B0C0E',
    900: '#2D0607',
  },
};

const fonts = {
  heading: '"Geist", -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif',
  body: '"Geist", -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif',
  mono: '"Geist Mono", SFMono-Regular, Menlo, Monaco, Consolas, monospace',
};

const components = {
  Button: {
    baseStyle: {
      fontWeight: 'medium',
      borderRadius: 'md',
    },
    variants: {
      solid: (props: { colorScheme: string }) => ({
        bg: props.colorScheme === 'primary' ? 'primary.500' : `${props.colorScheme}.500`,
        color: 'white',
        _hover: {
          bg: props.colorScheme === 'primary' ? 'primary.600' : `${props.colorScheme}.600`,
        },
      }),
      outline: (props: { colorScheme: string }) => ({
        border: '1px solid',
        borderColor: props.colorScheme === 'primary' ? 'primary.500' : `${props.colorScheme}.500`,
        color: props.colorScheme === 'primary' ? 'primary.500' : `${props.colorScheme}.500`,
      }),
    },
    defaultProps: {
      colorScheme: 'primary',
    },
  },
  Card: {
    baseStyle: (props: { colorMode: string }) => ({
      p: '6',
      bg: props.colorMode === 'dark' ? 'gray.800' : 'white',
      borderRadius: 'xl',
      boxShadow: 'md',
    }),
  },
  Input: {
    baseStyle: {
      field: {
        borderRadius: 'md',
      },
    },
    variants: {
      outline: (props: { colorMode: string }) => ({
        field: {
          border: '1px solid',
          borderColor: props.colorMode === 'dark' ? 'gray.600' : 'gray.300',
          _hover: {
            borderColor: 'primary.400',
          },
          _focus: {
            borderColor: 'primary.500',
            boxShadow: '0 0 0 1px var(--chakra-colors-primary-500)',
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
      fontWeight: '600',
      color: props.colorMode === 'dark' ? 'gray.100' : 'gray.800',
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
      bg: props.colorMode === 'dark' ? 'gray.900' : 'gray.50',
      color: props.colorMode === 'dark' ? 'gray.100' : 'gray.800',
    },
  }),
};

export const theme = extendTheme({
  colors,
  fonts,
  components,
  breakpoints,
  styles,
  config,
});