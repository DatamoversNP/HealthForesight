import React, { useState, useEffect, useRef } from 'react'
import {
  Box,
  Drawer,
  Typography,
  TextField,
  IconButton,
  Button,
  Paper,
  Chip,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Divider,
  Alert,
  CircularProgress,
} from '@mui/material'
import {
  Send as SendIcon,
  Close as CloseIcon,
  SmartToy as AIIcon,
  Person as PersonIcon,
  Code as CodeIcon,
  CheckCircle as CheckIcon,
  Edit as EditIcon,
} from '@mui/icons-material'
import { apiClient } from '../../lib/api'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  structured_data?: any
  metadata?: {
    confidence?: string
    requires_clarification?: boolean
    clarification_questions?: string[]
  }
  created_at: string
}

interface Conversation {
  id: string
  title: string
  mode: 'DRAFT' | 'EXPLAIN' | 'QUERY'
  domain?: 'POLICY' | 'DATA' | 'BASELINE' | 'IMPACT' | 'GOVERNANCE'
  status: string
  messages: Message[]
  artifacts: any[]
  created_at: string
  updated_at: string
}

interface ConversationalAIPanelProps {
  open: boolean
  onClose: () => void
  initialMode?: 'DRAFT' | 'EXPLAIN' | 'QUERY'
  initialDomain?: 'POLICY' | 'DATA' | 'BASELINE' | 'IMPACT' | 'GOVERNANCE'
}

