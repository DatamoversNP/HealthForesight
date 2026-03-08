/**
 * HealthForesight Brand Theme System
 * By DataMovers - Authoritative Specification
 */
import { createTheme, ThemeOptions } from '@mui/material/styles'

// HealthForesight Color Palette (Preserve DataMovers DNA)
const colors = {
  // Core Palette
  primary: {
    main: '#3B2F8F', // DataMovers Indigo
    light: '#5A4AA5',
    dark: '#2A1F6B',
    contrastText: '#FFFFFF',
  },
  secondary: {
    main: '#1E2A44', // Deep Navy
    light: '#3A4A64',
    dark: '#0F1522',
    contrastText: '#FFFFFF',
  },
  accent: {
    main: '#2EC4C6', // Teal start of gradient
    light: '#5EEAD4', // Teal end of gradient
    dark: '#1E9A9C',
    contrastText: '#0F172A',
  },
  amber: {
    main: '#E6A23C', // Amber/Orange
    light: '#FFB74D',
    dark: '#E65100',
    contrastText: '#FFFFFF',
  },
  // Neutral Palette
  neutral: {
    dark: '#0F172A',
    mid: '#64748B',
    light: '#E5E7EB',
    background: '#F8FAFC',
  },
  // Semantic Colors (Used Sparingly)
  semantic: {
    positive: '#2E8B57', // Muted Green
    warning: '#E6A23C', // Amber
    risk: '#C04A4A', // Muted Red
    info: '#6366F1', // Indigo Tint
  },
}

// Typography Configuration
const typography: ThemeOptions['typography'] = {
  fontFamily: [
    'Inter',
    '-apple-system',
    'BlinkMacSystemFont',
    '"Segoe UI"',
    'Roboto',
    '"Helvetica Neue"',
    'Arial',
    'sans-serif',
  ].join(','),
  h1: {
    fontFamily: '"IBM Plex Sans", "Inter", sans-serif',
    fontWeight: 600,
    fontSize: '2rem',
    lineHeight: 1.2,
    color: colors.neutral.dark,
    letterSpacing: '-0.02em',
  },
  h2: {
    fontFamily: '"IBM Plex Sans", "Inter", sans-serif',
    fontWeight: 600,
    fontSize: '1.75rem',
    lineHeight: 1.3,
    color: colors.neutral.dark,
    letterSpacing: '-0.01em',
  },
  h3: {
    fontFamily: '"IBM Plex Sans", "Inter", sans-serif',
    fontWeight: 600,
    fontSize: '1.5rem',
    lineHeight: 1.4,
    color: colors.neutral.dark,
  },
  h4: {
    fontFamily: '"IBM Plex Sans", "Inter", sans-serif',
    fontWeight: 600,
    fontSize: '1.25rem',
    lineHeight: 1.4,
    color: colors.neutral.dark,
  },
  h5: {
    fontFamily: '"IBM Plex Sans", "Inter", sans-serif',
    fontWeight: 600,
    fontSize: '1.125rem',
    lineHeight: 1.5,
    color: colors.neutral.dark,
  },
  h6: {
    fontFamily: '"IBM Plex Sans", "Inter", sans-serif',
    fontWeight: 600,
    fontSize: '1rem',
    lineHeight: 1.5,
    color: colors.neutral.dark,
  },
  body1: {
    fontFamily: 'Inter, sans-serif',
    fontWeight: 400,
    fontSize: '14px',
    lineHeight: 1.5,
    color: colors.neutral.dark,
  },
  body2: {
    fontFamily: 'Inter, sans-serif',
    fontWeight: 400,
    fontSize: '13px',
    lineHeight: 1.5,
    color: colors.neutral.mid,
  },
  button: {
    fontFamily: 'Inter, sans-serif',
    fontWeight: 500,
    fontSize: '14px',
    textTransform: 'none', // Sentence case, not uppercase
    letterSpacing: '0.01em',
  },
  caption: {
    fontFamily: 'Inter, sans-serif',
    fontWeight: 400,
    fontSize: '12px',
    lineHeight: 1.4,
    color: colors.neutral.mid,
  },
}

