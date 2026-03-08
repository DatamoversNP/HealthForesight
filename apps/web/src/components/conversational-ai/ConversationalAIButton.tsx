import React, { useState } from 'react'
import { IconButton, Tooltip, Badge } from '@mui/material'
import { SmartToy as AIIcon } from '@mui/icons-material'
import ConversationalAIPanel from './ConversationalAIPanel'

interface ConversationalAIButtonProps {
  initialMode?: 'DRAFT' | 'EXPLAIN' | 'QUERY'
  initialDomain?: 'POLICY' | 'DATA' | 'BASELINE' | 'IMPACT' | 'GOVERNANCE'
}

export default function ConversationalAIButton({
  initialMode = 'DRAFT',
  initialDomain = 'POLICY',
}: ConversationalAIButtonProps) {
  const [open, setOpen] = useState(false)

  return (
    <>
      <Tooltip title="Conversational AI Assistant">
        <IconButton
          color="primary"
          onClick={() => setOpen(true)}
          sx={{
            position: 'fixed',
            bottom: 24,
            right: 24,
            width: 56,
            height: 56,
            bgcolor: 'primary.main',
            color: 'white',
            '&:hover': {
              bgcolor: 'primary.dark',
            },
            boxShadow: 3,
            zIndex: 1300,
          }}
        >
          <AIIcon />
        </IconButton>
      </Tooltip>

      <ConversationalAIPanel
        open={open}
        onClose={() => setOpen(false)}
        initialMode={initialMode}
        initialDomain={initialDomain}
      />
    </>
  )
}