export default function ConversationalAIPanel({
  open,
  onClose,
  initialMode = 'DRAFT',
  initialDomain = 'POLICY',
}: ConversationalAIPanelProps) {
  const [conversation, setConversation] = useState<Conversation | null>(null)
  const [mode, setMode] = useState<'DRAFT' | 'EXPLAIN' | 'QUERY'>(initialMode)
  const [domain, setDomain] = useState<'POLICY' | 'DATA' | 'BASELINE' | 'IMPACT' | 'GOVERNANCE' | undefined>(initialDomain)
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (open && !conversation) {
      createNewConversation()
    }
  }, [open])

  useEffect(() => {
    scrollToBottom()
  }, [conversation?.messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const createNewConversation = async () => {
    try {
      setError(null)
      const newConversation = await apiClient.createConversation(mode, domain)
      setConversation(newConversation)
    } catch (err: any) {
      setError(err.message || 'Failed to create conversation')
    }
  }

  const handleSendMessage = async () => {
    if (!message.trim() || !conversation || loading) return

    const userMessage = message.trim()
    setMessage('')
    setLoading(true)
    setError(null)

    try {
      const response = await apiClient.sendMessage(conversation.id, userMessage)
      
      // Reload conversation to get updated messages
      const updatedConversation = await apiClient.getConversation(conversation.id)
      setConversation(updatedConversation)
    } catch (err: any) {
      setError(err.message || 'Failed to send message')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmitArtifact = async (artifact: any) => {
    if (!conversation) return

    try {
      setError(null)
      await apiClient.submitArtifact(conversation.id, artifact.id)
      
      // Reload conversation
      const updatedConversation = await apiClient.getConversation(conversation.id)
      setConversation(updatedConversation)
    } catch (err: any) {
      setError(err.message || 'Failed to submit artifact')
    }
  }

  const getModeColor = (mode: string) => {
    switch (mode) {
      case 'DRAFT': return 'primary'
      case 'EXPLAIN': return 'info'
      case 'QUERY': return 'success'
      default: return 'default'
    }
  }

  const getDomainLabel = (domain?: string) => {
    if (!domain) return 'General'
    const labels: Record<string, string> = {
      POLICY: 'Policy',
      DATA: 'Data',
      BASELINE: 'Baseline',
      IMPACT: 'Impact',
      GOVERNANCE: 'Governance',
    }
    return labels[domain] || domain
  }

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      PaperProps={{
        sx: {
          width: { xs: '100%', sm: 600, md: 700 },
          maxWidth: '100vw',
        },
      }}
    >
      <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        {/* Header */}
        <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <AIIcon color="primary" />
              <Typography variant="h6">Conversational AI</Typography>
            </Box>
            <IconButton onClick={onClose} size="small">
              <CloseIcon />
            </IconButton>
          </Box>
          
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 1 }}>
            <Chip
              label={mode}
              color={getModeColor(mode)}
              size="small"
            />
            {domain && (
              <Chip
                label={getDomainLabel(domain)}
                color="default"
                size="small"
              />
            )}
          </Box>
        </Box>

        {/* Messages */}
        <Box
          sx={{
            flex: 1,
            overflow: 'auto',
            p: 2,
            bgcolor: 'grey.50',
          }}
        >
          {error && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          {conversation?.messages.map((msg) => (
            <Box
              key={msg.id}
              sx={{
                display: 'flex',
                mb: 2,
                justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
              }}
            >
              <Paper
                sx={{
                  p: 2,
                  maxWidth: '80%',
                  bgcolor: msg.role === 'user' ? 'primary.light' : 'background.paper',
                  color: msg.role === 'user' ? 'primary.contrastText' : 'text.primary',
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'start', gap: 1, mb: 1 }}>
                  {msg.role === 'user' ? <PersonIcon fontSize="small" /> : <AIIcon fontSize="small" />}
                  <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                    {msg.role === 'user' ? 'You' : 'AI Assistant'}
                  </Typography>
                </Box>
                
                <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                  {msg.content}
                </Typography>

                {msg.metadata?.confidence && (
                  <Chip
                    label={`Confidence: ${msg.metadata.confidence}`}
                    size="small"
                    sx={{ mt: 1 }}
                    color={msg.metadata.confidence === 'HIGH' ? 'success' : msg.metadata.confidence === 'MEDIUM' ? 'warning' : 'error'}
                  />
                )}

                {msg.metadata?.clarification_questions && msg.metadata.clarification_questions.length > 0 && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="caption" sx={{ fontWeight: 'bold' }}>
                      Clarification needed:
                    </Typography>
                    {msg.metadata.clarification_questions.map((q: string, idx: number) => (
                      <Typography key={idx} variant="caption" display="block" sx={{ mt: 0.5 }}>
                        • {q}
                      </Typography>
                    ))}
                  </Box>
                )}

                {msg.structured_data && (
                  <Box sx={{ mt: 2 }}>
                    <Divider sx={{ my: 1 }} />
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <CodeIcon fontSize="small" />
                      <Typography variant="caption" sx={{ fontWeight: 'bold' }}>
                        Structured Output
                      </Typography>
                    </Box>
                    <Paper
                      variant="outlined"
                      sx={{
                        p: 1,
                        bgcolor: 'grey.100',
                        maxHeight: 200,
                        overflow: 'auto',
                      }}
                    >
                      <pre style={{ margin: 0, fontSize: '0.75rem' }}>
                        {JSON.stringify(msg.structured_data, null, 2)}
                      </pre>
                    </Paper>
                  </Box>
                )}
              </Paper>
            </Box>
          ))}

          {loading && (
            <Box sx={{ display: 'flex', justifyContent: 'flex-start', mb: 2 }}>
              <Paper sx={{ p: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CircularProgress size={16} />
                  <Typography variant="body2">AI is thinking...</Typography>
                </Box>
              </Paper>
            </Box>
          )}

          <div ref={messagesEndRef} />
        </Box>

        {/* Artifacts */}
        {conversation?.artifacts && conversation.artifacts.length > 0 && (
          <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider', bgcolor: 'background.paper' }}>
            <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 'bold' }}>
              Generated Artifacts
            </Typography>
            {conversation.artifacts.map((artifact) => (
              <Paper
                key={artifact.id}
                variant="outlined"
                sx={{
                  p: 1.5,
                  mb: 1,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <Box>
                  <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                    {artifact.artifact_type.replace('_', ' ')}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Status: {artifact.status}
                  </Typography>
                </Box>
                {artifact.status === 'DRAFT' && (
                  <Button
                    size="small"
                    variant="contained"
                    startIcon={<CheckIcon />}
                    onClick={() => handleSubmitArtifact(artifact)}
                  >
                    Submit
                  </Button>
                )}
              </Paper>
            ))}
          </Box>
        )}

        {/* Input */}
        <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider', bgcolor: 'background.paper' }}>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <TextField
              fullWidth
              multiline
              maxRows={4}
              placeholder="Ask me anything about policies, data, baselines, or impact analysis..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  handleSendMessage()
                }
              }}
              disabled={loading || !conversation}
            />
            <IconButton
              color="primary"
              onClick={handleSendMessage}
              disabled={!message.trim() || loading || !conversation}
            >
              <SendIcon />
            </IconButton>
          </Box>
          
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
            Mode: {mode} | Domain: {getDomainLabel(domain)} | All actions are logged and require approval
          </Typography>
        </Box>
      </Box>
    </Drawer>
  )
}