// Component Overrides for HealthForesight Brand
const componentOverrides: ThemeOptions['components'] = {
  MuiButton: {
    styleOverrides: {
      root: {
        borderRadius: 8,
        padding: '10px 20px',
        fontWeight: 500,
        textTransform: 'none',
        boxShadow: 'none',
        '&:hover': {
          boxShadow: 'none',
        },
      },
      contained: {
        backgroundColor: colors.primary.main,
        color: colors.primary.contrastText,
        '&:hover': {
          backgroundColor: colors.primary.dark,
        },
      },
      outlined: {
        borderColor: colors.neutral.light,
        color: colors.neutral.dark,
        '&:hover': {
          borderColor: colors.accent.main,
          backgroundColor: 'transparent',
        },
      },
    },
  },
  MuiCard: {
    styleOverrides: {
      root: {
        borderRadius: 8,
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.08)',
        border: `1px solid ${colors.neutral.light}`,
        backgroundColor: '#FFFFFF',
      },
    },
  },
  MuiPaper: {
    styleOverrides: {
      root: {
        borderRadius: 8,
        border: `1px solid ${colors.neutral.light}`,
      },
      elevation1: {
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.08)',
      },
    },
  },
  MuiChip: {
    styleOverrides: {
      root: {
        borderRadius: 6,
        fontWeight: 500,
        fontSize: '12px',
      },
    },
  },
  MuiTextField: {
    styleOverrides: {
      root: {
        '& .MuiOutlinedInput-root': {
          borderRadius: 8,
          '&:hover fieldset': {
            borderColor: colors.accent.main,
          },
        },
      },
    },
  },
  MuiTable: {
    styleOverrides: {
      root: {
        borderCollapse: 'separate',
        borderSpacing: 0,
      },
    },
  },
  MuiTableCell: {
    styleOverrides: {
      root: {
        borderBottom: `1px solid ${colors.neutral.light}`,
        padding: '12px 16px',
        fontVariantNumeric: 'tabular-nums',
      },
      head: {
        fontWeight: 600,
        fontSize: '12px',
        textTransform: 'uppercase',
        letterSpacing: '0.05em',
        color: colors.neutral.mid,
        backgroundColor: colors.neutral.background,
      },
    },
  },
  MuiDrawer: {
    styleOverrides: {
      paper: {
        borderRight: `1px solid ${colors.neutral.light}`,
        backgroundColor: '#FFFFFF',
      },
    },
  },
  MuiAppBar: {
    styleOverrides: {
      root: {
        backgroundColor: colors.primary.main,
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.08)',
      },
    },
  },
  MuiDivider: {
    styleOverrides: {
      root: {
        borderColor: colors.neutral.light,
      },
    },
  },
}

// Create HealthForesight Theme
export const healthForesightTheme = createTheme({
  palette: {
    mode: 'light',
    primary: colors.primary,
    secondary: colors.secondary,
    background: {
      default: colors.neutral.background,
      paper: '#FFFFFF',
    },
    text: {
      primary: colors.neutral.dark,
      secondary: colors.neutral.mid,
    },
    divider: colors.neutral.light,
    // Custom semantic colors
    success: {
      main: colors.semantic.positive,
      light: '#4CAF50',
      dark: '#1B5E20',
      contrastText: '#FFFFFF',
    },
    warning: {
      main: colors.semantic.warning,
      light: '#FFB74D',
      dark: '#E65100',
      contrastText: '#FFFFFF',
    },
    error: {
      main: colors.semantic.risk,
      light: '#E57373',
      dark: '#B71C1C',
      contrastText: '#FFFFFF',
    },
    info: {
      main: colors.semantic.info,
      light: '#81C784',
      dark: '#388E3C',
      contrastText: '#FFFFFF',
    },
  },
  typography,
  components: componentOverrides,
  shape: {
    borderRadius: 8,
  },
  transitions: {
    duration: {
      shortest: 150,
      shorter: 200,
      short: 250,
      standard: 300,
      complex: 375,
      enteringScreen: 225,
      leavingScreen: 195,
    },
    easing: {
      easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
      easeOut: 'cubic-bezier(0.0, 0, 0.2, 1)',
      easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
      sharp: 'cubic-bezier(0.4, 0, 0.6, 1)',
    },
  },
})

// Export color constants for use in components
export const healthForesightColors = colors

// Export typography constants
export const healthForesightTypography = {
  primaryFont: 'Inter',
  headingFont: 'IBM Plex Sans',
  bodySize: '14px',
  lineHeight: 1.5,
}

