/**
 * Shared filter strip for catalog-scale tables/grids.
 * Use variant="embedded" inside the same Paper as the table (grid toolbar).
 */
import { ReactNode } from 'react'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import TextField from '@mui/material/TextField'
import Typography from '@mui/material/Typography'

type Props = {
  search: string
  onSearchChange: (value: string) => void
  searchPlaceholder?: string
  searchLabel?: string
  children?: ReactNode
  shown: number
  total: number
  onClear: () => void
  clearDisabled?: boolean
  /** Extra note under the count line */
  hint?: string
  /**
   * embedded — sits inside the grid Paper as a toolbar (default for list tables).
   * standalone — reserved; prefer wrapping Paper yourself and using embedded.
   */
  variant?: 'embedded' | 'standalone'
}

export default function ListFilterBar({
  search,
  onSearchChange,
  searchPlaceholder = 'Search…',
  searchLabel = 'Search',
  children,
  shown,
  total,
  onClear,
  clearDisabled = false,
  hint,
  variant = 'embedded',
}: Props) {
  const isEmbedded = variant === 'embedded'

  return (
    <Box
      sx={{
        px: 2,
        pt: 1.5,
        pb: 1.25,
        borderBottom: isEmbedded ? 1 : 0,
        borderColor: 'divider',
        bgcolor: isEmbedded ? 'action.hover' : 'transparent',
      }}
    >
      <Box
        sx={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: 1.5,
          alignItems: 'center',
        }}
      >
        <TextField
          size="small"
          label={searchLabel}
          placeholder={searchPlaceholder}
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          sx={{ minWidth: { xs: '100%', sm: 200 }, flex: '1 1 180px', bgcolor: 'background.paper' }}
        />
        {children}
        <Button size="small" onClick={onClear} disabled={clearDisabled} sx={{ flexShrink: 0 }}>
          Clear
        </Button>
        <Typography
          variant="caption"
          color="text.secondary"
          sx={{ ml: { sm: 'auto' }, whiteSpace: 'nowrap' }}
        >
          Showing {shown} of {total}
          {shown !== total ? ' (filtered)' : ''}
          {hint ? ` · ${hint}` : ''}
        </Typography>
      </Box>
    </Box>
  )
}
